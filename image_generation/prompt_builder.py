"""Turns a post directive into an art-directed image prompt plus a designer brief."""

import re
from dataclasses import asdict, dataclass, field
from typing import Literal, Optional, Sequence, get_args

from agent import ContentWriterAgent

AspectRatio = Literal["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
VisualStyle = Literal["auto", "photo", "3d", "illustration"]
SUPPORTED_ASPECT_RATIOS = get_args(AspectRatio)

PLATFORMS = {
    "instagram": {
        "label": "Instagram",
        "aspect_ratio": "4:5",
        "aesthetic": "Make it scroll-stopping and highly aesthetic, with cohesive color grading "
                     "that fits a curated Instagram feed.",
    },
    "facebook": {
        "label": "Facebook",
        "aspect_ratio": "1:1",
        "aesthetic": "Keep it warm, authentic and relatable, with a community-oriented, everyday feel.",
    },
    "linkedin": {
        "label": "LinkedIn",
        "aspect_ratio": "16:9",
        "aesthetic": "Keep it polished, credible and uncluttered, like a premium editorial image "
                     "on a professional network.",
    },
    "twitter": {
        "label": "X (Twitter)",
        "aspect_ratio": "16:9",
        "aesthetic": "Make it bold and high-contrast with one clear focal point that still reads "
                     "well as a small timeline thumbnail.",
    },
}

TONES = {
    "professional": {
        "mood": "confident, credible and polished",
        "lighting": "soft, diffused studio-quality light with gentle shadows",
        "palette": [("Deep Navy", "#0F172A"), ("Slate", "#334155"),
                    ("Off-White", "#F8FAFC"), ("Accent Blue", "#2563EB")],
    },
    "inspirational": {
        "mood": "uplifting, hopeful and aspirational",
        "lighting": "cinematic golden-hour backlight with a warm, gentle lens glow",
        "palette": [("Amber", "#F59E0B"), ("Coral Rose", "#FB7185"),
                    ("Deep Teal", "#0F766E"), ("Warm Cream", "#FFF7ED")],
    },
    "casual": {
        "mood": "friendly, playful and approachable",
        "lighting": "bright natural daylight with a fresh, airy feel",
        "palette": [("Sunny Yellow", "#FACC15"), ("Fresh Green", "#22C55E"),
                    ("Sky Blue", "#38BDF8"), ("Clean White", "#FFFFFF")],
    },
}

FRAMEWORKS = {
    "AIDA": {
        "default_style": "photo",
        "composition": "Compose it as a hero shot: one clear focal subject that represents the solution "
                       "or the positive outcome, placed on the rule of thirds, with an aspirational, "
                       "desirable feel.",
    },
    "PAS": {
        "default_style": "3d",
        "composition": "Use a clear visual metaphor that explains the idea at a glance, showing the shift "
                       "from a problem state to a solved state, with few, purposeful elements and no clutter.",
    },
    "Story-Lesson-Question": {
        "default_style": "photo",
        "composition": "Capture an authentic, candid storytelling moment with genuine human emotion in a "
                       "relatable everyday scenario, as if photographed in the middle of a real moment.",
    },
}

STYLES = {
    "photo": {
        "label": "Photorealistic photography",
        "directive": "A photorealistic, high-end commercial photograph shot on a full-frame camera with a "
                     "50mm lens, shallow depth of field and crisp focus on the main subject.",
    },
    "3d": {
        "label": "Premium 3D illustration",
        "directive": "A polished, modern 3D illustration with soft global illumination, smooth matte "
                     "materials and gentle ambient occlusion, as clean as a tech brand's hero artwork.",
    },
    "illustration": {
        "label": "Editorial flat illustration",
        "directive": "A modern flat vector-style editorial illustration with clean geometric shapes, a "
                     "subtle grain texture and a balanced, harmonious composition.",
    },
}

DOMAIN_CUES = {
    "tech_ai": "Setting cues: sleek modern devices, subtle glowing interface elements and a clean, "
               "futuristic environment with cool blue and violet accents.",
    "productivity_time": "Setting cues: a calm, minimalist, well-organized workspace with a planner and a "
                         "subtle clock or timer motif, conveying focus and order.",
    "education_study": "Setting cues: a bright study environment with open books, notes and a laptop, in a "
                       "library or campus atmosphere with warm, focused energy.",
    "business_career": "Setting cues: a contemporary office or co-working space, confident professionals "
                       "and subtle motifs of growth and momentum.",
}

NO_TEXT_RULE = "Do not render any text, letters, numbers, logos or watermarks anywhere in the image."


@dataclass(frozen=True)
class ImagePlan:
    prompt: str
    platform: str
    aspect_ratio: str
    dimensions: str
    visual_style: str
    framework: str
    domain: str
    mood: str
    lighting: str
    composition: str
    text_overlay: str
    platform_notes: str
    palette: list = field(default_factory=list)

    def visual_direction(self) -> dict:
        direction = asdict(self)
        direction.pop("prompt")
        return direction


def _clean(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (text or "").replace('"', "'")).strip()


def _platform_key(platform: str) -> str:
    p = platform.strip().lower()
    if "insta" in p:
        return "instagram"
    if "linked" in p:
        return "linkedin"
    if "twitter" in p or p == "x":
        return "twitter"
    return "facebook"


def _tone_key(tone: str) -> str:
    t = tone.lower()
    if "inspir" in t:
        return "inspirational"
    if any(word in t for word in ("casual", "funny", "friendly", "playful")):
        return "casual"
    return "professional"


def _keyword_in(keyword: str, text: str) -> bool:
    if not keyword.isascii():
        return keyword in text
    # ASCII stems match at word starts only, so "ai" can't hit "maintain".
    pattern = rf"\b{re.escape(keyword)}\b" if len(keyword) <= 2 else rf"\b{re.escape(keyword)}"
    return re.search(pattern, text) is not None


def detect_visual_domain(text: str) -> str:
    lowered = text.lower()
    for domain, data in ContentWriterAgent.DOMAINS.items():
        if any(_keyword_in(kw, lowered) for kw in data["keywords"]):
            return domain
    return "general"


def recommended_dimensions(aspect_ratio: str) -> str:
    w, h = (int(x) for x in aspect_ratio.split(":"))
    if w >= h:
        return f"{round(1080 * w / h)}x1080"
    return f"1080x{round(1080 * h / w)}"


def build_image_plan(
    topic: str,
    keywords: Sequence[str] = (),
    platform: str = "Instagram",
    goal: str = "Marketing",
    tone: str = "Professional",
    language: str = "en",
    hook: Optional[str] = None,
    visual_style: str = "auto",
    aspect_ratio: Optional[str] = None,
) -> ImagePlan:
    topic = _clean(topic)
    keywords = [k for k in (_clean(k) for k in keywords) if k]
    hook = _clean(hook)

    platform_spec = PLATFORMS[_platform_key(platform)]
    tone_spec = TONES[_tone_key(tone)]
    framework = ContentWriterAgent.resolve_framework(goal)
    framework_spec = FRAMEWORKS[framework]
    style_key = framework_spec["default_style"] if visual_style == "auto" else visual_style
    style_spec = STYLES[style_key]
    domain = detect_visual_domain(" ".join([topic, *keywords]))
    ratio = aspect_ratio if aspect_ratio in SUPPORTED_ASPECT_RATIOS else platform_spec["aspect_ratio"]

    is_arabic = language == "ar"
    overlay_side = "right" if is_arabic else "left"
    palette_text = ", ".join(f"{name} ({hex_code})" for name, hex_code in tone_spec["palette"])

    sentences = [
        style_spec["directive"],
        f'It is the visual for a social media post on {platform_spec["label"]} about: "{topic}".',
    ]
    if keywords:
        sentences.append(f"Themes to reflect: {', '.join(keywords)}.")
    if hook:
        sentences.append(f'It accompanies the headline "{hook}"; express that message visually, not literally.')
    sentences.append(framework_spec["composition"])
    if domain in DOMAIN_CUES:
        sentences.append(DOMAIN_CUES[domain])
    sentences.append(
        f"Mood: {tone_spec['mood']}. Lighting: {tone_spec['lighting']}. Color palette: {palette_text}."
    )
    sentences.append(platform_spec["aesthetic"])
    if is_arabic:
        sentences.append("If people appear, depict them as Arab / Middle Eastern with culturally "
                         "appropriate, modest styling.")
    sentences.append(f"Keep the {overlay_side} third of the frame as clean, uncluttered negative space "
                     "for a headline overlay.")
    sentences.append(NO_TEXT_RULE)

    fonts = "Cairo or Tajawal" if is_arabic else "Inter or Montserrat"
    text_overlay = (
        f"Place the headline in the {overlay_side} third, {overlay_side}-aligned, in a bold sans-serif "
        f"({fonts}). Use {tone_spec['palette'][0][1]} or {tone_spec['palette'][2][1]} for maximum contrast."
    )

    return ImagePlan(
        prompt=" ".join(sentences),
        platform=platform_spec["label"],
        aspect_ratio=ratio,
        dimensions=recommended_dimensions(ratio),
        visual_style=style_spec["label"],
        framework=framework,
        domain=domain,
        mood=tone_spec["mood"],
        lighting=tone_spec["lighting"],
        composition=framework_spec["composition"],
        text_overlay=text_overlay,
        platform_notes=platform_spec["aesthetic"],
        palette=[{"name": name, "hex": hex_code} for name, hex_code in tone_spec["palette"]],
    )
