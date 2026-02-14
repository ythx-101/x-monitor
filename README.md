# x-monitor

Monitor X/Twitter tweet replies and get AI-analyzed answers for technical questions.

An [OpenClaw](https://github.com/openclaw/openclaw) skill.

## What It Does

1. **Monitor replies** — Watch a tweet's comment section for new replies
2. **Detect questions** — Identify technical questions in replies
3. **Draft answers** — AI analyzes the question and drafts an answer for you to review

You stay in control — the skill only reads and analyzes, never posts.

## Quick Start

```bash
# Check replies on a tweet
python3 scripts/monitor.py --url "https://x.com/user/status/123456"

# Watch for new replies (outputs new ones since last check)
python3 scripts/monitor.py --url "https://x.com/user/status/123456" --watch
```

## Requirements

- Python 3.7+ (stdlib only)
- [Camofox](https://github.com/nicepkg/camofox-browser) running on port 9377
- A working Nitter instance (default: nitter.net)

## How It Works

1. Uses Camofox browser to render nitter.net (JS-rendered page)
2. Extracts reply author, text, and engagement from the rendered page
3. Compares with previous check to find new replies
4. Optionally identifies technical questions for AI analysis

## Output Format

```json
{
  "tweet_url": "https://x.com/user/status/123",
  "checked_at": "2026-02-14T22:00:00",
  "total_replies": 5,
  "new_replies": [
    {
      "author": "@username",
      "text": "How do I fix this error?",
      "likes": 2,
      "is_question": true
    }
  ]
}
```

## Companion Skills

- [x-tweet-fetcher](https://github.com/ythx-101/x-tweet-fetcher) — Fetch tweet content and stats

## License

MIT
