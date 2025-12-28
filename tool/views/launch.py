import json
import secrets
import jwt
import os
from urllib.parse import urlencode

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from jwt import PyJWKClient
from jwcrypto import jwk
from datetime import datetime
from tool.models import ToolConfig

LTI_PUBLIC_KEY_PATH = os.getenv("LTI_PUBLIC_KEY_PATH", "lti_keys/public.pem")


# ----------------------------------------------------------
# Simple index (debug only)
# ----------------------------------------------------------
def index(request):
    return HttpResponse("<h1>Viva LTI Test Tool</h1>")


# ----------------------------------------------------------
# LTI 1.3 Login Initiation
# ----------------------------------------------------------
@csrf_exempt
def lti_login(request):
    data = request.GET if request.method == "GET" else request.POST

    iss = data.get("iss")
    login_hint = data.get("login_hint")
    lti_message_hint = data.get("lti_message_hint")

    if not iss or not login_hint:
        return HttpResponseBadRequest("Missing login parameters")

    # State + nonce
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    request.session["lti_state"] = state
    request.session["lti_nonce"] = nonce

    tool = ToolConfig.objects.get(platform="Canvas")

    params = {
        "response_type": "id_token",
        "response_mode": "form_post",
        "scope": "openid",
        "prompt": "none",
        "client_id": tool.client_id,
        "redirect_uri": tool.redirect_uri,
        "login_hint": login_hint,
        "lti_message_hint": lti_message_hint,
        "nonce": nonce,
        "state": state,
    }
    return redirect(tool.authorize_url + "?" + urlencode(params))


# ----------------------------------------------------------
# LTI 1.3 Launch
# ----------------------------------------------------------
@csrf_exempt
def lti_launch(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    id_token = request.POST.get("id_token")
    state = request.POST.get("state")

    # ------------------------------------------------------
    # Load platform configuration
    # ------------------------------------------------------
    platform = ToolConfig.objects.first()
    if not platform:
        return HttpResponseBadRequest("Platform configuration missing")

    print("🔧 Using PlatformConfig:", platform.platform)

    # ------------------------------------------------------
    # Basic checks
    # ------------------------------------------------------
    if not id_token or state != request.session.get("lti_state"):
        return HttpResponseBadRequest("Invalid launch")

    # ------------------------------------------------------
    # Step B: Validate JWT signature (Canvas → Tool)
    # ------------------------------------------------------
    jwks_client = PyJWKClient(platform.jwks_url)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(id_token).key
    except Exception as e:
        return HttpResponseBadRequest(f"JWKS key error: {e}")

    # Store the kid Canvas used
    try:
        kid = jwt.get_unverified_header(id_token).get("kid")
        platform.last_seen_kid = kid
        platform.save(update_fields=["last_seen_kid"])
        print("🔑 Canvas launch kid:", kid)
    except Exception as e:
        print("⚠ Could not read kid header:", e)

    # ------------------------------------------------------
    # Step C: Decode ID Token (relaxed checks for now)
    # ------------------------------------------------------
    try:
        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,
                "verify_iss": False,
                "verify_exp": False,
            }
        )
    except Exception as e:
        return HttpResponseBadRequest(f"Raw decode error: {e}")

    print("CLAIMS AUDIENCE:", claims.get("aud"))
    print("LAUNCH ISSUER:", claims.get("iss"))
    print("EXPECTED ISSUER:", platform.issuer)

    # ------------------------------------------------------
    # Nonce check
    # ------------------------------------------------------
    if claims.get("nonce") != request.session.get("lti_nonce"):
        return HttpResponseBadRequest("Invalid nonce")

    # ------------------------------------------------------
    # Deployment check
    # ------------------------------------------------------
    deployment_claim = claims.get("https://purl.imsglobal.org/spec/lti/claim/deployment_id")
    if deployment_claim != platform.deployment_id:
        return HttpResponseBadRequest("Invalid deployment_id")

    # ------------------------------------------------------
    # Extract NRPS endpoint
    # ------------------------------------------------------
    nrps_claim = claims.get("https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice")
    if nrps_claim:
        nrps_url = nrps_claim.get("context_memberships_url")
        request.session["nrps_url"] = nrps_url
        print("NRPS URL saved:", nrps_url)
    else:
        request.session["nrps_url"] = None

    # ------------------------------------------------------
    # Save user/session metadata
    # ------------------------------------------------------
    request.session["lti_claims"] = claims
    request.session["lti_user_id"] = claims.get("sub")
    request.session["lti_user_name"] = (
        claims.get("given_name")
        or claims.get("family_name")
        or claims.get("name")
    )
    request.session["lti_roles"] = claims.get(
        "https://purl.imsglobal.org/spec/lti/claim/roles", []
    )
    request.session["lti_course_name"] = claims.get(
        "https://purl.imsglobal.org/spec/lti/claim/context", {}
    ).get("title")

    request.session["lti_resource_link_id"] = claims.get(
        "https://purl.imsglobal.org/spec/lti/claim/resource_link", {}
    ).get("id")

    # ------------------------------------------------------
    # Route based on message type
    # ------------------------------------------------------
    msg_type = claims.get("https://purl.imsglobal.org/spec/lti/claim/message_type")

    if msg_type == "LtiDeepLinkingRequest":
        return redirect("deeplink")

    if msg_type == "LtiResourceLinkRequest":
        return redirect("assignment_view")

    return redirect("lti_landing")


# ----------------------------------------------------------
# Landing Page (shown only if fallback)
# ----------------------------------------------------------
from datetime import datetime
from ..views.helpers import is_instructor_role, is_admin_role


def landing(request):
    claims = request.session.get("lti_claims", {})
    roles = claims.get("https://purl.imsglobal.org/spec/lti/claim/roles", [])

    return render(request, "tool/landing.html", {
        "user_name": request.session.get("lti_user_name", "Unknown"),
        "course_name": request.session.get("lti_course_name", "Unknown"),
        "roles": roles,
        "claims": claims,
        "year": datetime.now().year,

        # REQUIRED FIELDS
        "is_instructor": is_instructor_role(roles),
        "is_admin": is_admin_role(roles),
        "user_id": request.session.get("lti_user_id"),
        "resource_link_id": request.session.get("lti_resource_link_id"),
    })



# ----------------------------------------------------------
# Public JWKS Endpoint
# ----------------------------------------------------------
def jwks(request):
    print("🔥 JWKS endpoint hit from:", request.META.get("HTTP_USER_AGENT"))

    # Load your RSA public key
    with open(LTI_PUBLIC_KEY_PATH, "rb") as f:
        pub = jwk.JWK.from_pem(f.read())

    # Export raw JWK from the PEM
    raw = json.loads(pub.export_public())

    # Canvas requires ALG + USE fields
    jwk_canvas = {
        "kty": raw["kty"],
        "kid": raw["kid"],
        "alg": "RS256",
        "use": "sig",
        "n": raw["n"],
        "e": raw["e"],
    }

    # JWKS Set format
    return JsonResponse({"keys": [jwk_canvas]})

