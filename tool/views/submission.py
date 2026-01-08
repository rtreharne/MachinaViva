import json

from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .helpers import is_instructor_role, is_admin_role
from ..models import Assignment, Submission, VivaSession, AssignmentResource, AssignmentResourcePreference
from ..utils import extract_text_from_file, is_allowed_upload, MAX_SUBMISSION_TEXT_CHARS, ALLOWED_UPLOAD_EXTENSIONS


def _reject_upload(request, message):
    if request.headers.get("accept") == "application/json":
        return JsonResponse({"status": "error", "message": message}, status=400)
    return HttpResponseBadRequest(message)


def _allowed_ext_label():
    return ", ".join(sorted(ext.lstrip(".").upper() for ext in ALLOWED_UPLOAD_EXTENSIONS))


def _cleanup_submissions(submissions):
    for sub in submissions:
        if sub.file:
            sub.file.delete(save=False)
        sub.delete()


def _cleanup_resources(resources):
    for resource in resources:
        if resource.file:
            resource.file.delete(save=False)
        resource.delete()


def _is_extracted_text_empty(extracted):
    if not extracted:
        return True
    stripped = extracted.strip()
    if not stripped:
        return True
    if stripped.startswith("[Extraction Error"):
        return True
    return False


# ============================================================
# Text Submission (fallback / debug mode)
# ============================================================
@csrf_exempt
def submit_text(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    user_id = request.session.get("lti_user_id")
    resource_link_id = request.session.get("lti_resource_link_id")

    if not user_id or not resource_link_id:
        return _reject_upload(request, "Missing LTI session info")

    assignment = Assignment.objects.get(slug=resource_link_id)

    text = (request.POST.get("text") or "").strip()
    if len(text) > MAX_SUBMISSION_TEXT_CHARS:
        return HttpResponseBadRequest(f"Text submission too long (max {MAX_SUBMISSION_TEXT_CHARS} chars).")

    Submission.objects.create(
        assignment=assignment,
        user_id=user_id,
        comment=text,
        file=None,
    )

    return redirect("assignment_view")


# ============================================================
# File Upload Submission (PDF / DOCX / TXT / PY)
# ============================================================
@csrf_exempt
def submit_file(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    user_id = request.session.get("lti_user_id")
    resource_link_id = request.session.get("lti_resource_link_id")

    if not user_id or not resource_link_id:
        return HttpResponseBadRequest("Missing LTI session info")

    assignment = Assignment.objects.get(slug=resource_link_id)

    uploads = request.FILES.getlist("file")
    if not uploads:
        return _reject_upload(request, "Missing file")

    invalid_uploads = [f.name for f in uploads if not is_allowed_upload(getattr(f, "name", ""))]
    if invalid_uploads:
        return _reject_upload(request, f"Unsupported file type. Allowed: {_allowed_ext_label()}.")
    empty_uploads = [f.name for f in uploads if getattr(f, "size", 0) <= 0]
    if empty_uploads:
        return _reject_upload(request, "Empty files cannot be uploaded.")

    existing_submissions = list(Submission.objects.filter(
        assignment=assignment,
        user_id=user_id,
        is_placeholder=False,
    ))
    if len(existing_submissions) + len(uploads) > 10:
        if request.headers.get("accept") == "application/json":
            return JsonResponse({"status": "error", "message": "You can upload up to 10 files in total."}, status=400)
        return redirect("assignment_view")

    max_total_bytes = 50 * 1024 * 1024  # 50 MB
    existing_size = sum((s.file.size for s in existing_submissions if s.file), 0)
    new_size = sum((getattr(f, "size", 0) for f in uploads), 0)
    if existing_size + new_size > max_total_bytes:
        if request.headers.get("accept") == "application/json":
            return JsonResponse({"status": "error", "message": "Total upload size limit is 50MB across all files."}, status=400)
        return redirect("assignment_view")

    created_submissions = []
    for uploaded in uploads:
        sub = Submission.objects.create(
            assignment=assignment,
            user_id=user_id,
            file=uploaded,
            comment="",  # extracted text will be added after save
        )
        created_submissions.append(sub)

        extracted = ""
        try:
            if sub.file and sub.file.path:
                extracted = extract_text_from_file(sub.file.path)
        except Exception:
            extracted = ""
        if _is_extracted_text_empty(extracted):
            _cleanup_submissions(created_submissions)
            return _reject_upload(
                request,
                "No extractable text found. If this is a scanned PDF, upload a text-based version.",
            )

        sub.comment = extracted[:MAX_SUBMISSION_TEXT_CHARS]
        sub.save(update_fields=["comment"])

    if request.headers.get("accept") == "application/json":
        return JsonResponse({"status": "ok"})

    return redirect("assignment_view")


# ============================================================
# Submission Status Page
# Automatically extracts text if needed
# ============================================================
def submission_status(request, submission_id):
    """Show extracted text and submission state."""
    try:
        sub = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return HttpResponseBadRequest("Invalid submission ID")

    # Perform extraction only if comment is empty and file exists
    if sub.file and not sub.comment:
        extracted = extract_text_from_file(sub.file.path)
        sub.comment = extracted[:MAX_SUBMISSION_TEXT_CHARS]  # safety cap
        sub.save()

    return render(request, "tool/submission_status.html", {
        "submission": sub,
    })


@csrf_exempt
def delete_submission(request, submission_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    user_id = request.session.get("lti_user_id")
    if not user_id:
        return HttpResponseBadRequest("Missing user")

    try:
        sub = Submission.objects.get(id=submission_id, user_id=user_id)
    except Submission.DoesNotExist:
        return HttpResponseBadRequest("Invalid submission")

    if sub.is_placeholder:
        return HttpResponseBadRequest("Cannot delete a placeholder submission.")

    if VivaSession.objects.filter(submission=sub).exists():
        return HttpResponseBadRequest("Cannot delete a submission linked to a viva session.")

    sub.delete()
    if request.headers.get("accept") == "application/json":
        return JsonResponse({"status": "ok"})
    return redirect("assignment_view")


# ============================================================
# Assignment Resources (Instructor-uploaded files)
# ============================================================
@csrf_exempt
def upload_assignment_resource(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    roles = request.session.get("lti_roles", [])
    if not (is_instructor_role(roles) or is_admin_role(roles)):
        return HttpResponseBadRequest("Forbidden")

    resource_link_id = request.session.get("lti_resource_link_id")
    if not resource_link_id:
        return HttpResponseBadRequest("Missing LTI session info")

    assignment = Assignment.objects.get(slug=resource_link_id)
    uploads = request.FILES.getlist("file")
    if not uploads:
        return HttpResponseBadRequest("Missing file")

    invalid_uploads = [f.name for f in uploads if not is_allowed_upload(getattr(f, "name", ""))]
    if invalid_uploads:
        return JsonResponse({"status": "error", "message": f"Unsupported file type. Allowed: {_allowed_ext_label()}."}, status=400)
    empty_uploads = [f.name for f in uploads if getattr(f, "size", 0) <= 0]
    if empty_uploads:
        return JsonResponse({"status": "error", "message": "Empty files cannot be uploaded."}, status=400)

    existing_resources = list(AssignmentResource.objects.filter(assignment=assignment))
    if len(existing_resources) + len(uploads) > 10:
        return JsonResponse({"status": "error", "message": "You can upload up to 10 files in total."}, status=400)

    max_total_bytes = 50 * 1024 * 1024  # 50 MB
    existing_size = sum((r.file.size for r in existing_resources if r.file), 0)
    new_size = sum((getattr(f, "size", 0) for f in uploads), 0)
    if existing_size + new_size > max_total_bytes:
        return JsonResponse({"status": "error", "message": "Total upload size limit is 50MB across all files."}, status=400)

    created = []
    created_resources = []
    for uploaded in uploads:
        resource = AssignmentResource.objects.create(
            assignment=assignment,
            file=uploaded,
            comment="",
            included=True,
        )
        created_resources.append(resource)

        extracted = ""
        try:
            if resource.file and resource.file.path:
                extracted = extract_text_from_file(resource.file.path)
        except Exception:
            extracted = ""
        if _is_extracted_text_empty(extracted):
            _cleanup_resources(created_resources)
            return JsonResponse({
                "status": "error",
                "message": "No extractable text found. If this is a scanned PDF, upload a text-based version.",
            }, status=400)

        resource.comment = extracted[:MAX_SUBMISSION_TEXT_CHARS]
        resource.save(update_fields=["comment"])
        created.append({
            "id": resource.id,
            "file_name": resource.file.name if resource.file else "Uploaded file",
            "comment": resource.comment,
            "included": resource.included,
            "file_size": resource.file.size if resource.file else 0,
        })

    return JsonResponse({"status": "ok", "resources": created})


@csrf_exempt
def toggle_assignment_resource(request, resource_id=None):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    roles = request.session.get("lti_roles", [])
    if not (is_instructor_role(roles) or is_admin_role(roles)):
        return HttpResponseBadRequest("Forbidden")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST

    payload_resource_id = payload.get("resource_id")
    resource_id = payload_resource_id or resource_id
    included_raw = payload.get("included")

    if not resource_id:
        return HttpResponseBadRequest("Missing resource ID")

    resource_link_id = request.session.get("lti_resource_link_id")
    if not resource_link_id:
        return HttpResponseBadRequest("Missing LTI session info")

    assignment = Assignment.objects.get(slug=resource_link_id)
    try:
        resource = AssignmentResource.objects.get(id=resource_id, assignment=assignment)
    except AssignmentResource.DoesNotExist:
        return HttpResponseBadRequest("Invalid resource")

    included = str(included_raw).lower() in ["1", "true", "yes", "on"]
    resource.included = included
    resource.save(update_fields=["included"])

    return JsonResponse({"status": "ok", "included": resource.included})


@csrf_exempt
def toggle_assignment_resource_preference(request, resource_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    user_id = request.session.get("lti_user_id")
    if not user_id:
        return HttpResponseBadRequest("Missing user")

    resource_link_id = request.session.get("lti_resource_link_id")
    if not resource_link_id:
        return HttpResponseBadRequest("Missing LTI session info")

    assignment = Assignment.objects.get(slug=resource_link_id)
    if not assignment.allow_student_resource_toggle:
        return HttpResponseBadRequest("Resource toggles disabled")

    try:
        resource = AssignmentResource.objects.get(id=resource_id, assignment=assignment)
    except AssignmentResource.DoesNotExist:
        return HttpResponseBadRequest("Invalid resource")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST

    included_raw = payload.get("included")
    included = str(included_raw).lower() in ["1", "true", "yes", "on"]

    pref, _ = AssignmentResourcePreference.objects.update_or_create(
        resource=resource,
        user_id=str(user_id),
        defaults={"included": included},
    )

    return JsonResponse({"status": "ok", "included": pref.included})


@csrf_exempt
def delete_assignment_resource(request, resource_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    roles = request.session.get("lti_roles", [])
    if not (is_instructor_role(roles) or is_admin_role(roles)):
        return HttpResponseBadRequest("Forbidden")

    resource_link_id = request.session.get("lti_resource_link_id")
    if not resource_link_id:
        return HttpResponseBadRequest("Missing LTI session info")

    assignment = Assignment.objects.get(slug=resource_link_id)
    try:
        resource = AssignmentResource.objects.get(id=resource_id, assignment=assignment)
    except AssignmentResource.DoesNotExist:
        return HttpResponseBadRequest("Invalid resource")

    try:
        if resource.file:
            resource.file.delete(save=False)
    except Exception:
        pass
    resource.delete()
    return JsonResponse({"status": "ok"})
