"""Tests for Module 3 (Content Writer Agent) and the /generate endpoint."""

import re
from itertools import combinations, product

import pytest
from fastapi.testclient import TestClient

from agent import COPY_BANK, TWITTER_LIMIT, ContentWriterAgent, content_agent
from app import app

PLATFORMS = ["LinkedIn", "Instagram", "Twitter", "Facebook"]
GOALS = ["Marketing", "Educational", "Engagement"]
TONES = ["Professional", "Inspirational", "Casual"]
LANGUAGES = ["en", "ar"]

VALID = {
    "topic": "Time management mobile application for college students",
    "keywords": ["tasks", "productivity", "study routine"],
    "platform": "LinkedIn",
    "goal": "Marketing",
    "tone": "Professional",
    "language": "en",
}


@pytest.fixture
def client():
    return TestClient(app)


# ── /generate: happy path & contract ────────────────────────────────────────

def test_generate_returns_two_variations(client):
    response = client.post("/generate", json=VALID)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    meta = body["data"]["agent_metadata"]
    assert (meta["platform"], meta["framework"], meta["language"]) == ("LinkedIn", "AIDA", "en")
    variations = body["data"]["variations"]
    assert [v["type"] for v in variations] == ["Action-driven", "Value-driven"]
    for v in variations:
        assert {"hook", "body", "call_to_action", "full_caption", "hashtags"} <= set(v)
        assert v["hook"] and v["full_caption"]


def test_only_topic_uses_defaults(client):
    response = client.post("/generate", json={"topic": "Study tips"})
    assert response.status_code == 200
    meta = response.json()["data"]["agent_metadata"]
    assert (meta["platform"], meta["tone"], meta["language"]) == ("LinkedIn", "Professional", "en")


def test_topic_is_stripped(client):
    response = client.post("/generate", json={**VALID, "topic": "   Study tips   "})
    assert response.status_code == 200
    assert "Study tips" in response.json()["data"]["variations"][0]["hook"]
    assert "  Study" not in response.json()["data"]["variations"][0]["hook"]


# ── keywords: null / blanks ─────────────────────────────────────────────────

def test_null_keywords_does_not_crash(client):
    response = client.post("/generate", json={**VALID, "keywords": None})
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_blank_keywords_are_dropped(client):
    response = client.post("/generate", json={**VALID, "keywords": ["", "   ", "focus"], "platform": "Instagram"})
    assert response.status_code == 200
    hashtags = response.json()["data"]["variations"][0]["hashtags"]
    assert "#focus" in hashtags
    assert all(len(tag) > 1 for tag in hashtags)


# ── Validation: clean 422s ──────────────────────────────────────────────────

@pytest.mark.parametrize("topic", ["", "   ", "\n\t"])
def test_empty_topic_is_rejected(client, topic):
    response = client.post("/generate", json={**VALID, "topic": topic})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "topic"]


def test_missing_or_too_long_topic_is_rejected(client):
    assert client.post("/generate", json={"keywords": ["x"]}).status_code == 422
    assert client.post("/generate", json={**VALID, "topic": "x" * 501}).status_code == 422
    assert client.post("/generate", json={**VALID, "topic": "x" * 500}).status_code == 200


@pytest.mark.parametrize("field, value", [
    ("platform", "TikTok"),
    ("platform", "linkedin"),
    ("goal", "Sales"),
    ("tone", "Angry"),
    ("language", "fr"),
])
def test_invalid_choice_is_rejected(client, field, value):
    response = client.post("/generate", json={**VALID, field: value})
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]


@pytest.mark.parametrize("field, value", [
    ("platform", "Twitter"), ("platform", "Instagram"), ("platform", "Facebook"),
    ("goal", "Educational"), ("goal", "Engagement"),
    ("tone", "Inspirational"), ("tone", "Casual"),
    ("language", "ar"),
])
def test_every_ui_choice_is_accepted(client, field, value):
    assert client.post("/generate", json={**VALID, field: value}).status_code == 200


def test_openapi_schema_keeps_examples(client):
    props = client.get("/openapi.json").json()["components"]["schemas"]["DirectiveRequest"]["properties"]
    assert props["topic"]["example"] == VALID["topic"]
    assert props["platform"]["enum"] == ["LinkedIn", "Instagram", "Twitter", "Facebook"]


# ── Direct calls (Main Coordinator path, no HTTP validation) ────────────────

