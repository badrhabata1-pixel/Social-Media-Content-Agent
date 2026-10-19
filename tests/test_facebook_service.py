"""Tests for Module 5 (Facebook publishing & metrics). The Graph API is always mocked."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi.testclient import TestClient

from app import app, get_facebook_service
from image_generation.router import get_image_service
from image_generation.service import ImageGenerationService
from social_integrations import FacebookService
from social_integrations.facebook_service import GRAPH_URL, METRIC_FIELDS

TOKEN = "test-token"
PNG = b"\x89PNG\r\n\x1a\nfake-image-bytes"
IMAGE_NAME = "0123456789abcdef0123456789abcdef.png"


def graph_response(status=200, body=None, json_error=False):
    response = MagicMock()
    response.status_code = status
    response.ok = status < 400
    if json_error:
        response.json.side_effect = ValueError("not JSON")
    else:
        response.json.return_value = {} if body is None else body
    return response


def expired_token_error():
    return graph_response(400, {"error": {
        "message": "Error validating access token: Session has expired.",
        "type": "OAuthException", "code": 190, "error_subcode": 463, "fbtrace_id": "trace-1",
    }})


def permission_error():
    return graph_response(403, {"error": {
        "message": "(#200) The user hasn't authorized the application to perform this action",
        "type": "OAuthException", "code": 200,
    }})


@pytest.fixture(autouse=True)
def graph():
    """Replaces the HTTP layer for every test: nothing here can reach Facebook."""
    with patch("social_integrations.facebook_service.requests.post") as post, \
            patch("social_integrations.facebook_service.requests.get") as get:
        yield SimpleNamespace(post=post, get=get)


@pytest.fixture
def service():
    return FacebookService(page_id="123", access_token=TOKEN)


@pytest.fixture
def image_file(tmp_path):
    path = tmp_path / IMAGE_NAME
    path.write_bytes(PNG)
    return path


# ── Publishing a text post ──────────────────────────────────────────────────

def test_text_post_payload(service, graph):
    graph.post.return_value = graph_response(200, {"id": "123_456"})

    result = service.publish_text_post("  Hello from the agent  ")

    assert result == {"success": True, "post_id": "123_456", "url": "https://facebook.com/123_456"}
    graph.post.assert_called_once()
    (url,), kwargs = graph.post.call_args
    assert url == f"{GRAPH_URL}/123/feed"
    assert kwargs["data"] == {"message": "Hello from the agent", "access_token": TOKEN}
    assert kwargs["files"] is None and kwargs["timeout"] > 0


def test_graph_api_version_is_v21():
    assert GRAPH_URL == "https://graph.facebook.com/v21.0"


@pytest.mark.parametrize("message", ["", "   ", None])
def test_empty_message_is_rejected_locally(service, graph, message):
    result = service.publish_text_post(message)
    assert result["success"] is False and result["error"]["category"] == "invalid_request"
    graph.post.assert_not_called()


def test_missing_credentials_are_reported_without_calling_facebook(monkeypatch, graph):
    monkeypatch.delenv("FACEBOOK_PAGE_ID", raising=False)
    monkeypatch.delenv("FACEBOOK_PAGE_ACCESS_TOKEN", raising=False)
    service = FacebookService()

    assert service.configured is False
    for result in (service.publish_text_post("Hi"), service.get_post_metrics("1_2")):
        assert result["error"]["category"] == "config"
        assert "FACEBOOK_PAGE_ACCESS_TOKEN" in result["error"]["message"]
    graph.post.assert_not_called()
    graph.get.assert_not_called()


def test_success_without_post_id_is_an_error(service, graph):
    graph.post.return_value = graph_response(200, {})
    assert service.publish_text_post("Hi")["error"]["category"] == "facebook"


# ── Publishing a photo post ─────────────────────────────────────────────────

def test_photo_post_uploads_file_as_multipart(service, graph, image_file):
    uploaded = {}

    def fake_post(url, data=None, files=None, timeout=None):
        name, handle, mime_type = files["source"]
        uploaded.update(url=url, data=data, name=name, mime_type=mime_type, bytes=handle.read())
        return graph_response(200, {"id": "789", "post_id": "123_456"})

    graph.post.side_effect = fake_post

    result = service.publish_photo_post("  My caption ", str(image_file))

    assert result == {"success": True, "post_id": "123_456", "photo_id": "789",
                      "url": "https://facebook.com/123_456"}
    assert uploaded["url"] == f"{GRAPH_URL}/123/photos"
    assert uploaded["data"] == {"caption": "My caption", "access_token": TOKEN}
    assert (uploaded["name"], uploaded["mime_type"], uploaded["bytes"]) == (IMAGE_NAME, "image/png", PNG)


def test_photo_post_falls_back_to_photo_id(service, graph, image_file):
    graph.post.return_value = graph_response(200, {"id": "789"})
    result = service.publish_photo_post("Caption", str(image_file))
    assert (result["post_id"], result["photo_id"]) == ("789", "789")


def test_photo_post_with_missing_file_is_rejected_locally(service, graph, tmp_path):
    result = service.publish_photo_post("Caption", str(tmp_path / "missing.png"))
    assert result["error"]["category"] == "invalid_request"
    graph.post.assert_not_called()


# ── Metrics ─────────────────────────────────────────────────────────────────

def test_metrics_are_normalized(service, graph):
    graph.get.return_value = graph_response(200, {
        "id": "123_456",
        "reactions": {"data": [], "summary": {"total_count": 12, "viewer_reaction": "NONE"}},
        "comments": {"data": [], "summary": {"total_count": 3, "can_comment": True}},
        "shares": {"count": 2},
    })

    result = service.get_post_metrics("123_456")

    assert result == {"success": True, "post_id": "123_456", "reactions": 12, "comments": 3, "shares": 2}
    (url,), kwargs = graph.get.call_args
    assert url == f"{GRAPH_URL}/123_456"
    assert kwargs["params"] == {"fields": METRIC_FIELDS, "access_token": TOKEN}
    assert METRIC_FIELDS == "reactions.summary(total_count),comments.summary(total_count),shares"


def test_new_post_metrics_default_to_zero(service, graph):
    # Facebook omits "shares" until the first share, and summaries can be missing.
    graph.get.return_value = graph_response(200, {"id": "123_456", "reactions": {"data": []}})
    result = service.get_post_metrics("123_456")
    assert (result["reactions"], result["comments"], result["shares"]) == (0, 0, 0)


# ── Error handling ──────────────────────────────────────────────────────────

def test_expired_token_is_explained(service, graph):
    graph.post.return_value = expired_token_error()

    error = service.publish_text_post("Hi")["error"]

    assert error["category"] == "facebook"
    assert (error["code"], error["subcode"], error["http_status"]) == (190, 463, 400)
    assert error["type"] == "OAuthException" and error["fbtrace_id"] == "trace-1"
    assert "expired" in error["message"] and "expired" in error["hint"]


def test_permission_denied_is_explained(service, graph):
    graph.get.return_value = permission_error()
    error = service.get_post_metrics("123_456")["error"]
    assert error["code"] == 200 and "pages_manage_posts" in error["hint"]


def test_server_error_without_json_body(service, graph):
    graph.post.return_value = graph_response(500, json_error=True)
    error = service.publish_text_post("Hi")["error"]
    assert error["http_status"] == 500 and "HTTP 500" in error["message"]


def test_network_errors_never_leak_the_token(service, graph):
    graph.post.side_effect = requests.exceptions.ConnectionError(
        f"Max retries exceeded with url: /v21.0/123/feed?access_token={TOKEN}")
    result = service.publish_text_post("Hi")
    assert result["error"]["category"] == "network"
    assert TOKEN not in str(result)


def test_timeout_is_reported(service, graph):
    graph.get.side_effect = requests.exceptions.Timeout()
    assert service.get_post_metrics("123_456")["error"]["category"] == "network"


def test_repr_hides_the_token(service):
    assert TOKEN not in repr(service) and "123" in repr(service)


# ── Token check ─────────────────────────────────────────────────────────────

def debug_token_response(**overrides):
    data = {"type": "PAGE", "application": "SocialAgentApp", "is_valid": True, "profile_id": "123",
            "scopes": ["pages_show_list", "pages_manage_posts", "pages_read_engagement"],
            "expires_at": 1792443600}
    return graph_response(200, {"data": {**data, **overrides}})


def test_ready_token_passes_the_check(service, graph):
    graph.get.return_value = debug_token_response()

    result = service.inspect_token()

    assert result["ready_to_publish"] is True and result["problems"] == []
    assert result["expires_at"] == "2026-10-19T21:00:00+00:00"
    (url,), kwargs = graph.get.call_args
    assert url == f"{GRAPH_URL}/debug_token"
    assert kwargs["params"] == {"input_token": TOKEN, "access_token": TOKEN}
    graph.post.assert_not_called()


def test_token_check_reports_wrong_page_and_missing_permissions(service, graph):
    # The real misconfiguration found on 2026-10-19: right Page token, wrong Page ID, no publish scopes.
    graph.get.return_value = debug_token_response(
        profile_id="1443854245469364", scopes=["pages_show_list", "business_management", "public_profile"])

    result = service.inspect_token()

    assert result["ready_to_publish"] is False
    assert result["missing_scopes"] == ["pages_manage_posts", "pages_read_engagement"]
    problems = " ".join(result["problems"])
    assert "FACEBOOK_PAGE_ID=1443854245469364" in problems and "pages_manage_posts" in problems


@pytest.mark.parametrize("overrides, phrase", [
    ({"is_valid": False}, "not valid"),
    ({"type": "USER"}, "not a Page access token"),
])
def test_token_check_flags_invalid_or_user_tokens(service, graph, overrides, phrase):
    graph.get.return_value = debug_token_response(**overrides)
    result = service.inspect_token()
    assert result["ready_to_publish"] is False and phrase in " ".join(result["problems"])


def test_never_expiring_token_has_no_expiry(service, graph):
    graph.get.return_value = debug_token_response(expires_at=0)
    assert service.inspect_token()["expires_at"] is None


# ── HTTP API ────────────────────────────────────────────────────────────────

@pytest.fixture
def api(service, tmp_path):
    images = ImageGenerationService(client=MagicMock(), output_dir=tmp_path)
    app.dependency_overrides[get_facebook_service] = lambda: service
    app.dependency_overrides[get_image_service] = lambda: images
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_publishes_text_post(api, graph):
    graph.post.return_value = graph_response(200, {"id": "123_456"})
    response = api.post("/publish/facebook", json={"message": "Hello"})
    assert response.status_code == 200
    assert response.json() == {"status": "success", "data": {
        "success": True, "post_id": "123_456", "url": "https://facebook.com/123_456"}}


def test_api_publishes_generated_image_as_photo(api, graph, image_file):
    graph.post.return_value = graph_response(200, {"id": "789", "post_id": "123_456"})

    response = api.post("/publish/facebook", json={"message": "Caption", "image_filename": IMAGE_NAME})

    assert response.status_code == 200 and response.json()["data"]["photo_id"] == "789"
    (url,), kwargs = graph.post.call_args
    assert url.endswith("/123/photos") and kwargs["files"]["source"][0] == IMAGE_NAME


@pytest.mark.parametrize("filename", ["fedcba9876543210fedcba9876543210.png", "../app.py", "app.py"])
def test_api_rejects_unknown_or_unsafe_image(api, graph, filename):
    response = api.post("/publish/facebook", json={"message": "Caption", "image_filename": filename})
    assert response.status_code == 404 and response.json()["status"] == "error"
    graph.post.assert_not_called()


@pytest.mark.parametrize("message", ["", "   "])
def test_api_rejects_empty_message(api, graph, message):
    assert api.post("/publish/facebook", json={"message": message}).status_code == 422
    graph.post.assert_not_called()


@pytest.mark.parametrize("graph_reply, status", [
    (expired_token_error, 400),
    (permission_error, 400),
    (lambda: graph_response(500, json_error=True), 502),
])
def test_api_maps_facebook_errors_to_clean_statuses(api, graph, graph_reply, status):
    graph.post.return_value = graph_reply()
    response = api.post("/publish/facebook", json={"message": "Hi"})
    assert response.status_code == status
    assert response.json()["status"] == "error" and TOKEN not in response.text


def test_api_network_failure_is_502(api, graph):
    graph.post.side_effect = requests.exceptions.ConnectionError("boom")
    assert api.post("/publish/facebook", json={"message": "Hi"}).status_code == 502


def test_api_not_configured_is_503(monkeypatch, graph):
    monkeypatch.delenv("FACEBOOK_PAGE_ID", raising=False)
    monkeypatch.delenv("FACEBOOK_PAGE_ACCESS_TOKEN", raising=False)
    app.dependency_overrides[get_facebook_service] = FacebookService
    try:
        response = TestClient(app).post("/publish/facebook", json={"message": "Hi"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503 and response.json()["error"]["category"] == "config"
    graph.post.assert_not_called()


@pytest.mark.parametrize("topic", ["AI tools for teams", "Boost your productivity", "Exam preparation guide",
                                   "Startup sales strategy", "Cooking Italian pasta"])
@pytest.mark.parametrize("language", ["en", "ar"])
def test_ui_publish_payload_built_from_generate_is_accepted(api, graph, posts_db, topic, language):
    # The exact payload App.jsx's handlePublishFacebook builds from a /generate response.
    generated = api.post("/generate", json={"topic": topic, "platform": "Facebook", "tone": "Casual",
                                            "language": language}).json()["data"]
    meta = generated["agent_metadata"]
    graph.post.return_value = graph_response(200, {"id": "123_456"})

    response = api.post("/publish/facebook", json={
        "message": generated["variations"][1]["full_caption"],
        "topic": topic,
        "domain": meta["detected_domain"],
        "tone": meta["tone"],
        "image_filename": None,
    })

    assert response.status_code == 200
    [post] = posts_db.get_all_posts()
    assert (post["topic"], post["domain"], post["tone"]) == (topic, meta["detected_domain"], "Casual")


def test_api_returns_metrics(api, graph):
    graph.get.return_value = graph_response(200, {
        "reactions": {"summary": {"total_count": 5}}, "comments": {"summary": {"total_count": 1}},
    })
    response = api.get("/metrics/facebook/123_456")
    assert response.status_code == 200
    assert response.json()["data"] == {"success": True, "post_id": "123_456",
                                       "reactions": 5, "comments": 1, "shares": 0}


@pytest.mark.parametrize("post_id", ["abc", "me", "123_456_789", "123-456"])
def test_api_rejects_malformed_post_ids(api, graph, post_id):
    assert api.get(f"/metrics/facebook/{post_id}").status_code == 422
    graph.get.assert_not_called()
