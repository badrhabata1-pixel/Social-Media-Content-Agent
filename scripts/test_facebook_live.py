"""Live check against the real Meta Graph API.

Checks the token (type, Page, permissions, expiry), then publishes ONE public test post to
the Facebook Page in .env and reads its metrics. Nothing is posted if the token check fails.
Run from the project root:

    python scripts/test_facebook_live.py

Not collected by pytest (tests live in tests/), and nothing runs on import.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from social_integrations import FacebookService  # noqa: E402

TEST_MESSAGE = ("🤖 Test post from Intelligent Social Media Content Agent! "
                "System is officially connected to Meta Graph API.")


def show(title: str, data: dict) -> None:
    print(f"\n== {title}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # emoji on Windows consoles
    service = FacebookService()
    print(f"Page ID: {service.page_id}")
    if not service.configured:
        print("FACEBOOK_PAGE_ID / FACEBOOK_PAGE_ACCESS_TOKEN are missing from .env.")
        return 1

    # Check the token first, so a misconfiguration is explained instead of failing on a public post.
    token = service.inspect_token()
    show("Token check", token)
    if token["success"] and not token["ready_to_publish"]:
        print("\nNot publishing until these are fixed:")
        for problem in token["problems"]:
            print(f"  - {problem}")
        return 1

    published = service.publish_text_post(TEST_MESSAGE)
    show("Publish response", published)
    if not published["success"]:
        return 1
    print(f"\nPost ID: {published['post_id']}")
    print(f"URL:     {published['url']}")

    metrics = service.get_post_metrics(published["post_id"])
    show("Initial metrics", metrics)
    return 0 if metrics["success"] else 2


if __name__ == "__main__":
    sys.exit(main())
