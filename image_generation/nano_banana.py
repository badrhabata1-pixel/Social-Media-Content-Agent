"""Client for Google's Gemini "Nano Banana" image models."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
logger = logging.getLogger(__name__)

# Newest first. A 404 falls through to the next model, so renamed/retired IDs don't break the module.
DEFAULT_MODELS = ("gemini-nano-banana-2.1", "gemini-3.1-flash-image", "gemini-2.5-flash-image")
REQUEST_TIMEOUT_MS = 120_000
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
BLOCKED_FINISH_REASONS = {
    "SAFETY", "IMAGE_SAFETY", "PROHIBITED_CONTENT", "IMAGE_PROHIBITED_CONTENT",
    "BLOCKLIST", "SPII", "RECITATION", "IMAGE_RECITATION",
}


class ImageGenerationUnavailable(Exception):
    """No image could be produced. The message is safe to show to end users."""


@dataclass(frozen=True)
class GeneratedImage:
    data: bytes
    mime_type: str
    model: str


class NanoBananaClient:
    def __init__(self, api_key: Optional[str] = None, models: Optional[Sequence[str]] = None):
        self.api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) if api_key is None else api_key
        pinned = os.getenv("IMAGE_MODEL")
        self.models = tuple(models) if models else ((pinned,) if pinned else DEFAULT_MODELS)
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(
                    timeout=REQUEST_TIMEOUT_MS,
                    retry_options=types.HttpRetryOptions(attempts=3, http_status_codes=RETRY_STATUS_CODES),
                ),
            )
        return self._client

    def generate(self, prompt: str, aspect_ratio: str) -> GeneratedImage:
        if not self.available:
            raise ImageGenerationUnavailable(
                "No GEMINI_API_KEY is configured on the server, so the image prompt and designer brief "
                "were prepared instead. Paste the prompt into any image tool, or add the key to .env."
            )

        config = types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        )
        for model in self.models:
            try:
                response = self._get_client().models.generate_content(model=model, contents=prompt, config=config)
            except errors.ClientError as exc:
                if exc.code == 404:
                    logger.warning("Image model %s is not available for this key, trying the next one", model)
                    continue
                raise ImageGenerationUnavailable(_client_error_message(exc)) from exc
            except errors.APIError as exc:
                logger.warning("Gemini server error: %s", exc)
                raise ImageGenerationUnavailable(
                    "The image service is temporarily unavailable. Please try again in a moment."
                ) from exc
            except Exception as exc:
                logger.exception("Image generation request failed")
                raise ImageGenerationUnavailable(
                    "Could not reach the image service. Check the server's internet connection."
                ) from exc
            return _extract_image(response, model)

        raise ImageGenerationUnavailable("None of the configured Nano Banana models are available for this API key.")


def _extract_image(response: types.GenerateContentResponse, model: str) -> GeneratedImage:
    for part in response.parts or []:
        blob = part.inline_data
        if blob and blob.data and (blob.mime_type or "").startswith("image/"):
            return GeneratedImage(data=blob.data, mime_type=blob.mime_type, model=model)
    raise ImageGenerationUnavailable(_empty_response_message(response))


def _empty_response_message(response: types.GenerateContentResponse) -> str:
    if response.prompt_feedback and response.prompt_feedback.block_reason:
        return "The request was blocked by the image safety filter. Try rephrasing the topic."
    candidates = response.candidates or []
    reason = candidates[0].finish_reason if candidates else None
    if getattr(reason, "name", str(reason)) in BLOCKED_FINISH_REASONS:
        return "The image was blocked by the safety filter. Try rephrasing the topic or keywords."
    return "The model did not return an image this time. Please try again."


def _client_error_message(exc: errors.ClientError) -> str:
    detail = exc.message or ""
    if exc.code == 403 and "SERVICE_DISABLED" in str(exc.details):
        return ("The Gemini API is not enabled for this API key's project yet. Enable the "
                "'Generative Language API' in Google Cloud Console, wait a minute, then try again.")
    if exc.code in (401, 403) or "api key" in detail.lower():
        return "The Gemini API key was rejected. Check GEMINI_API_KEY in the server's .env file."
    if exc.code == 429 and "FreeTier" in str(exc.details):
        return ("This API key's project is on the Gemini free tier, which has no image-generation quota. "
                "Enable billing for the project in Google AI Studio, then try again.")
    if exc.code == 429:
        return ("Gemini image quota exceeded. Wait a minute and retry, or enable billing on the "
                "API key's Google Cloud project.")
    return f"Gemini rejected the request ({exc.code}): {detail}"
