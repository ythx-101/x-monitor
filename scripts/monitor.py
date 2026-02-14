#!/usr/bin/env python3
"""
X Monitor - Monitor tweet replies via Camofox + Nitter.
No login required. Read-only.
"""

import json
import re
import sys
import os
import argparse
import urllib.request
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path


STATE_FILE = Path(__file__).parent.parent / "data" / "state.json"


def parse_tweet_url(url: str) -> tuple:
    """Extract username and tweet_id from X/Twitter URL."""
    match = re.search(r'(?:x\.com|twitter\.com)/(\w+)/status/(\d+)', url)
    if match:
        return match.group(1), match.group(2)
    raise ValueError(f"Cannot parse tweet URL: {url}")


def load_state() -> Dict:
    """Load previous check state."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: Dict):
    """Save check state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_replies_via_camofox(
    username: str,
    tweet_id: str,
    camofox_port: int = 9377,
    nitter_instance: str = "nitter.net",
) -> Optional[List[Dict]]:
    """Fetch reply thread using Camofox + Nitter."""
    nitter_url = f"https://{nitter_instance}/{username}/status/{tweet_id}"

    try:
        # Create tab
        create_data = json.dumps({
            "userId": "x-monitor",
            "sessionKey": f"monitor-{tweet_id}",
            "url": nitter_url,
        }).encode()

        req = urllib.request.Request(
            f"http://localhost:{camofox_port}/tabs",
            data=create_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            tab_data = json.loads(resp.read().decode())

        tab_id = tab_data.get("tabId")
        if not tab_id:
            print("[Camofox] No tabId returned", file=sys.stderr)
            return None

        # Wait for page to render
        time.sleep(8)

        # Get snapshot
        snap_url = f"http://localhost:{camofox_port}/tabs/{tab_id}/snapshot?userId=x-monitor"
        req = urllib.request.Request(snap_url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            snap_data = json.loads(resp.read().decode())

        snapshot = snap_data.get("snapshot", "")

        # Close tab
        try:
            close_req = urllib.request.Request(
                f"http://localhost:{camofox_port}/tabs/{tab_id}",
                method="DELETE",
            )
            urllib.request.urlopen(close_req, timeout=5)
        except Exception:
            pass

        # Parse replies from snapshot
        replies = parse_replies(snapshot, username)
        return replies

    except Exception as e:
        print(f"[Camofox] Error: {e}", file=sys.stderr)
        return None


def parse_replies(snapshot: str, original_author: str) -> List[Dict]:
    """Parse reply data from Camofox snapshot."""
    replies = []
    lines = snapshot.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for reply pattern: "Replying to @username"
        if "Replying to" in line:
            # The reply author should be a few lines above
            author = None
            text = None
            likes = 0

            # Search backwards for author
            for j in range(max(0, i - 10), i):
                author_match = re.search(r'@(\w+)', lines[j])
                if author_match and author_match.group(1) != original_author:
                    author = f"@{author_match.group(1)}"

            # Search forward for reply text
            for j in range(i + 1, min(len(lines), i + 10)):
                content = lines[j].strip()
                if content.startswith("- text:"):
                    text = content.replace("- text:", "").strip()
                    if text and "Replying to" not in text:
                        break
                    text = None

            # Search for engagement numbers
            for j in range(i + 1, min(len(lines), i + 15)):
                engagement = lines[j].strip()
                nums = re.findall(r'\d+', engagement)
                if len(nums) >= 3 and not engagement.startswith("- "):
                    # Pattern: replies likes views or similar
                    try:
                        likes = int(nums[0]) if len(nums) > 0 else 0
                    except (ValueError, IndexError):
                        pass
                    break

            if author and text:
                reply = {
                    "author": author,
                    "text": text,
                    "likes": likes,
                    "is_question": is_question(text),
                }
                # Avoid duplicates
                if not any(r["author"] == author and r["text"] == text for r in replies):
                    replies.append(reply)

        i += 1

    return replies


def is_question(text: str) -> bool:
    """Heuristic: detect if text is a question."""
    question_markers = [
        "?", "？", "怎么", "如何", "为什么", "为啥", "什么原因",
        "请教", "请问", "能不能", "可以吗", "是什么", "怎样",
        "how", "why", "what", "can you", "is there", "does",
    ]
    text_lower = text.lower()
    return any(marker in text_lower for marker in question_markers)


def monitor_tweet(
    url: str,
    watch: bool = False,
    camofox_port: int = 9377,
    nitter_instance: str = "nitter.net",
) -> Dict[str, Any]:
    """Monitor a tweet's replies."""
    username, tweet_id = parse_tweet_url(url)

    result = {
        "tweet_url": url,
        "username": username,
        "tweet_id": tweet_id,
        "checked_at": datetime.utcnow().isoformat(),
    }

    # Fetch replies
    replies = fetch_replies_via_camofox(
        username, tweet_id, camofox_port, nitter_instance
    )

    if replies is None:
        result["error"] = "Failed to fetch replies (is Camofox running?)"
        return result

    result["total_replies"] = len(replies)
    result["questions"] = [r for r in replies if r.get("is_question")]
    result["question_count"] = len(result["questions"])

    if watch:
        # Compare with previous state
        state = load_state()
        prev_key = f"tweet_{tweet_id}"
        prev_authors = set()
        if prev_key in state:
            prev_authors = set(
                f"{r['author']}:{r['text']}" for r in state[prev_key].get("replies", [])
            )

        new_replies = [
            r for r in replies
            if f"{r['author']}:{r['text']}" not in prev_authors
        ]
        result["new_replies"] = new_replies
        result["new_count"] = len(new_replies)

        # Save current state
        state[prev_key] = {
            "replies": replies,
            "last_checked": result["checked_at"],
        }
        save_state(state)
    else:
        result["replies"] = replies

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Monitor X/Twitter tweet replies via Camofox + Nitter"
    )
    parser.add_argument("--url", "-u", required=True, help="Tweet URL")
    parser.add_argument("--watch", "-w", action="store_true",
                        help="Watch mode: show only new replies since last check")
    parser.add_argument("--pretty", "-p", action="store_true", help="Pretty print JSON")
    parser.add_argument("--port", type=int, default=9377, help="Camofox port (default: 9377)")
    parser.add_argument("--nitter", default="nitter.net", help="Nitter instance (default: nitter.net)")

    args = parser.parse_args()
    result = monitor_tweet(
        args.url,
        watch=args.watch,
        camofox_port=args.port,
        nitter_instance=args.nitter,
    )

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
