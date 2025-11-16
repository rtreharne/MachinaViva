import json, secrets, jwt, requests
from urllib.parse import urlencode
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.conf import settings
from jwt import PyJWKClient
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta

from .models import Assignment, Submission
from jwcrypto import jwk


# ============================================================
# Helper functions
# ============================================================

def is_instructor_role(roles):
    instructor_keywords = [
        "Instructor", "ContentDeveloper", "TeachingAssistant",
        "CourseDesigner"
    ]
    return any(any(k in r for k in instructor_keywords) for r in roles)


def is_admin_role(roles):
    admin_keywords = ["Admin", "Administrator", "SysAdmin"]
    return any(any(k in r for k in admin_keywords) for r in roles)


def is_student_role(roles):
    return not is_instructor_role(roles) and not is_admin_role(roles)


# ============================================================
# Deep Linking – Create Assignment Only
# ============================================================

def build_deep_link_jwt(return_url, title, launch_url, description="", custom_params=None):
    now = datetime.utcnow()

    private_key = open("lti_keys/private.pem", "rb").read()
    pub = jwk.JWK.from_pem(open("lti_keys/public.pem", "rb").read())
    kid = pub.export_public(as_dict=True)["kid"]

    content_item = {
        "type": "ltiResourceLink",
        "title": title,
        "url": launch_url,
        "text": description,
        "description": description,
    }

    if custom_params:
        content_item["custom"] = custom_params

    payload = {
        "iss": settings.LTI_CLIENT_ID,
        "aud": settings.LTI_ISS,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "nonce": secrets.token_urlsafe(12),
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": return_url,
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [content_item],
    }

    headers = {"alg": "RS256", "kid": kid, "typ": "JWT"}

    return jwt.encode(payload, private_key, algorithm="RS256", headers=headers)


def deeplink(request):
    """Instructor selecting content (Deep Linking Launch)."""
    claims = request.session.get("lti_claims")
    if not claims:
        return HttpResponse("Missing LTI claims", status=400)

    deep_link = claims.get("https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings")
    if not deep_link:
        return HttpResponse("Not a deep linking launch", status=400)

    return render(request, "tool/deeplink.html", {
        "deep_link_return": deep_link["deep_link_return_url"],
    })


