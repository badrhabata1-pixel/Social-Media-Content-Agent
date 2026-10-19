import logging
import sqlite3
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, List, Literal, Optional
from fastapi import Depends, FastAPI, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints, field_validator

from agent import content_agent
from analytics import AnalyticsEngine, PostsDatabase
from image_generation import router as image_router
from image_generation.router import get_image_service
from image_generation.service import ImageGenerationService
from social_integrations import FacebookService
from social_integrations.facebook_service import CONFIG, INVALID_REQUEST, NETWORK

logger = logging.getLogger(__name__)


@lru_cache
def get_posts_db() -> PostsDatabase:
    db = PostsDatabase()
    db.init_db()
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Open the analytics database at startup. A failure must not stop text/image generation,
    # so it is logged and only the analytics endpoints will report it.
    try:
        app.dependency_overrides.get(get_posts_db, get_posts_db)()
    except (sqlite3.Error, OSError):
        logger.exception("Analytics database could not be initialized")
    yield


app = FastAPI(
    title="Social Media Content Agent - Module 3",
    description="Offline Rule-Based NLG Bilingual Social Media Content Writer Agent",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router)

# ── Sensors: Sensory Input Data Contract (from Person 2 - Planner Agent) ────
class DirectiveRequest(BaseModel):
    topic: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)] = Field(
        ..., json_schema_extra={"example": "Time management mobile application for college students"}
    )
    keywords: Optional[List[str]] = Field(
        default_factory=list, json_schema_extra={"example": ["tasks", "productivity", "study routine"]}
    )
    platform: Literal["LinkedIn", "Instagram", "Twitter", "Facebook"] = Field(
        "LinkedIn", json_schema_extra={"example": "LinkedIn"}
    )
    goal: Literal["Marketing", "Educational", "Engagement"] = Field(
        "Marketing", json_schema_extra={"example": "Marketing"}
    )
    tone: Literal["Professional", "Inspirational", "Casual"] = Field(
        "Professional", json_schema_extra={"example": "Professional"}
    )
    language: Literal["en", "ar"] = Field("en", json_schema_extra={"example": "en"})

    @field_validator("keywords")
    @classmethod
    def drop_blank_keywords(cls, keywords: Optional[List[str]]) -> List[str]:
        # null -> [], and "" / "   " entries are removed instead of becoming empty hashtags
        return [k.strip() for k in keywords or [] if k.strip()]

# ── Legacy PostRequest adapter for backward compatibility ────────────────────
class LegacyPostRequest(BaseModel):
    topic: str
    platform: str
    tone: str


@app.post("/generate")
def generate_content(request: DirectiveRequest):
    """
    Actuator Endpoint: Receives high-level directives and generates
    bilingual multi-variation social media content strictly offline.
    """
    output = content_agent.generate({
        "topic": request.topic,
        "keywords": request.keywords,
        "platform": request.platform,
        "goal": request.goal,
        "tone": request.tone,
        "language": request.language,
    })
    return {"status": "success", "data": output}


@app.post("/generate-legacy")
def generate_legacy_content(request: LegacyPostRequest):
    """
    Backward compatible endpoint for previous single-caption UI queries.
    """
    output = content_agent.generate({
        "topic": request.topic,
        "keywords": [request.topic],
        "platform": request.platform,
        "goal": "Marketing",
        "tone": request.tone,
        "language": "en",
    })
    return {"status": "success", "data": output}


# ── Module 5: Facebook Page publishing & engagement metrics ──────────────────
class PublishFacebookRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=63206)] = Field(
        ..., json_schema_extra={"example": "Ready to take your study routine to the next level?"}
    )
    image_filename: Optional[str] = Field(
        None,
        description="File name of an image returned by /generate-image (stored in generated_images/)",
        json_schema_extra={"example": None},
    )
    # Context of the generated post, logged for analytics. Missing values are inferred.
    topic: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]] = None
    domain: Optional[Literal["tech_ai", "productivity_time", "education_study", "business_career", "general"]] = None
    tone: Optional[Literal["Professional", "Inspirational", "Casual"]] = None


@lru_cache
def get_facebook_service() -> FacebookService:
    return FacebookService()


FacebookDep = Annotated[FacebookService, Depends(get_facebook_service)]
ImageServiceDep = Annotated[ImageGenerationService, Depends(get_image_service)]
PostsDbDep = Annotated[PostsDatabase, Depends(get_posts_db)]


def _log_published_post(db: PostsDatabase, post_id: str, request: PublishFacebookRequest) -> None:
    """Records a published post for analytics. The post is already live, so a database
    failure is logged rather than reported as a failed publish (which could invite a re-post)."""
    topic = request.topic or request.message.splitlines()[0][:120]
    try:
        db.insert_post(platform="facebook", platform_post_id=post_id, topic=topic,
                       domain=request.domain or content_agent.detect_domain(topic),
                       tone=request.tone or "Unknown")
    except sqlite3.Error:
        logger.exception("Published post %s could not be logged for analytics", post_id)


def _facebook_response(result: dict):
    if result["success"]:
        return {"status": "success", "data": result}
    error = result["error"]
    if error["category"] == CONFIG:
        status_code = 503
    elif error["category"] == INVALID_REQUEST:
        status_code = 400
    elif error["category"] == NETWORK:
        status_code = 502
    else:  # Facebook answered with an error: 4xx = it rejected the request, 5xx = it failed
        status_code = 400 if (error.get("http_status") or 500) < 500 else 502
    return JSONResponse(status_code=status_code, content={"status": "error", "error": error})


@app.post("/publish/facebook")
def publish_to_facebook(request: PublishFacebookRequest, facebook: FacebookDep, images: ImageServiceDep,
                        db: PostsDbDep):
    """Publishes a text post, or a photo post when image_filename names a generated image,
    and logs it for analytics."""
    if request.image_filename:
        image_path = images.resolve_image(request.image_filename)
        if image_path is None:
            return JSONResponse(status_code=404, content={"status": "error", "error": {
                "category": INVALID_REQUEST, "message": "Image not found in generated_images/."}})
        result = facebook.publish_photo_post(request.message, str(image_path))
    else:
        result = facebook.publish_text_post(request.message)
    if result["success"]:
        _log_published_post(db, result["post_id"], request)
    return _facebook_response(result)


@app.get("/metrics/facebook/{post_id}")
def facebook_post_metrics(
    post_id: Annotated[str, Path(pattern=r"^\d+(_\d+)?$", max_length=64)],
    facebook: FacebookDep,
):
    """Live engagement for a published post: reactions, comments and shares."""
    return _facebook_response(facebook.get_post_metrics(post_id))


# ── Module 6: Monitor & analytics (closes the loop: publish → measure → compare) ─
@app.post("/analytics/sync")
def sync_analytics(db: PostsDbDep, facebook: FacebookDep):
    """Fetches live metrics from Facebook for every logged post and stores them."""
    return _facebook_response(AnalyticsEngine(db, facebook).sync_all_metrics())


@app.get("/analytics/report")
def analytics_report(db: PostsDbDep, facebook: FacebookDep):
    """Engagement compared by domain, topic and tone, from the stored metrics."""
    return {"status": "success", "data": AnalyticsEngine(db, facebook).generate_comparative_report()}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "agent": "Module 3 - AI Content Writer Agent",
        "mode": "Offline Rule-Based NLG"
    }