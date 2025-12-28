import time
import json
import jwt
import requests
import os
from django.http import JsonResponse, HttpResponseBadRequest
from tool.models import ToolConfig

LTI_PRIVATE_KEY_PATH = os.getenv("LTI_PRIVATE_KEY_PATH", "lti_keys/private.pem")

def nrps_test(request):
    """Diagnostic endpoint: Try fetching the roster via NRPS."""

    nrps_url = request.session.get("nrps_url")
    if not nrps_url:
        return HttpResponseBadRequest("NRPS URL missing from session.")

    print("🔍 Testing NRPS fetch from:", nrps_url)

    # ---------------------------------------------------
    # Load platform config
    # ---------------------------------------------------
    platform = ToolConfig.objects.first()
    if not platform:
        return JsonResponse({"error": "PlatformConfig missing"})

    now = int(time.time())

    # ---------------------------------------------------
    # Step 1: Create client_assertion for Canvas
    # ---------------------------------------------------
    private_key = open(LTI_PRIVATE_KEY_PATH, "rb").read()

    client_assertion_payload = {
        "iss": platform.client_id,
        "sub": platform.client_id,
        "aud": platform.token_url,       # MUST match Canvas token endpoint
        "iat": now,
        "exp": now + 60,
        "jti": str(now),
    }

    client_assertion = jwt.encode(
        client_assertion_payload,
        private_key,
        algorithm="RS256",
    )

    # ---------------------------------------------------
    # Step 2: Exchange it for a service access token
    # ---------------------------------------------------
    token_resp = requests.post(
        platform.token_url,
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
            "scope": "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
        },
    )

    print("🔍 Token response:", token_resp.text)

    token_json = token_resp.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return JsonResponse({
            "error": "Failed to obtain access token",
            "details": token_json
        })

    # ---------------------------------------------------
    # Step 3: Call NRPS memberships endpoint
    # ---------------------------------------------------
    members_resp = requests.get(
        nrps_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    print("🔍 Members response:", members_resp.text)

    try:
        members_json = members_resp.json()
    except Exception:
        return JsonResponse({
            "error": "Invalid JSON from NRPS",
            "text": members_resp.text
        })

    return JsonResponse(members_json, safe=False)
