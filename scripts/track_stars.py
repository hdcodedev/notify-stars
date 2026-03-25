#!/usr/bin/env python3
"""
GitHub Stars Tracker
Fetches current stargazers, diffs against stored state,
and POSTs new stargazers to the Kilo webhook for AI analysis + Discord notification.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

HTTP_TIMEOUT = 30  # seconds
PROFILE_ENRICH_DELAY = 0.5  # seconds between profile fetches to avoid rate limits

# --- Configuration ---
TRACKED_REPO = os.environ.get("TRACKED_REPO", "HDCharts/charts")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
DATA_FILE = os.environ.get("DATA_FILE", "data/stargazers.json")
KILO_WEBHOOK_URL = os.environ.get("KILO_WEBHOOK_URL", "")
GITHUB_API = "https://api.github.com"


def fetch_stargazers(repo: str) -> list[dict]:
    """
    Fetch all stargazers with timestamps.
    Uses the star+json accept header to get starred_at field.
    """
    url = f"{GITHUB_API}/repos/{repo}/stargazers?per_page=100"
    all_stargazers = []

    while url:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3.star+json")
        req.add_header("User-Agent", "notify-stars-bot")
        if GITHUB_TOKEN:
            req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")

        try:
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
                all_stargazers.extend(data)

                # Pagination via Link header
                link = resp.headers.get("Link", "")
                url = None
                for part in link.split(","):
                    if 'rel="next"' in part:
                        url = part.split(";")[0].strip().strip("<>")
        except urllib.error.HTTPError as e:
            print(f"GitHub API error fetching stargazers: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)

    return all_stargazers


def load_previous_state() -> dict:
    """Load previous stargazer state from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"last_checked": None, "total_stars": 0, "stargazers": []}


def save_state(stargazers: list[dict], total: int):
    """Persist current stargazer state to JSON file."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    stored = []
    for s in stargazers:
        stored.append({
            "username": s["user"]["login"],
            "starred_at": s["starred_at"],
            "profile_url": s["user"]["html_url"],
        })

    state = {
        "last_checked": datetime.now(timezone.utc).isoformat(),
        "total_stars": total,
        "stargazers": stored,
    }

    with open(DATA_FILE, "w") as f:
        json.dump(state, f, indent=2)


def find_new_stargazers(current: list[dict], previous_usernames: set[str]) -> list[dict]:
    """Return stargazers not in the previous set."""
    new = []
    for s in current:
        username = s["user"]["login"]
        if username not in previous_usernames:
            new.append({
                "username": username,
                "starred_at": s["starred_at"],
                "profile_url": s["user"]["html_url"],
                "avatar_url": s["user"]["avatar_url"],
            })
    return new


def fetch_github_profile(username: str) -> dict | None:
    """Fetch public GitHub profile data for a user."""
    url = f"{GITHUB_API}/users/{username}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "notify-stars-bot")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")

    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        return None


def enrich_stargazers(stargazers: list[dict]) -> list[dict]:
    """Enrich stargazer data with public profile info for AI analysis."""
    enriched = []
    for i, s in enumerate(stargazers):
        if i > 0:
            time.sleep(PROFILE_ENRICH_DELAY)  # Rate limit protection
        profile = fetch_github_profile(s["username"])
        entry = {**s}
        if profile:
            entry["name"] = profile.get("name")
            entry["bio"] = profile.get("bio")
            entry["company"] = profile.get("company")
            entry["location"] = profile.get("location")
            entry["public_repos"] = profile.get("public_repos", 0)
            entry["followers"] = profile.get("followers", 0)
            entry["following"] = profile.get("following", 0)
        enriched.append(entry)
    return enriched


def post_to_kilo_webhook(payload: dict):
    """POST the star report to Kilo webhook for AI analysis + Discord notification."""
    if not KILO_WEBHOOK_URL:
        print("WARNING: KILO_WEBHOOK_URL not set, skipping webhook POST.", file=sys.stderr)
        return

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        KILO_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            print(f"Kilo webhook response: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Kilo webhook error: {e.code} {body}", file=sys.stderr)
        # Don't fail the workflow — star tracking still succeeded


def main():
    test_mode = "--test" in sys.argv
    test_sample_size = 3  # Number of stargazers to use in test mode

    if test_mode:
        print("=== TEST MODE ===")
        print(f"Will pick last {test_sample_size} stargazers and force webhook.\n")

    print(f"Fetching stargazers for {TRACKED_REPO}...")
    current_stargazers = fetch_stargazers(TRACKED_REPO)
    current_total = len(current_stargazers)
    print(f"Current total stars: {current_total}")

    # Load previous state
    prev_state = load_previous_state()
    prev_usernames = {s["username"] for s in prev_state.get("stargazers", [])}
    prev_total = prev_state.get("total_stars", 0)

    if test_mode:
        # Pick the last N stargazers (most recent) as "new"
        new_stargazers = []
        for s in current_stargazers[-test_sample_size:]:
            new_stargazers.append({
                "username": s["user"]["login"],
                "starred_at": s["starred_at"],
                "profile_url": s["user"]["html_url"],
                "avatar_url": s["user"]["avatar_url"],
            })
        is_first_run = False
        print(f"Test mode: picked {len(new_stargazers)} recent stargazers.")
    else:
        # Find new stargazers
        new_stargazers = find_new_stargazers(current_stargazers, prev_usernames)
        is_first_run = prev_total == 0 and prev_state["last_checked"] is None

        if is_first_run:
            print(f"First run: recording {current_total} stargazers as baseline.")
            new_stargazers = []  # Don't notify on first run
        else:
            print(f"New stargazers since last check: {len(new_stargazers)}")
            lost = prev_total - current_total if prev_total > current_total else 0
            if lost > 0:
                print(f"Stars lost since last check: {lost}")

    # Save current state (skip in test mode to preserve baseline)
    if not test_mode:
        save_state(current_stargazers, current_total)

    new_count = len(new_stargazers)
    net_change = current_total - prev_total

    # Write GitHub Actions summary
    github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary:
        with open(github_summary, "a") as f:
            f.write("## Star Tracker Report\n")
            if test_mode:
                f.write("> **TEST MODE** — forced webhook with recent stargazers\n\n")
            f.write(f"- **Repo:** {TRACKED_REPO}\n")
            f.write(f"- **Total Stars:** {current_total}\n")
            f.write(f"- **New Stars:** {new_count}\n")
            f.write(f"- **Net Change:** {'+' if net_change >= 0 else ''}{net_change}\n")
            if new_stargazers:
                f.write("\n### New Stargazers\n")
                for s in new_stargazers:
                    f.write(f"- [{s['username']}]({s['profile_url']}) ({s['starred_at']})\n")

    # Post to Kilo webhook if there are new stargazers
    if new_stargazers and KILO_WEBHOOK_URL:
        print("Enriching stargazer profiles for AI analysis...")
        enriched = enrich_stargazers(new_stargazers)

        payload = {
            "event": "test_stargazers" if test_mode else "new_stargazers",
            "repo": TRACKED_REPO,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "new_count": new_count,
                "total_stars": current_total,
                "net_change": net_change,
            },
            "new_stargazers": enriched,
        }

        print("Posting to Kilo webhook...")
        post_to_kilo_webhook(payload)
    elif not new_stargazers:
        print("No new stargazers, skipping webhook.")
    elif not KILO_WEBHOOK_URL:
        print("KILO_WEBHOOK_URL not configured, skipping webhook.")

    print(f"\nDone. Total: {current_total}, New: {new_count}, Change: {net_change}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
