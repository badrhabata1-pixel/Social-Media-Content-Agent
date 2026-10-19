"""Plans the visual, generates it, stores it next to its metadata, or falls back to a brief."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .nano_banana import ImageGenerationUnavailable, NanoBananaClient
from .prompt_builder import build_image_plan

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "generated_images"
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
IMAGE_FILENAME = re.compile(r"^[0-9a-f]{32}\.(png|jpg|webp)$")


class ImageGenerationService:
    def __init__(self, client=None, output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.client = client or NanoBananaClient()
        self.output_dir = Path(output_dir)

    def status(self) -> dict:
        return {"ai_generation_available": self.client.available, "models": list(self.client.models)}

    def create(self, directive: dict) -> dict:
        plan = build_image_plan(
            topic=directive["topic"],
            keywords=directive.get("keywords") or [],
            platform=directive.get("platform") or "Instagram",
            goal=directive.get("goal") or "Marketing",
            tone=directive.get("tone") or "Professional",
            language=directive.get("language") or "en",
            hook=directive.get("hook"),
            visual_style=directive.get("visual_style") or "auto",
            aspect_ratio=directive.get("aspect_ratio"),
        )
        result = {
            "image_id": None,
            "post_id": directive.get("post_id"),
            "mode": "prompt_only",
            "image_file": None,
            "model": None,
            "prompt": plan.prompt,
            "visual_direction": plan.visual_direction(),
            "notice": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if not directive.get("generate_image", True):
            result["notice"] = "Image generation was skipped on request. Use the prompt with any image tool."
            return result

        try:
            image = self.client.generate(plan.prompt, plan.aspect_ratio)
        except ImageGenerationUnavailable as exc:
            result["notice"] = str(exc)
            return result

        image_id = uuid.uuid4().hex
        filename = image_id + EXTENSIONS.get(image.mime_type, ".png")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / filename).write_bytes(image.data)
        result.update(image_id=image_id, mode="ai_generated", image_file=filename, model=image.model)

        metadata = {**result, "directive": directive}
        (self.output_dir / f"{image_id}.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

    def resolve_image(self, filename: str) -> Optional[Path]:
        if not IMAGE_FILENAME.match(filename):
            return None
        path = self.output_dir / filename
        return path if path.is_file() else None
