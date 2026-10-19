"""Monitor & analytics: refreshes post metrics from Facebook and compares what performs best.

This closes the agent's loop: content is generated, published, measured, and the comparison
(by domain, topic and tone) shows which choices earn the most engagement.
"""

from typing import Optional

from social_integrations.facebook_service import CONFIG, PERMISSION_ERROR_CODES, TOKEN_ERROR_CODES

from .db import PostsDatabase, utc_now

SCORING = "reactions + 2 × comments + 3 × shares"
TOP_POSTS = 5


def engagement_score(reactions: int, comments: int, shares: int) -> int:
    """Weighted engagement: a comment or share signals more interest than a reaction."""
    return reactions + comments * 2 + shares * 3


def _affects_every_post(error: dict) -> bool:
    """Missing config, a bad token or a missing permission will fail for every post alike."""
    return error.get("category") == CONFIG or error.get("code") in TOKEN_ERROR_CODES | PERMISSION_ERROR_CODES


class AnalyticsEngine:
    def __init__(self, db: PostsDatabase, facebook):
        self.db = db
        self.facebook = facebook

    # ── Monitor ──────────────────────────────────────────────────────────────
    def sync_all_metrics(self) -> dict:
        """Pulls live metrics for every logged Facebook post and stores them.

        Per-post failures (e.g. a deleted post) are listed and the sync continues. A failure that
        would repeat for every post stops the sync and is returned as ``error``.
        """
        posts = self.db.get_all_posts(platform="facebook")
        summary = {"success": True, "total": len(posts), "synced": 0, "failed": 0, "errors": []}
        synced_at = utc_now()
        for post in posts:
            post_id = post["platform_post_id"]
            result = self.facebook.get_post_metrics(post_id)
            if result["success"]:
                self.db.update_metrics(post_id, result["reactions"], result["comments"], result["shares"],
                                       synced_at=synced_at)
                summary["synced"] += 1
                continue

            error = result["error"]
            if _affects_every_post(error):
                summary.update(success=False, error=error, failed=len(posts) - summary["synced"])
                return summary
            summary["failed"] += 1
            summary["errors"].append({"platform_post_id": post_id, "message": error["message"],
                                      "hint": error.get("hint")})
        summary["synced_at"] = synced_at if summary["synced"] else None
        return summary

    # ── Analytics ────────────────────────────────────────────────────────────
    def generate_comparative_report(self) -> dict:
        posts = self.db.get_all_posts()
        for post in posts:
            post["engagement_score"] = engagement_score(post["reactions"], post["comments"], post["shares"])

        total_engagement = sum(post["engagement_score"] for post in posts)
        by_domain = _aggregate(posts, "domain")
        synced = [post["metrics_synced_at"] for post in posts if post["metrics_synced_at"]]
        return {
            "total_posts": len(posts),
            "total_engagement": total_engagement,
            "average_engagement": round(total_engagement / len(posts), 2) if posts else 0,
            "totals": {key: sum(post[key] for post in posts) for key in ("reactions", "comments", "shares")},
            "top_domain": _top(by_domain),
            "by_domain": by_domain,
            "by_topic": _aggregate(posts, "topic"),
            "by_tone": _aggregate(posts, "tone"),
            "top_posts": [
                {key: post[key] for key in ("platform", "platform_post_id", "topic", "domain", "tone",
                                            "reactions", "comments", "shares", "engagement_score", "created_at")}
                for post in sorted(posts, key=lambda p: p["engagement_score"], reverse=True)[:TOP_POSTS]
            ],
            "last_synced_at": max(synced) if synced else None,
            "scoring": SCORING,
            "ranking": "Top domain = highest average engagement per post",
            "generated_at": utc_now(),
        }


def _aggregate(posts: list[dict], field: str) -> list[dict]:
    """Totals per value of ``field`` (case-insensitive), best total engagement first."""
    groups: dict[str, dict] = {}
    for post in posts:
        name = (post[field] or "").strip() or "Unknown"
        group = groups.setdefault(name.lower(), {
            "name": name, "posts": 0, "reactions": 0, "comments": 0, "shares": 0, "engagement_score": 0,
        })
        group["posts"] += 1
        for key in ("reactions", "comments", "shares", "engagement_score"):
            group[key] += post[key]
    rows = list(groups.values())
    for row in rows:
        row["average_engagement"] = round(row["engagement_score"] / row["posts"], 2)
    return sorted(rows, key=lambda row: (-row["engagement_score"], row["name"].lower()))


def _top(rows: list[dict]) -> Optional[dict]:
    """Best average engagement (ties: more total engagement). None until something has engagement."""
    scored = [row for row in rows if row["engagement_score"] > 0]
    if not scored:
        return None
    return max(scored, key=lambda row: (row["average_engagement"], row["engagement_score"]))
