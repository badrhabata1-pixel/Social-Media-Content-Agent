import json

import pytest
from fastapi.testclient import TestClient

from app import app
from image_generation.nano_banana import GeneratedImage, ImageGenerationUnavailable, NanoBananaClient
from image_generation.prompt_builder import build_image_plan, detect_visual_domain
from image_generation.router import get_image_service
from image_generation.service import ImageGenerationService

FAKE_PNG = b"\x89PNG\r\n\x1a\nfake-image-bytes"


class FakeClient:
    available = True
    models = ("fake-nano-banana",)

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def generate(self, prompt, aspect_ratio):
        self.calls.append((prompt, aspect_ratio))
        if self.error:
            raise self.error
        return GeneratedImage(data=FAKE_PNG, mime_type="image/png", model="fake-nano-banana")


@pytest.fixture
def api(tmp_path):
    fake = FakeClient()
    service = ImageGenerationService(client=fake, output_dir=tmp_path)
    app.dependency_overrides[get_image_service] = lambda: service
    yield TestClient(app), fake, tmp_path
    app.dependency_overrides.clear()


# ── Prompt builder ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("platform, ratio, dimensions", [
    ("Instagram", "4:5", "1080x1350"),
    ("Facebook", "1:1", "1080x1080"),
    ("LinkedIn", "16:9", "1920x1080"),
    ("Twitter / X", "16:9", "1920x1080"),
])
def test_platform_drives_aspect_ratio(platform, ratio, dimensions):
    plan = build_image_plan(topic="Study habits", platform=platform)
    assert (plan.aspect_ratio, plan.dimensions) == (ratio, dimensions)


def test_aspect_ratio_override_wins():
    plan = build_image_plan(topic="Study habits", platform="Instagram", aspect_ratio="9:16")
    assert (plan.aspect_ratio, plan.dimensions) == ("9:16", "1080x1920")


def test_goal_selects_framework_and_auto_style():
    assert build_image_plan(topic="x", goal="Marketing").visual_style == "Photorealistic photography"
    educational = build_image_plan(topic="x", goal="Educational")
    assert educational.framework == "PAS"
    assert educational.visual_style == "Premium 3D illustration"
    assert build_image_plan(topic="x", goal="Engagement", visual_style="illustration").visual_style == \
        "Editorial flat illustration"


def test_prompt_carries_post_context_and_rules():
    plan = build_image_plan(
        topic='A "smart" planner app', keywords=["focus", " "], platform="LinkedIn",
        tone="Inspirational", hook="Own your day",
    )
    assert "A 'smart' planner app" in plan.prompt
    assert "Themes to reflect: focus." in plan.prompt
    assert 'headline "Own your day"' in plan.prompt
    assert "golden-hour" in plan.prompt
    assert "left third" in plan.prompt
    assert "Do not render any text" in plan.prompt
    assert "prompt" not in plan.visual_direction()


def test_arabic_localizes_people_and_overlay_side():
    plan = build_image_plan(topic="تنظيم الوقت للطلاب", language="ar")
    assert "Arab / Middle Eastern" in plan.prompt
    assert "right third" in plan.prompt
    assert "Cairo or Tajawal" in plan.text_overlay


@pytest.mark.parametrize("text, domain", [
    ("AI tools for marketing", "tech_ai"),
    ("How to maintain a garden", "general"),
    ("مذاكرة الامتحانات", "education_study"),
    ("Startup sales strategy", "business_career"),
])
def test_domain_detection(text, domain):
    assert detect_visual_domain(text) == domain


# ── Service ─────────────────────────────────────────────────────────────────

def test_without_api_key_returns_prompt_and_brief(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    service = ImageGenerationService(client=NanoBananaClient(), output_dir=tmp_path)

    result = service.create({"topic": "Healthy breakfast ideas", "platform": "Instagram"})

    assert result["mode"] == "prompt_only"
    assert result["image_file"] is None
    assert "GEMINI_API_KEY" in result["notice"]
    assert result["prompt"]
    assert result["visual_direction"]["aspect_ratio"] == "4:5"
    assert list(tmp_path.iterdir()) == []


def test_generated_image_is_saved_and_linked_to_post(tmp_path):
    fake = FakeClient()
    service = ImageGenerationService(client=fake, output_dir=tmp_path)

    result = service.create({"topic": "Coffee shop launch", "platform": "Facebook", "post_id": "post-42"})

    assert result["mode"] == "ai_generated"
    assert result["model"] == "fake-nano-banana"
    assert fake.calls[0][1] == "1:1"
    assert (tmp_path / result["image_file"]).read_bytes() == FAKE_PNG
    metadata = json.loads((tmp_path / f"{result['image_id']}.json").read_text(encoding="utf-8"))
    assert metadata["post_id"] == "post-42"
    assert metadata["prompt"] == result["prompt"]


def test_service_failure_falls_back_with_reason(tmp_path):
    fake = FakeClient(error=ImageGenerationUnavailable("quota exceeded"))
    result = ImageGenerationService(client=fake, output_dir=tmp_path).create({"topic": "x"})
    assert result["mode"] == "prompt_only"
    assert result["notice"] == "quota exceeded"


@pytest.mark.parametrize("details, expected", [
    ({"error": {"details": [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}},
     "free tier"),
    ({"error": {"message": "Rate limit"}}, "Wait a minute"),
])
def test_quota_errors_explain_the_fix(details, expected):
    from google.genai import errors
    from image_generation.nano_banana import _client_error_message
    assert expected in _client_error_message(errors.ClientError(429, details))


def test_disabled_service_is_not_reported_as_bad_key():
    from google.genai import errors
    from image_generation.nano_banana import _client_error_message
    details = {"error": {"message": "Generative Language API has not been used in project 123",
                         "details": [{"reason": "SERVICE_DISABLED"}]}}
    assert "not enabled" in _client_error_message(errors.ClientError(403, details))


def test_generate_image_false_skips_api_call(tmp_path):
    fake = FakeClient()
    result = ImageGenerationService(client=fake, output_dir=tmp_path).create({"topic": "x", "generate_image": False})
    assert result["mode"] == "prompt_only"
    assert fake.calls == []


# ── HTTP API ────────────────────────────────────────────────────────────────

def test_generate_image_endpoint_returns_servable_url(api):
    client, _, _ = api
    response = client.post("/generate-image", json={"topic": "Remote work tips", "platform": "LinkedIn"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["mode"] == "ai_generated"
    assert "image_file" not in data

    image = client.get(data["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.content == FAKE_PNG
    assert "attachment" in client.get(data["image_url"], params={"download": True}).headers["content-disposition"]


def test_blank_topic_is_rejected(api):
    client, _, _ = api
    assert client.post("/generate-image", json={"topic": "   "}).status_code == 422


def test_unsupported_aspect_ratio_is_rejected(api):
    client, _, _ = api
    assert client.post("/generate-image", json={"topic": "x", "aspect_ratio": "7:3"}).status_code == 422


@pytest.mark.parametrize("filename", ["..%2Fapp.py", "app.py", "0" * 32 + ".png", "0" * 32 + ".json"])
def test_image_route_only_serves_existing_generated_images(api, filename):
    client, _, _ = api
    assert client.get(f"/images/{filename}").status_code == 404


def test_status_endpoint(api):
    client, _, _ = api
    assert client.get("/image-service/status").json() == {
        "ai_generation_available": True, "models": ["fake-nano-banana"],
    }
