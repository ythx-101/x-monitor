---
name: x-monitor
description: >
  Monitor X/Twitter tweet replies and detect technical questions.
  Uses Camofox + Nitter to fetch reply threads without login.
  Identifies questions in replies for AI-assisted answer drafting.
---

# X Monitor

Monitor tweet replies and detect questions for AI-assisted answering.

## When to Use

- User says "monitor this tweet", "watch replies", "check comments"
- User shares a tweet link and wants to track responses
- User needs help answering technical questions in their tweet replies

## When NOT to Use

- Just fetching a single tweet's content → use x-tweet-fetcher
- Posting or replying on X → not supported (read-only)
- Searching X for topics → use x-research

## Usage

```bash
# Fetch all replies on a tweet
python3 scripts/monitor.py --url "https://x.com/user/status/123"

# Check for new replies since last check
python3 scripts/monitor.py --url "https://x.com/user/status/123" --watch

# Pretty output
python3 scripts/monitor.py --url "https://x.com/user/status/123" --pretty
```

## Requirements

- Camofox browser running on localhost:9377
- Working Nitter instance (default: nitter.net)

## Optional TweetClaw Input

If Camofox or Nitter is unavailable, or the user already has TweetClaw
installed in OpenClaw, collect X/Twitter context through TweetClaw first and
use this skill for question detection and answer drafting.

Setup:

```bash
openclaw plugins install npm:@xquik/tweetclaw
openclaw config set plugins.entries.tweetclaw.config.apiKey "$XQUIK_API_KEY"
# Or configure MPP signing instead of an API key:
openclaw config set plugins.entries.tweetclaw.config.tempoSigningKey "$MPP_SIGNING_KEY"
openclaw config set tools.alsoAllow '["explore", "tweetclaw"]'
```

Workflow:

1. Use TweetClaw to fetch the target tweet, recent replies, or relevant search
   context with narrow limits.
2. Review the fetched context before drafting a public answer.
3. Run x-monitor, or paste the reviewed TweetClaw context into OpenClaw, to
   draft answers for user approval.

Rules:

- Keep this skill read-only.
- Preserve source tweet URLs in any drafted answer context.
- If TweetClaw write-like actions are needed, wait for TweetClaw approval flow
  and explicit user confirmation.

## File Structure

```
x-monitor/
├── README.md
├── SKILL.md          (this file)
├── scripts/
│   └── monitor.py    (main script)
└── data/
    └── state.json    (tracks last check per tweet)
```