@csrf_exempt
def deeplink_submit(request):
    """Return Deep Linking Content Item to Canvas."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    return_url = request.POST.get("return_url")
    title = request.POST.get("title", "Viva Assignment")
    description = request.POST.get("description", "")
    allow_multiple = (request.POST.get("allow_multiple") == "true")

    custom_params = {
        "allow_multiple_submissions": "true" if allow_multiple else "false"
    }

    jwt_token = build_deep_link_jwt(
        return_url=return_url,
        title=title,
        launch_url="https://app.ninepointeightone.com/launch/",
        description=description,
        custom_params=custom_params,
    )

    return render(request, "tool/deeplink_return.html", {
        "return_url": return_url,
        "jwt": jwt_token,
    })


# ============================================================
# INTERNAL ASSIGNMENT EDITING (no deep linking)
# ============================================================

def assignment_edit(request):
    """Instructor edits assignment settings inside LTI tool."""
    roles = request.session.get("lti_roles", [])
    if not (is_instructor_role(roles) or is_admin_role(roles)):
        return HttpResponse("Forbidden", status=403)

    resource_link_id = request.session.get("lti_resource_link_id")
    assignment = Assignment.objects.get(slug=resource_link_id)

    return render(request, "tool/assignment_edit.html", {
        "assignment": assignment,
    })


@csrf_exempt
def assignment_edit_save(request):
    """Save local assignment settings (NO deep linking)."""
    roles = request.session.get("lti_roles", [])
    if not (is_instructor_role(roles) or is_admin_role(roles)):
        return HttpResponse("Forbidden", status=403)

    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    resource_link_id = request.session.get("lti_resource_link_id")
    assignment = Assignment.objects.get(slug=resource_link_id)

    assignment.title = request.POST.get("title", assignment.title)
    assignment.description = request.POST.get("description", assignment.description)
    assignment.allow_multiple_submissions = (request.POST.get("allow_multiple") == "true")
    assignment.save()

    return redirect("assignment_view")


# ============================================================
# Assignment View – Student & Instructor
# ============================================================

def assignment_view(request):
    resource_link_id = request.session.get("lti_resource_link_id")
    roles = request.session.get("lti_roles", [])
    user_id = request.session.get("lti_user_id")

    if not resource_link_id:
        return HttpResponse("No LTI resource_link_id", status=400)

    assignment, created = Assignment.objects.get_or_create(
        slug=resource_link_id,
        defaults={"title": f"Assignment {resource_link_id}"}
    )

    # Instructor dashboard
    if is_instructor_role(roles) or is_admin_role(roles):
        submissions = Submission.objects.filter(assignment=assignment)
        return render(request, "tool/instructor_review.html", {
            "assignment": assignment,
            "submissions": submissions,
        })

    # Student view
    student_submissions = Submission.objects.filter(
        assignment=assignment,
        user_id=user_id
    ).order_by("-created_at")

    return render(request, "tool/student_submit.html", {
        "assignment": assignment,
        "user_id": user_id,
        "latest_submission": student_submissions.first() if student_submissions else None,
        "past_submissions": student_submissions,
    })


# ============================================================
# Student Submission
# ============================================================

@csrf_exempt
def submit_text(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    user_id = request.session.get("lti_user_id")
    resource_link_id = request.session.get("lti_resource_link_id")

    if not user_id or not resource_link_id:
        return HttpResponseBadRequest("Missing session info")

    assignment = Assignment.objects.get(slug=resource_link_id)

    Submission.objects.create(
        assignment=assignment,
        user_id=user_id,
        comment=request.POST.get("text", "").strip(),
        file=None,
    )

    return redirect("assignment_view")


# ============================================================
# Landing Page
# ============================================================

def landing(request):
    claims = request.session.get("lti_claims", {})
    roles = claims.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])

    return render(request, "tool/landing.html", {
        "user_name": request.session.get("lti_user_name", "Unknown"),
        "course_name": request.session.get("lti_course_name", "Unknown"),
        "claims": claims,
        "roles": roles,
        "is_instructor": is_instructor_role(roles),
        "is_admin": is_admin_role(roles),
        "user_id": request.session.get("lti_user_id"),
        "resource_link_id": request.session.get("lti_resource_link_id"),
        "year": datetime.now().year,
    })


# ============================================================
# LTI 1.3 Launch Flow
# ============================================================

def index(request):
    return HttpResponse("<h1>Viva LTI Test Tool</h1>")


@csrf_exempt
def lti_login(request):
    data = request.GET if request.method == "GET" else request.POST

    iss = data.get("iss")
    login_hint = data.get("login_hint")
    lti_message_hint = data.get("lti_message_hint")

    if not iss or not login_hint:
        return HttpResponseBadRequest("Missing login parameters")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    request.session["lti_state"] = state
    request.session["lti_nonce"] = nonce

    params = {
        "response_type": "id_token",
        "response_mode": "form_post",
        "scope": "openid",
        "prompt": "none",
        "client_id": settings.LTI_CLIENT_ID,
        "redirect_uri": settings.LTI_TOOL_REDIRECT_URI,
        "login_hint": login_hint,
        "lti_message_hint": lti_message_hint,
        "nonce": nonce,
        "state": state,
    }

    return redirect(settings.LTI_AUTHORIZE_URL + "?" + urlencode(params))


@csrf_exempt
def lti_launch(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    id_token = request.POST.get("id_token")
    state = request.POST.get("state")

    if not id_token or state != request.session.get("lti_state"):
        return HttpResponseBadRequest("Invalid launch")

    # --- Validate JWT ---
    jwks_client = PyJWKClient(settings.LTI_PLATFORM_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(id_token).key

    try:
        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.LTI_CLIENT_ID,
            issuer=settings.LTI_ISS,
        )
    except Exception as e:
        return HttpResponseBadRequest(f"JWT error: {e}")

    # Nonce check
    if claims.get("nonce") != request.session.get("lti_nonce"):
        return HttpResponseBadRequest("Invalid nonce")

    # Deployment ID check
    deployment_id = claims.get("https://purl.imsglobal.org/spec/lti/claim/deployment_id")
    if deployment_id != settings.LTI_DEPLOYMENT_ID:
        return HttpResponseBadRequest("Invalid deployment_id")

    # Save session fields
    request.session["lti_claims"] = claims
    request.session["lti_user_id"] = claims.get("sub")
    request.session["lti_user_name"] = (
        claims.get("given_name") or claims.get("family_name") or claims.get("name")
    )
    request.session["lti_roles"] = claims.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])
    request.session["lti_course_name"] = claims.get(
        "https://purl.imsglobal.org/spec/lti/claim/context", {}
    ).get("title")
    request.session["lti_resource_link_id"] = claims.get(
        "https://purl.imsglobal.org/spec/lti/claim/resource_link", {}
    ).get("id")

    message_type = claims.get("https://purl.imsglobal.org/spec/lti/claim/message_type")

    # Deep Linking → setup only
    if message_type == "LtiDeepLinkingRequest":
        return redirect("deeplink")

    # ResourceLink → show assignment
    if message_type == "LtiResourceLinkRequest":
        return redirect("assignment_view")

    # Otherwise fallback
    return redirect("lti_landing")


# ============================================================
# JWKS
# ============================================================

def jwks(request):
    pub = jwk.JWK.from_pem(open("lti_keys/public.pem", "rb").read())
    return JsonResponse({"keys": [json.loads(pub.export_public())]})


# Debug helpers
def test_set_cookie(request):
    request.session["foo"] = "bar"
    return HttpResponse("Cookie set")


def test_read_cookie(request):
    return HttpResponse(f"Cookie: {request.session.get('foo')}")