@pytest.mark.parametrize("directive", [
    {"topic": "Study tips", "keywords": None},
    {"topic": None},
    {"topic": "Study tips", "platform": None, "goal": None, "tone": None, "language": None},
])
def test_direct_call_tolerates_none_values(directive):
    output = content_agent.generate(directive)
    assert len(output["variations"]) == 2


def test_direct_call_accepts_comma_separated_keywords():
    body = content_agent.generate({"topic": "Habits", "keywords": "focus, , routine"})["variations"][0]["body"]
    assert "focus and routine" in body


# ── Domain detection: word boundaries ───────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Oil painting tutorial",
    "Daily email campaign tips",
    "Training for a marathon",
    "How to maintain a garden",
    "Healthy breakfast for a happy family",
    "Brain teasers for kids",
])
def test_ai_inside_other_words_is_not_tech(text):
    assert ContentWriterAgent().detect_domain(text) != "tech_ai"


@pytest.mark.parametrize("text, domain", [
    ("AI tools for students", "tech_ai"),
    ("Building a mobile app", "tech_ai"),
    ("Boost your productivity", "productivity_time"),
    ("Exam preparation guide", "education_study"),
    ("Startup sales strategy", "business_career"),
    ("مذاكرة الامتحانات", "education_study"),
    ("الذكاء الاصطناعي في التعليم", "tech_ai"),
])
def test_real_keywords_are_still_detected(text, domain):
    assert ContentWriterAgent().detect_domain(text) == domain


def test_metadata_domain_matches_hashtag_domain(client):
    response = client.post("/generate", json={
        **VALID, "topic": "Weekly planner", "keywords": ["exam", "study"], "platform": "Instagram",
    })
    data = response.json()["data"]
    assert data["agent_metadata"]["detected_domain"] == "education_study"
    assert "#StudentLife" in data["variations"][0]["hashtags"]


def test_no_tech_hashtags_for_unrelated_topic():
    output = content_agent.generate({"topic": "Healthy breakfast for a happy family", "platform": "Instagram"})
    assert output["agent_metadata"]["detected_domain"] != "tech_ai"
    assert "#ArtificialIntelligence" not in output["variations"][0]["hashtags"]


# ── Phase 2: varied output ("Regenerate") ───────────────────────────────────

def test_regenerate_gives_fresh_copy():
    captions = {content_agent.generate(VALID)["variations"][0]["full_caption"] for _ in range(10)}
    assert len(captions) >= 3


def test_api_regenerate_gives_fresh_copy(client):
    captions = {
        client.post("/generate", json=VALID).json()["data"]["variations"][1]["full_caption"] for _ in range(10)
    }
    assert len(captions) >= 3


def test_same_seed_is_reproducible():
    assert ContentWriterAgent(seed=7).generate(VALID) == ContentWriterAgent(seed=7).generate(VALID)


def test_both_variations_differ_in_one_response():
    for _ in range(10):
        first, second = content_agent.generate(VALID)["variations"]
        assert first["hook"] != second["hook"] and first["body"] != second["body"]


def test_both_variations_use_different_key_sentences():
    for _ in range(20):
        first, second = content_agent.generate({"topic": "AI", "platform": "Twitter"})["variations"]
        assert first["full_caption"].split("\n\n")[1] != second["full_caption"].split("\n\n")[1]


# ── Phase 2: X/Twitter limit ────────────────────────────────────────────────

LONG_TOPIC = (
    "A complete practical guide to building calm and focused study routines for busy "
    "university students who also work part time and want better grades "
) * 4


@pytest.mark.parametrize("topic, keywords", [
    ("AI", []),
    (VALID["topic"], VALID["keywords"]),
    (LONG_TOPIC, ["deep focus", "study planning", "weekly review"]),
    ("Tips", ["a" * 150, "b" * 150]),
    ("A" + "x" * 600, []),
])
@pytest.mark.parametrize("language", LANGUAGES)
def test_twitter_never_exceeds_limit(topic, keywords, language):
    for goal, tone in product(GOALS, TONES):
        for _ in range(3):
            output = content_agent.generate({"topic": topic, "keywords": keywords, "platform": "Twitter",
                                             "goal": goal, "tone": tone, "language": language})
            for v in output["variations"]:
                assert len(v["full_caption"]) <= TWITTER_LIMIT
                assert len(v["hashtags"]) <= 3
                assert all(tag in v["full_caption"].split() for tag in v["hashtags"])


