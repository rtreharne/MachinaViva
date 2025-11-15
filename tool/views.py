import json, secrets, jwt, requests
from urllib.parse import urlencode
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.conf import settings
from jwt import PyJWKClient
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render
from datetime import datetime

def landing(request):
    user_name = request.session.get("lti_user_name", "Unknown User")
    course_name = request.session.get("lti_course_name", "Unknown Course")
    claims = request.session.get("lti_claims", {})

    return render(request, "tool/landing.html", {
        "user_name": user_name,
        "course_name": course_name,
        "claims": claims,
        "year": datetime.now().year,
    })


def index(request):
    return HttpResponse("<h1>Viva LTI Test Tool</h1>")


@csrf_exempt
def lti_login(request):
    """
    Step 1: Handle OIDC login initiation from Canvas.
    Canvas may call this endpoint using GET or POST.
    """
    data = request.GET if request.method == "GET" else request.POST

    iss = data.get("iss")
    login_hint = data.get("login_hint")
    lti_message_hint = data.get("lti_message_hint")
    target_link_uri = data.get("target_link_uri")

    if not iss or not login_hint:
        return HttpResponseBadRequest("Missing login parameters (iss or login_hint)")

    # Create state + nonce and save to session
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    request.session["lti_state"] = state
    request.session["lti_nonce"] = nonce

    redirect_uri = settings.LTI_TOOL_REDIRECT_URI

    # OIDC params (MUST include scope=openid)
    params = {
        "response_type": "id_token",
        "response_mode": "form_post",
        "scope": "openid",
        "prompt": "none",                       # REQUIRED
        "client_id": settings.LTI_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "login_hint": login_hint,
        "lti_message_hint": lti_message_hint,
        "nonce": nonce,
        "state": state,
    }


    # Build final redirect URL
    auth_url = settings.LTI_AUTHORIZE_URL + "?" + urlencode(params)

    return redirect(auth_url)


@csrf_exempt
def lti_launch(request):
    """
    Step 2: Canvas returns an id_token via POST.
    We must validate: state, nonce, JWT signature, deployment_id, audience, issuer.
    """
    print("---- LAUNCH CALLED ----")
    print("POST data:", request.POST.dict())
    print("Session:", dict(request.session.items()))

    if request.method != "POST":
        return HttpResponseBadRequest("Launch must be POST")

    id_token = request.POST.get("id_token")
    state = request.POST.get("state")

    if not id_token:
        print("ERROR: Missing id_token")
        return HttpResponseBadRequest("Missing id_token")

    if state != request.session.get("lti_state"):
        print("ERROR: Invalid state")
        print("Received:", state)
        print("Expected:", request.session.get("lti_state"))
        return HttpResponseBadRequest("Invalid state")

    # Validate JWT signature against Canvas’s JWKS
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
        print("JWT validation error:", e)
        return HttpResponseBadRequest(f"JWT validation error: {e}")

    # Check nonce
    if claims.get("nonce") != request.session.get("lti_nonce"):
        print("ERROR: Invalid nonce")
        return HttpResponseBadRequest("Invalid nonce")

    # Check deployment ID
    deployment_id = claims.get("https://purl.imsglobal.org/spec/lti/claim/deployment_id")
    if deployment_id != settings.LTI_DEPLOYMENT_ID:
        print("ERROR: Invalid deployment_id")
        print("Received:", deployment_id)
        print("Expected:", settings.LTI_DEPLOYMENT_ID)
        return HttpResponseBadRequest("Invalid deployment_id")

    # Success
    print("Successful LTI launch!")

    # Extract user + course info from claims
    user_name = claims.get("given_name") or claims.get("family_name") or claims.get("name")
    course_name = claims.get("https://purl.imsglobal.org/spec/lti/claim/context", {}).get("title")

    # Save to session
    request.session["lti_user_name"] = user_name
    request.session["lti_course_name"] = course_name

    # Save full claims for debugging/display
    request.session["lti_claims"] = claims

    return redirect("/landing/")


def jwks(request):
    """Serve your tool’s public JWK."""
    from jwcrypto import jwk

    with open("lti_keys/public.pem", "rb") as f:
        pub = jwk.JWK.from_pem(f.read())

    return JsonResponse({"keys": [json.loads(pub.export_public())]})

from django.http import HttpResponse

def test_set_cookie(request):
    request.session['foo'] = 'bar'
    return HttpResponse("Cookie set: foo=bar")

def test_read_cookie(request):
    val = request.session.get('foo')
    return HttpResponse(f"Cookie read: foo={val}")
