# Django LTI 1.3 Base Tool

This is a minimal Django-based LTI 1.3 tool designed for development and
testing against Canvas LMS (or any LTI-compliant VLE).\
It includes:

-   OIDC login initiation\
-   LTI launch validation\
-   JWKS endpoint\
-   Minimal landing page showing user + course data\
-   Claims inspection table

------------------------------------------------------------------------

## 🚀 Quick Start

### 1. Clone the repository

    git clone git@github.com:rtreharne/django-lti1.3-example.git
    cd django-lti1.3-example

------------------------------------------------------------------------

## 🔑 2. Generate RSA Keys for LTI

The tool requires an RSA private/public keypair to sign LTI messages.

Run the following:

``` bash
mkdir -p lti_keys
openssl genrsa -out lti_keys/private.pem 2048
openssl rsa -in lti_keys/private.pem -pubout -out lti_keys/public.pem
```

Ensure these keys are **NOT committed to git** --- they are already
ignored in `.gitignore`.

------------------------------------------------------------------------

## ⚙️ 3. Environment Settings

Set your environment variables in `.env` (or directly in `settings.py`
for dev).

For use with a development instance of the Canvas LMS you'll need at least:

    LTI_CLIENT_ID=XXXXX
    LTI_DEPLOYMENT_ID=XXXXX
    LTI_TOOL_REDIRECT_URI=http://localhost:8000/launch/
    LTI_ISS=https://canvas.instructure.com
    LTI_PLATFORM_JWKS_URL=http://canvas.docker/api/lti/security/jwks
    LTI_AUTHORIZE_URL=http://canvas.docker/api/lti/authorize_redirect

------------------------------------------------------------------------

## 🧩 4. Start Django

    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000

------------------------------------------------------------------------

## ▶️ 5. Register Your Tool in Canvas

In **Developer Keys → LTI Key**, configure:

-   **Redirect URI**\
    `http://localhost:8000/launch/`
-   **OIDC Login URL**\
    `http://localhost:8000/login/`
-   **Tool JWKS URL**\
    `http://localhost:8000/jwks/`
-   **LTI Advantage Services** (optional)

After saving, grab your:

-   **Client ID**
-   **Deployment ID**

Add these to your settings.

------------------------------------------------------------------------

## ✔️ 6. Launch Flow

Canvas → `/login/` → redirects to Canvas OIDC → Canvas posts `id_token`
→ `/launch/`.

The tool then:

1.  Validates the JWT signature using Canvas's JWKS\
2.  Validates issuer, audience, nonce, state\
3.  Extracts user & course data\
4.  Stores claims in session\
5.  Redirects to `/landing/`

------------------------------------------------------------------------

## 🎛️ 7. Landing Page

Displays:

-   Logged-in user's given name
-   Course title
-   A full expandable LTI claims table

Useful for debugging and verifying launches.

------------------------------------------------------------------------

## 🧪 8. Testing Cookies in Cross‑Site Contexts

Endpoints:

-   `/test_set/`
-   `/test_read/`

These demonstrate session persistence in Firefox and Chrome during LTI
launches.

------------------------------------------------------------------------

## 📁 Project Structure

    tool/
        views.py
        urls.py
        templates/
    lti/
        settings.py
    lti_keys/
        private.pem
        public.pem
    manage.py

------------------------------------------------------------------------

## 📜 License

MIT (or your preferred license).

------------------------------------------------------------------------

## 👤 Author

**Dr. Robert Treharne**