def test_twitter_truncates_at_word_boundary():
    for _ in range(10):
        v = content_agent.generate({"topic": LONG_TOPIC, "platform": "Twitter"})["variations"][0]
        first_line = v["full_caption"].split("\n\n")[0]
        assert first_line.endswith("...")
        kept = first_line[:-3]
        assert v["hook"].startswith(kept)
        assert v["hook"][len(kept)] in " ,.;:!?،؛-—"  # the cut fell between words
        assert v["hashtags"], "the primary hashtag is kept"


def test_twitter_keeps_full_post_when_it_fits():
    v = content_agent.generate({"topic": "AI", "platform": "Twitter"})["variations"][0]
    assert v["hook"] in v["full_caption"] and v["call_to_action"] in v["full_caption"]
    assert "..." not in v["full_caption"]


@pytest.mark.parametrize("language", LANGUAGES)
def test_twitter_follows_the_hook_with_a_complete_idea(language):
    # X/Twitter skips the body, so a hook ending in ":" must not be left hanging.
    insights = COPY_BANK[language]["domains"]["tech_ai"]["insight"]
    for goal in GOALS:
        for _ in range(5):
            for v in content_agent.generate({"topic": "AI", "platform": "Twitter", "goal": goal,
                                             "language": language})["variations"]:
                assert any(insight in v["full_caption"] for insight in insights), v["full_caption"]


def test_braces_in_user_text_are_kept_literally():
    for platform in PLATFORMS:
        output = content_agent.generate({"topic": "Using {topic} and {kw} in templates",
                                         "keywords": ["{challenge}"], "platform": platform})
        assert "{topic} and {kw}" in output["variations"][0]["full_caption"]


def test_keywords_are_joined_naturally():
    join = ContentWriterAgent._join_keywords
    assert join(["المهام", "المذاكرة"], "ar") == "المهام والمذاكرة"
    assert join(["المهام", "المذاكرة", "التركيز"], "ar") == "المهام، والمذاكرة، والتركيز"
    assert join(["tasks", "focus"], "en") == "tasks and focus"
    assert join(["tasks", "focus", "habits"], "en") == "tasks, focus, and habits"
    assert join([], "en") == ""


# ── Phase 2: domain detection ("app" prefix) ────────────────────────────────

@pytest.mark.parametrize("text", ["Apple pie recipe", "A new philosophical approach", "Applied art for kids"])
def test_app_prefix_words_are_not_tech(text):
    assert ContentWriterAgent().detect_domain(text) != "tech_ai"


@pytest.mark.parametrize("text", [
    "Mobile application for students", "Best apps for students", "Launching our new app",
    VALID["topic"], "تطبيقات الهاتف للطلاب", "تطبيق جديد لتنظيم الوقت",
])
def test_applications_are_tech(text):
    assert ContentWriterAgent().detect_domain(text) == "tech_ai"


def test_unmatched_topic_is_general():
    assert ContentWriterAgent().detect_domain("Cooking Italian pasta") == "general"


# ── Phase 2: tone shapes every framework ────────────────────────────────────

@pytest.mark.parametrize("goal", GOALS)
@pytest.mark.parametrize("language", LANGUAGES)
def test_tone_changes_the_copy_in_every_framework(goal, language):
    agent = ContentWriterAgent(seed=3)
    seen = {}
    for tone in TONES:
        hooks, bodies = set(), set()
        for _ in range(15):
            for v in agent.generate({**VALID, "goal": goal, "tone": tone, "language": language})["variations"]:
                hooks.add(v["hook"])
                bodies.add(v["body"])
        seen[tone] = (hooks, bodies)
    for a, b in combinations(TONES, 2):
        assert seen[a][0].isdisjoint(seen[b][0]), f"{a} and {b} share a hook"
        assert seen[a][1].isdisjoint(seen[b][1]), f"{a} and {b} share a body"


def test_legacy_tone_maps_to_supported_tone(client):
    meta = client.post("/generate-legacy", json={"topic": "AI", "platform": "Facebook", "tone": "funny"}).json()
    assert meta["data"]["agent_metadata"]["tone"] == "Casual"


# ── Phase 2: no fabricated claims, no productivity bias ─────────────────────

def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    else:
        for value in node:
            yield from _strings(value)


FABRICATION = re.compile(
    r"\d|[٠-٩]|%|٪|\blinks?\b|\bbio\b|رابط|proven|case study|\byears?\b|\bmonths?\b|guarantee|"
    r"أثبتت|مضمون|سنوات|شهور|أشهر|ضعف|تضاعف",
    re.IGNORECASE,
)


def test_copy_bank_has_no_fabricated_claims():
    offenders = [text for text in _strings(COPY_BANK) if FABRICATION.search(text)]
    assert offenders == []


