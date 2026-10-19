"""HTTP endpoints for Module 4 (AI Image Generation)."""

from functools import lru_cache
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, StringConstraints

from .prompt_builder import AspectRatio, VisualStyle
from .service import ImageGenerationService

Topic = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Keyword = Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]


class ImageDirective(BaseModel):
    topic: Topic
    keywords: list[Keyword] = Field(default_factory=list, max_length=15)
    platform: str = Field("Instagram", max_length=40)
    goal: str = Field("Marketing", max_length=40)
    tone: str = Field("Professional", max_length=40)
    language: Literal["en", "ar"] = "en"
    hook: Optional[str] = Field(None, max_length=600, description="Post headline from the content writer")
    post_id: Optional[str] = Field(None, max_length=64, description="ID of the post this image belongs to")
    visual_style: VisualStyle = "auto"
    aspect_ratio: Optional[AspectRatio] = Field(None, description="Overrides the platform's default ratio")
    generate_image: bool = Field(True, description="False returns only the prompt and designer brief")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "topic": "Time management mobile application for college students",
                "keywords": ["tasks", "productivity", "study routine"],
                "platform": "Instagram",
                "goal": "Marketing",
                "tone": "Inspirational",
                "language": "en",
                "hook": "Transform the way you approach time management and unlock your true potential.",
            }]
        }
    }


router = APIRouter(tags=["Module 4 - Image Generation"])


@lru_cache
def get_image_service() -> ImageGenerationService:
    return ImageGenerationService()


ServiceDep = Annotated[ImageGenerationService, Depends(get_image_service)]


@router.post("/generate-image")
def generate_image(directive: ImageDirective, request: Request, service: ServiceDep):
    result = service.create(directive.model_dump())
    image_file = result.pop("image_file")
    result["image_url"] = str(request.url_for("get_generated_image", filename=image_file)) if image_file else None
    return {"status": "success", "data": result}


@router.get("/image-service/status")
def image_service_status(service: ServiceDep):
    return service.status()


@router.get("/images/{filename}", name="get_generated_image")
def get_generated_image(filename: str, service: ServiceDep, download: bool = False):
    path = service.resolve_image(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path, filename=filename if download else None)
