from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import content_agent

app = FastAPI(
    title="Social Media Content Agent - Module 3",
    description="Offline Rule-Based NLG Bilingual Social Media Content Writer Agent",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Sensors: Sensory Input Data Contract (from Person 2 - Planner Agent) ────
class DirectiveRequest(BaseModel):
    topic: str = Field(..., example="Time management mobile application for college students")
    keywords: Optional[List[str]] = Field(default_factory=list, example=["tasks", "productivity", "study routine"])
    platform: Optional[str] = Field("LinkedIn", example="LinkedIn")
    goal: Optional[str] = Field("Marketing", example="Marketing")
    tone: Optional[str] = Field("Professional", example="Professional")
    language: Optional[str] = Field("en", example="en")

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


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "agent": "Module 3 - AI Content Writer Agent",
        "mode": "Offline Deterministic Rule-Based NLG"
    }