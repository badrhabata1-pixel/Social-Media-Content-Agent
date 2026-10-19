"""Publishes posts to a Facebook Page and reads their engagement through the Meta Graph API.

Every method returns a dict instead of raising: ``{"success": True, ...}`` on success, or
``{"success": False, "error": {...}}`` with a user-safe message. The access token never
appears in return values or logs.
"""

import logging
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
REQUEST_TIMEOUT_SECONDS = 30
UPLOAD_TIMEOUT_SECONDS = 120
METRIC_FIELDS = "reactions.summary(total_count),comments.summary(total_count),shares"
# Publishing needs both; reading metrics needs pages_read_engagement.
REQUIRED_SCOPES = ("pages_manage_posts", "pages_read_engagement")

# Error categories, used by the API layer to pick an HTTP status.
CONFIG, INVALID_REQUEST, NETWORK, FACEBOOK = "config", "invalid_request", "network", "facebook"

# Graph API error codes -> what the user should do about them.
# https://developers.facebook.com/docs/graph-api/guides/error-handling
TOKEN_ERROR_CODES = {102, 190}
PERMISSION_ERROR_CODES = {10} | set(range(200, 300))
RATE_LIMIT_ERROR_CODES = {4, 17, 32, 613}


def _error(category: str, message: str, **details: Any) -> dict:
    return {"success": False, "error": {"category": category, "message": message, **details}}


def _hint(code: Optional[int]) -> Optional[str]:
    if code in TOKEN_ERROR_CODES:
        return ("The Page access token is invalid or expired. Generate a new one and update "
                "FACEBOOK_PAGE_ACCESS_TOKEN in .env, then restart the server.")
    if code in PERMISSION_ERROR_CODES:
        return ("The token lacks a required permission: pages_manage_posts to publish, "
                "pages_read_engagement to read metrics.")
    if code in RATE_LIMIT_ERROR_CODES:
        return "Facebook rate limit reached. Wait a few minutes before trying again."
    if code == 100:
        return "Facebook rejected a parameter. Check the Page ID or post ID."
    return None