def test_generated_posts_have_no_numbers_or_links():
    for platform, goal, tone, language in product(PLATFORMS, GOALS, TONES, LANGUAGES):
        output = content_agent.generate({"topic": "Topic", "keywords": ["idea"], "platform": platform,
                                         "goal": goal, "tone": tone, "language": language})
        for v in output["variations"]:
            assert not FABRICATION.search(v["full_caption"]), v["full_caption"]


def test_each_language_bank_stays_in_its_script():
    def text_of(template):
        return re.sub(r"\{\w+\}", "", template)  # placeholder names are not copy

    assert not [t for t in _strings(COPY_BANK["ar"]) if re.search(r"[A-Za-z]", text_of(t))]
    assert not [t for t in _strings(COPY_BANK["en"]) if re.search(r"[؀-ۿ]", text_of(t))]


@pytest.mark.parametrize("topic", ["Cooking Italian pasta", "Traveling to Japan", "Yoga for beginners"])
def test_general_topics_get_no_productivity_jargon(topic):
    jargon = ("productiv", "deep work", "to-do", "timemanagement", "focusmode", "matrix", "workflow")
    for goal in GOALS:
        for _ in range(5):
            output = content_agent.generate({"topic": topic, "platform": "Instagram", "goal": goal})
            assert output["agent_metadata"]["detected_domain"] == "general"
            for v in output["variations"]:
                text = v["full_caption"].lower()
                assert not any(word in text for word in jargon), text


@pytest.mark.parametrize("topic, domain", [
    ("AI tools for small teams", "tech_ai"),
    ("Boost your productivity", "productivity_time"),
    ("Exam preparation guide", "education_study"),
    ("Startup sales strategy", "business_career"),
    ("Cooking Italian pasta", "general"),
])
@pytest.mark.parametrize("language", LANGUAGES)
def test_body_uses_the_domain_vocabulary(topic, domain, language):
    phrases = [phrase for group in COPY_BANK[language]["domains"][domain].values() for phrase in group]
    for goal in GOALS:
        for _ in range(5):
            output = content_agent.generate({"topic": topic, "goal": goal, "language": language})
            assert output["agent_metadata"]["detected_domain"] == domain
            for v in output["variations"]:
                assert any(phrase in v["body"] for phrase in phrases), v["body"]


# ── Phase 2: formatting details ─────────────────────────────────────────────

def test_instagram_has_no_double_sparkle_or_double_save_prompt():
    for tone in TONES:
        for _ in range(15):
            for v in content_agent.generate({**VALID, "platform": "Instagram", "tone": tone})["variations"]:
                assert "✨ ✨" not in v["full_caption"]
                assert len(re.findall(r"\bsave\b", v["full_caption"], re.IGNORECASE)) <= 1


def test_hashtags_are_deduplicated_ignoring_case():
    tags = content_agent.generate({"topic": "Meal prep", "keywords": ["Meal Prep", "meal prep"],
                                   "platform": "Instagram"})["variations"][0]["hashtags"]
    assert len({t.lower() for t in tags}) == len(tags)


def test_general_topics_get_neutral_hashtags():
    tags = content_agent.generate({"topic": "Cooking Italian pasta", "platform": "Instagram"})["variations"][0]["hashtags"]
    assert "#Productivity" not in tags and "#ArtificialIntelligence" not in tags
    assert "#Lifestyle" in tags


# ── Phase 2: Arabic spelling normalization ──────────────────────────────────

@pytest.mark.parametrize("text", [
    "سوشيال ميديا للمشاريع", "روبوت ذكي", "حاجه مهمة في الشغل", "التعمل في الوقت", "ابلكيشن جديدة",
])
def test_valid_arabic_words_are_left_alone(text):
    assert ContentWriterAgent().normalize_and_clean_text(text, "ar") == text


@pytest.mark.parametrize("raw, fixed", [
    ("مذاكره الامتحانات", "مذاكرة الامتحانات"),
    ("زكاء اصطناعي", "ذكاء اصطناعي"),
    ("انتاجيه عالية", "إنتاجية عالية"),
    ("وظايف جديدة", "وظائف جديدة"),
])
def test_real_arabic_misspellings_are_fixed(raw, fixed):
    assert ContentWriterAgent().normalize_and_clean_text(raw, "ar") == fixed


def test_typo_map_only_fixes_spelling():
    for wrong, right in ContentWriterAgent.TYPO_MAP_AR.items():
        assert wrong != right
        assert " " not in right or right == "لينكد إن"  # no phrase rewrites, except the brand name
