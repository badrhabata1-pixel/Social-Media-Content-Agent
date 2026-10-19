"""Tests for Module 6 (post log, metrics sync, comparative report). In-memory SQLite, mocked Facebook."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from analytics import AnalyticsEngine, PostsDatabase, engagement_score
from app import app, get_facebook_service


def metrics(reactions=0, comments=0, shares=0, post_id="x"):
    return {"success": True, "post_id": post_id, "reactions": reactions, "comments": comments, "shares": shares}


def failure(message="boom", **details):
    return {"success": False, "error": {"category": "facebook", "message": message, **details}}


@pytest.fixture
def facebook():
    service = MagicMock()
    service.get_post_metrics.side_effect = lambda post_id: metrics(post_id=post_id)
    return service


@pytest.fixture
def engine(posts_db, facebook):
    return AnalyticsEngine(posts_db, facebook)


def seed(db):
    """Two tech posts, one productivity post, one general post."""
    db.insert_post("facebook", "1_1", topic="AI tools", domain="tech_ai", tone="Professional",
                   created_at="2026-10-19T10:00:00+00:00")
    db.insert_post("facebook", "1_2", topic="ai tools", domain="tech_ai", tone="Casual",
                   created_at="2026-10-19T11:00:00+00:00")
    db.insert_post("facebook", "1_3", topic="Time blocking", domain="productivity_time", tone="Casual",
                   created_at="2026-10-19T12:00:00+00:00")
    db.insert_post("facebook", "1_4", topic="Pasta night", domain="general", tone="Inspirational",
                   created_at="2026-10-19T13:00:00+00:00")
    db.update_metrics("1_1", reactions=10, comments=2, shares=1)   # score 17
    db.update_metrics("1_2", reactions=4, comments=0, shares=0)    # score 4   -> tech total 21, avg 10.5
    db.update_metrics("1_3", reactions=5, comments=4, shares=2)    # score 19  -> productivity avg 19
    db.update_metrics("1_4", reactions=1, comments=0, shares=0)    # score 1


# ── Database ────────────────────────────────────────────────────────────────

def test_insert_and_read_back(posts_db):
    row_id = posts_db.insert_post("facebook", "123_456", topic="AI", domain="tech_ai", tone="Casual")
    posts = posts_db.get_all_posts()
    assert len(posts) == 1 and posts[0]["id"] == row_id
    post = posts[0]
    assert (post["platform"], post["platform_post_id"], post["topic"], post["domain"], post["tone"]) == \
        ("facebook", "123_456", "AI", "tech_ai", "Casual")
    assert (post["reactions"], post["comments"], post["shares"]) == (0, 0, 0)
    assert post["created_at"] and post["metrics_synced_at"] is None


def test_init_db_is_idempotent_and_keeps_data(posts_db):
    posts_db.insert_post("facebook", "1_1")
    posts_db.init_db()
    assert len(posts_db.get_all_posts()) == 1


def test_duplicate_post_id_is_not_logged_twice(posts_db):
    first = posts_db.insert_post("facebook", "1_1", topic="A")
    again = posts_db.insert_post("facebook", "1_1", topic="B")
    assert first == again and len(posts_db.get_all_posts()) == 1
    assert posts_db.get_all_posts()[0]["topic"] == "A"


def test_update_metrics(posts_db):
    posts_db.insert_post("facebook", "1_1")
    assert posts_db.update_metrics("1_1", reactions=7, comments=3, shares=1, synced_at="2026-10-19T20:00:00+00:00")
    post = posts_db.get_all_posts()[0]
    assert (post["reactions"], post["comments"], post["shares"]) == (7, 3, 1)
    assert post["metrics_synced_at"] == "2026-10-19T20:00:00+00:00"


def test_update_metrics_for_unknown_post(posts_db):
    assert posts_db.update_metrics("missing", 1, 1, 1) is False


def test_posts_are_newest_first_and_filterable(posts_db):
    posts_db.insert_post("facebook", "old", created_at="2026-01-01T00:00:00+00:00")
    posts_db.insert_post("instagram", "ig", created_at="2026-06-01T00:00:00+00:00")
    posts_db.insert_post("facebook", "new", created_at="2026-10-01T00:00:00+00:00")
    assert [p["platform_post_id"] for p in posts_db.get_all_posts()] == ["new", "ig", "old"]
    assert [p["platform_post_id"] for p in posts_db.get_all_posts(platform="facebook")] == ["new", "old"]


def test_file_database_persists_between_connections(tmp_path):
    path = str(tmp_path / "analytics.db")
    first = PostsDatabase(path)
    first.init_db()
    first.insert_post("facebook", "1_1")
    first.close()
    second = PostsDatabase(path)
    second.init_db()
    assert [p["platform_post_id"] for p in second.get_all_posts()] == ["1_1"]
    second.close()


# ── Engagement score & report ───────────────────────────────────────────────

def test_engagement_score_formula():
    assert engagement_score(reactions=10, comments=2, shares=1) == 10 + 4 + 3


def test_report_on_empty_database(engine):
    report = engine.generate_comparative_report()
    assert report["total_posts"] == 0 and report["total_engagement"] == 0
    assert report["top_domain"] is None
    assert report["by_domain"] == report["by_topic"] == report["by_tone"] == report["top_posts"] == []
    assert report["last_synced_at"] is None


def test_report_structure_and_totals(engine, posts_db):
    seed(posts_db)
    report = engine.generate_comparative_report()

    assert {"total_posts", "total_engagement", "average_engagement", "totals", "top_domain", "by_domain",
            "by_topic", "by_tone", "top_posts", "last_synced_at", "scoring", "generated_at"} <= set(report)
    assert report["total_posts"] == 4
    assert report["total_engagement"] == 17 + 4 + 19 + 1
    assert report["average_engagement"] == 10.25
    assert report["totals"] == {"reactions": 20, "comments": 6, "shares": 3}
    assert report["last_synced_at"] is not None


def test_report_groups_by_domain(engine, posts_db):
    seed(posts_db)
    by_domain = {row["name"]: row for row in engine.generate_comparative_report()["by_domain"]}
    assert by_domain["tech_ai"] == {"name": "tech_ai", "posts": 2, "reactions": 14, "comments": 2, "shares": 1,
                                    "engagement_score": 21, "average_engagement": 10.5}
    assert by_domain["productivity_time"]["engagement_score"] == 19


def test_report_lists_are_sorted_for_charting(engine, posts_db):
    seed(posts_db)
    report = engine.generate_comparative_report()
    for key in ("by_domain", "by_topic", "by_tone"):
        scores = [row["engagement_score"] for row in report[key]]
        assert scores == sorted(scores, reverse=True), key
    assert [p["platform_post_id"] for p in report["top_posts"]] == ["1_3", "1_1", "1_2", "1_4"]


def test_topics_group_case_insensitively(engine, posts_db):
    seed(posts_db)
    topics = {row["name"].lower(): row for row in engine.generate_comparative_report()["by_topic"]}
    assert topics["ai tools"]["posts"] == 2 and topics["ai tools"]["engagement_score"] == 21


def test_report_groups_by_tone(engine, posts_db):
    seed(posts_db)
    tones = {row["name"]: row["engagement_score"] for row in engine.generate_comparative_report()["by_tone"]}
    assert tones == {"Casual": 23, "Professional": 17, "Inspirational": 1}


def test_top_domain_uses_average_per_post(engine, posts_db):
    # tech_ai has the most total engagement (21 over 2 posts), productivity_time the best average (19).
    seed(posts_db)
    top = engine.generate_comparative_report()["top_domain"]
    assert top["name"] == "productivity_time" and top["average_engagement"] == 19


def test_no_top_domain_before_any_engagement(engine, posts_db):
    posts_db.insert_post("facebook", "1_1", domain="tech_ai")
    assert engine.generate_comparative_report()["top_domain"] is None


# ── Metrics sync ────────────────────────────────────────────────────────────

def test_sync_updates_every_facebook_post(engine, posts_db, facebook):
    posts_db.insert_post("facebook", "1_1")
    posts_db.insert_post("facebook", "1_2")
    posts_db.insert_post("instagram", "ig_1")
    facebook.get_post_metrics.side_effect = lambda post_id: {
        "1_1": metrics(3, 1, 0), "1_2": metrics(8, 2, 5)}[post_id]

    summary = engine.sync_all_metrics()

    assert summary["success"] is True
    assert (summary["total"], summary["synced"], summary["failed"]) == (2, 2, 0)
    assert summary["synced_at"]
    assert sorted(call.args[0] for call in facebook.get_post_metrics.call_args_list) == ["1_1", "1_2"]
    stored = {p["platform_post_id"]: (p["reactions"], p["comments"], p["shares"]) for p in posts_db.get_all_posts()}
    assert stored == {"1_1": (3, 1, 0), "1_2": (8, 2, 5), "ig_1": (0, 0, 0)}


def test_sync_continues_past_a_single_post_failure(engine, posts_db, facebook):
    posts_db.insert_post("facebook", "deleted")
    posts_db.insert_post("facebook", "ok")
    facebook.get_post_metrics.side_effect = lambda post_id: (
        failure("Unsupported get request", code=100) if post_id == "deleted" else metrics(4))

    summary = engine.sync_all_metrics()

    assert summary["success"] is True and (summary["synced"], summary["failed"]) == (1, 1)
    assert summary["errors"][0]["platform_post_id"] == "deleted"


@pytest.mark.parametrize("error", [
    {"category": "facebook", "message": "Session has expired", "code": 190},
    {"category": "facebook", "message": "Permission denied", "code": 10},
    {"category": "config", "message": "Not configured"},
])
def test_sync_stops_on_errors_that_affect_every_post(engine, posts_db, facebook, error):
    for post_id in ("1_1", "1_2", "1_3"):
        posts_db.insert_post("facebook", post_id)
    facebook.get_post_metrics.side_effect = lambda post_id: {"success": False, "error": error}

    summary = engine.sync_all_metrics()

    assert summary["success"] is False and summary["error"] == error
    assert facebook.get_post_metrics.call_count == 1 and summary["failed"] == 3


def test_sync_with_no_posts(engine, facebook):
    summary = engine.sync_all_metrics()
    assert summary["success"] is True and summary["total"] == 0 and summary["synced_at"] is None
    facebook.get_post_metrics.assert_not_called()


# ── HTTP API ────────────────────────────────────────────────────────────────

@pytest.fixture
def client(facebook):
    app.dependency_overrides[get_facebook_service] = lambda: facebook
    yield TestClient(app)
    app.dependency_overrides.pop(get_facebook_service, None)


def test_publishing_logs_the_post(client, facebook, posts_db):
    facebook.publish_text_post.return_value = {"success": True, "post_id": "123_456",
                                               "url": "https://facebook.com/123_456"}
    response = client.post("/publish/facebook", json={
        "message": "Hello", "topic": "AI tools for teams", "domain": "tech_ai", "tone": "Casual"})

    assert response.status_code == 200
    [post] = posts_db.get_all_posts()
    assert (post["platform"], post["platform_post_id"], post["topic"], post["domain"], post["tone"]) == \
        ("facebook", "123_456", "AI tools for teams", "tech_ai", "Casual")


def test_publishing_without_context_infers_it(client, facebook, posts_db):
    facebook.publish_text_post.return_value = {"success": True, "post_id": "9_9", "url": "u"}
    client.post("/publish/facebook", json={"message": "Exam preparation guide\nMore text here"})
    [post] = posts_db.get_all_posts()
    assert (post["topic"], post["domain"], post["tone"]) == ("Exam preparation guide", "education_study", "Unknown")


def test_failed_publish_is_not_logged(client, facebook, posts_db):
    facebook.publish_text_post.return_value = failure(http_status=400, code=190)
    assert client.post("/publish/facebook", json={"message": "Hello"}).status_code == 400
    assert posts_db.get_all_posts() == []


def test_database_failure_does_not_fail_a_live_publish(client, facebook, posts_db):
    facebook.publish_text_post.return_value = {"success": True, "post_id": "1_1", "url": "u"}
    posts_db.close()  # every write now raises sqlite3.ProgrammingError
    response = client.post("/publish/facebook", json={"message": "Hello"})
    assert response.status_code == 200 and response.json()["data"]["post_id"] == "1_1"


@pytest.mark.parametrize("field, value", [("domain", "cooking"), ("tone", "Angry")])
def test_publish_rejects_unknown_context_values(client, field, value):
    assert client.post("/publish/facebook", json={"message": "Hi", field: value}).status_code == 422


def test_sync_endpoint(client, facebook, posts_db):
    posts_db.insert_post("facebook", "1_1")
    facebook.get_post_metrics.side_effect = lambda post_id: metrics(2, 1, 1)

    response = client.post("/analytics/sync")

    assert response.status_code == 200
    assert response.json()["data"]["synced"] == 1
    assert posts_db.get_all_posts()[0]["reactions"] == 2


@pytest.mark.parametrize("error, status", [
    ({"category": "config", "message": "Not configured"}, 503),
    ({"category": "facebook", "message": "expired", "code": 190, "http_status": 400}, 400),
])
def test_sync_endpoint_reports_blocking_errors(client, facebook, posts_db, error, status):
    posts_db.insert_post("facebook", "1_1")
    facebook.get_post_metrics.side_effect = lambda post_id: {"success": False, "error": error}
    response = client.post("/analytics/sync")
    assert response.status_code == status and response.json()["status"] == "error"


def test_report_endpoint(client, posts_db):
    seed(posts_db)
    response = client.get("/analytics/report")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_posts"] == 4 and data["top_domain"]["name"] == "productivity_time"
    assert [row["name"] for row in data["by_domain"]][0] == "tech_ai"


def test_report_endpoint_when_empty(client):
    data = client.get("/analytics/report").json()["data"]
    assert data["total_posts"] == 0 and data["top_domain"] is None