class FacebookService:
    def __init__(self, page_id: Optional[str] = None, access_token: Optional[str] = None):
        self.page_id = page_id or os.getenv("FACEBOOK_PAGE_ID")
        self.access_token = access_token or os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

    def __repr__(self) -> str:  # keep the token out of logs and tracebacks
        return f"FacebookService(page_id={self.page_id!r}, configured={self.configured})"

    @property
    def configured(self) -> bool:
        return bool(self.page_id and self.access_token)

    # ── Publishing ───────────────────────────────────────────────────────────
    def publish_text_post(self, message: str) -> dict:
        message = (message or "").strip()
        if not message:
            return _error(INVALID_REQUEST, "The post message is empty.")
        if not self.configured:
            return self._not_configured()

        payload, error = self._call("POST", f"{self.page_id}/feed",
                                    data={"message": message, "access_token": self.access_token})
        if error:
            return error
        post_id = payload.get("id")
        if not post_id:
            return _error(FACEBOOK, "Facebook did not return a post ID.")
        return {"success": True, "post_id": post_id, "url": f"https://facebook.com/{post_id}"}

    def publish_photo_post(self, caption: str, image_path: str) -> dict:
        path = Path(image_path)
        if not path.is_file():
            return _error(INVALID_REQUEST, f"Image file not found: {path.name}")
        if not self.configured:
            return self._not_configured()

        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as image:
            payload, error = self._call(
                "POST", f"{self.page_id}/photos",
                data={"caption": (caption or "").strip(), "access_token": self.access_token},
                files={"source": (path.name, image, mime_type)},
                timeout=UPLOAD_TIMEOUT_SECONDS,
            )
        if error:
            return error
        photo_id = payload.get("id")
        post_id = payload.get("post_id") or photo_id  # the feed post that wraps the photo
        if not post_id:
            return _error(FACEBOOK, "Facebook did not return a photo ID.")
        return {"success": True, "post_id": post_id, "photo_id": photo_id,
                "url": f"https://facebook.com/{post_id}"}

    # ── Monitoring ───────────────────────────────────────────────────────────
    def get_post_metrics(self, post_id: str) -> dict:
        if not (post_id or "").strip():
            return _error(INVALID_REQUEST, "The post ID is empty.")
        if not self.configured:
            return self._not_configured()

        payload, error = self._call("GET", post_id.strip(),
                                    params={"fields": METRIC_FIELDS, "access_token": self.access_token})
        if error:
            return error
        return {
            "success": True,
            "post_id": post_id,
            "reactions": _summary_count(payload.get("reactions")),
            "comments": _summary_count(payload.get("comments")),
            # Facebook omits "shares" entirely until the first share.
            "shares": int((payload.get("shares") or {}).get("count", 0)),
        }

    # ── Diagnostics ──────────────────────────────────────────────────────────
    def inspect_token(self) -> dict:
        """Checks, without posting anything, whether the token can publish to the configured Page.

        Uses /debug_token to read the token's type, owning Page, permissions and expiry, and lists
        every problem found in ``problems`` (empty when ``ready_to_publish`` is True).
        """
        if not self.configured:
            return self._not_configured()
        payload, error = self._call("GET", "debug_token",
                                    params={"input_token": self.access_token, "access_token": self.access_token})
        if error:
            return error

        data = payload.get("data") or {}
        token_type, token_page = data.get("type"), data.get("profile_id")
        scopes = data.get("scopes") or []
        missing = [scope for scope in REQUIRED_SCOPES if scope not in scopes]
        problems = []
        if not data.get("is_valid"):
            problems.append("The token is not valid (expired or revoked). Generate a new Page access token.")
        if token_type != "PAGE":
            problems.append(f"This is a {token_type or 'unknown'} token, not a Page access token.")
        elif token_page and str(token_page) != str(self.page_id):
            problems.append(f"The token belongs to Page {token_page}, but FACEBOOK_PAGE_ID is {self.page_id}. "
                            f"Set FACEBOOK_PAGE_ID={token_page} in .env.")
        if missing:
            problems.append(f"The token is missing permission(s): {', '.join(missing)}. "
                            "Generate a new token with these permissions granted.")
        return {
            "success": True,
            "ready_to_publish": not problems,
            "problems": problems,
            "valid": bool(data.get("is_valid")),
            "type": token_type,
            "token_page_id": token_page,
            "configured_page_id": self.page_id,
            "app": data.get("application"),
            "scopes": scopes,
            "missing_scopes": missing,
            "expires_at": _timestamp(data.get("expires_at")),
        }

    # ── HTTP ─────────────────────────────────────────────────────────────────
    def _not_configured(self) -> dict:
        return _error(CONFIG, "Facebook publishing is not configured. Set FACEBOOK_PAGE_ID and "
                              "FACEBOOK_PAGE_ACCESS_TOKEN in .env, then restart the server.")

    def _call(self, method: str, path: str, *, data=None, params=None, files=None,
              timeout: int = REQUEST_TIMEOUT_SECONDS) -> tuple[Optional[dict], Optional[dict]]:
        url = f"{GRAPH_URL}/{path}"
        try:
            if method == "POST":
                response = requests.post(url, data=data, files=files, timeout=timeout)
            else:
                response = requests.get(url, params=params, timeout=timeout)
        except requests.exceptions.Timeout:
            return None, _error(NETWORK, "Facebook did not respond in time. Please try again.")
        except requests.exceptions.RequestException as exc:
            # str(exc) can contain the request URL, and with it the access token: log the type only.
            logger.warning("Facebook request failed: %s", type(exc).__name__)
            return None, _error(NETWORK, "Could not reach Facebook. Check the server's internet connection.")

        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.ok and "error" not in body:
            return body, None

        graph_error = body.get("error") or {}
        code = graph_error.get("code")
        logger.warning("Facebook API error: HTTP %s, code %s", response.status_code, code)
        return None, _error(
            FACEBOOK,
            graph_error.get("message") or f"Facebook returned HTTP {response.status_code}.",
            http_status=response.status_code,
            code=code,
            subcode=graph_error.get("error_subcode"),
            type=graph_error.get("type"),
            fbtrace_id=graph_error.get("fbtrace_id"),
            hint=_hint(code),
        )


def _summary_count(edge: Optional[dict]) -> int:
    return int(((edge or {}).get("summary") or {}).get("total_count", 0))


def _timestamp(seconds: Optional[int]) -> Optional[str]:
    """Unix time -> ISO 8601 UTC. Facebook uses 0 for tokens that never expire."""
    if not seconds:
        return None
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()
