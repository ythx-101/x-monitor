# x-monitor

A read-only [OpenClaw](https://github.com/openclaw/openclaw) skill that fetches the replies to a tweet through Camofox + Nitter without any login, flags the replies that look like questions, and in watch mode reports only the new ones — built for creators and developers who post technical content on X and want to find and answer the questions in their comments.

**中文简介：** x-monitor 是一个 OpenClaw 技能（也是一个普通的 Python 命令行工具），用于 X/推特评论监控：免登录、只读，通过 Camofox + Nitter 抓取某条推文的回复，标出评论区里的提问，并在 watch 模式下只返回新增评论，方便你或你的 AI agent 挑出要回答的问题、起草回复。

## What It Does

- **Fetches replies** to a tweet via Camofox (a browser) rendering a Nitter page — no X account, no API key.
- **Flags questions** with a keyword/question-mark heuristic (English and Chinese) and sets `is_question` on each reply.
- **Watch mode** (`--watch`) compares against the previous run and returns only new replies.

The script does these three things and nothing else. Drafting answers is done by the **AI agent that calls this skill**, and it only shows you drafts — x-monitor never posts or replies on X.

## Requirements

- Python 3.7+ (standard library only)
- [Camofox](https://github.com/jo-inc/camofox-browser) running and listening on port 9377 (default)
- A working Nitter instance (default: `nitter.net`; change it with `--nitter`)

## Quick Start

```bash
git clone https://github.com/ythx-101/x-monitor.git && cd x-monitor
```

Start Camofox following its README and make sure it listens on port 9377. Then:

```bash
# Check replies on a tweet
python3 scripts/monitor.py --url "https://x.com/username/status/123456"

# Watch for new replies (outputs only the ones not seen at the last check)
python3 scripts/monitor.py --url "https://x.com/username/status/123456" --watch
```

## Usage

| Option | Description |
|--------|-------------|
| `--url`, `-u` | Tweet URL (required; `x.com` or `twitter.com`) |
| `--watch`, `-w` | Watch mode: show only new replies since the last check |
| `--pretty`, `-p` | Pretty-print the JSON output |
| `--port` | Camofox port (default: `9377`) |
| `--nitter` | Nitter instance host (default: `nitter.net`) |

```bash
python3 scripts/monitor.py -u "https://x.com/username/status/123456" --port 9400 --nitter nitter.example.org --pretty
```

An unparseable URL prints a short usage line plus `error: Cannot parse tweet URL: ...` to stderr (no traceback) and exits with code 2.

## Output Format

Default mode (`replies`):

```json
{
  "tweet_url": "https://x.com/username/status/123",
  "username": "username",
  "tweet_id": "123",
  "checked_at": "2026-01-01T12:00:00.000000",
  "total_replies": 1,
  "questions": [
    {
      "author": "@someone",
      "author_name": "Display Name",
      "text": "How do I fix this error?",
      "time_ago": "12h",
      "likes": 2,
      "replies": 1,
      "views": 185,
      "media": ["https://pbs.twimg.com/media/XXX.jpg"],
      "is_question": true
    }
  ],
  "question_count": 1,
  "replies": [
    {
      "author": "@someone",
      "author_name": "Display Name",
      "text": "How do I fix this error?",
      "time_ago": "12h",
      "likes": 2,
      "replies": 1,
      "views": 185,
      "media": ["https://pbs.twimg.com/media/XXX.jpg"],
      "is_question": true
    }
  ]
}
```

With `--watch`, `replies` is replaced by `new_replies` and `new_count` (same per-reply fields):

```json
{
  "tweet_url": "https://x.com/username/status/123",
  "username": "username",
  "tweet_id": "123",
  "checked_at": "2026-01-01T12:00:00.000000",
  "total_replies": 5,
  "questions": [],
  "question_count": 0,
  "new_replies": [],
  "new_count": 0
}
```

If the replies cannot be fetched:

```json
{"tweet_url": "...", "username": "username", "tweet_id": "123", "checked_at": "...", "error": "Failed to fetch replies (is Camofox running?)"}
```

## When to Use / When Not to Use

**Good for:**

- Monitoring the comment section of your own tweets
- Finding the questions you still need to answer
- Periodic checks by an AI agent (watch mode)

**Not for:**

- Posting or replying on X (not supported)
- Fetching a single tweet's content — use [x-tweet-fetcher](https://github.com/ythx-101/x-tweet-fetcher)
- Searching all of X

Compared with other approaches: it needs no login and no X API key, is read-only, and uses only the Python standard library. The trade-offs are that it depends on a Nitter instance being available and on Camofox, and it parses page snapshots, so a change in the page structure can break it.

## FAQ

**Do I need an X/Twitter account or API key? / 需要 X 账号或 API key 吗？**
No. It reads public pages through Nitter. 不需要，通过 Nitter 读取公开页面。

**Does it post or reply for me? / 会自动回复吗？**
No, it is read-only. 不会，只读。

**What if nitter.net is down or blocked? / Nitter 挂了怎么办？**
Use another instance with `--nitter`. 用 `--nitter` 换其他实例。

**What does "Failed to fetch replies (is Camofox running?)" mean? / 这个报错是什么意思？**
Check that Camofox is running and that the port matches (`--port`). 检查 Camofox 是否在运行、端口是否正确。

**How does watch mode know what's new? / watch 模式怎么判断新评论？**
It compares `author` + `text` of each reply with the previous result stored in `data/state.json`. 按 author+text 与 `data/state.json` 里的上次结果比对。

**How are questions detected? / 怎么识别提问？**
By a keyword and question-mark heuristic (Chinese and English). It can misjudge; it is not an AI classifier. 关键词和问号启发式，可能误判，不是 AI 分类。

**Can I use it without OpenClaw? / 不用 OpenClaw 能用吗？**
Yes. It is a plain Python CLI that prints JSON. 可以，它就是个普通 Python CLI，输出 JSON。

## File Structure

```
x-monitor/
├── SKILL.md                    # Agent skill file
├── README.md                   # This file
├── LICENSE                     # MIT license
├── llms.txt                    # Summary for LLMs
├── scripts/
│   ├── monitor.py              # Main monitor script (replies + watch mode)
│   └── version_check.py        # Version checker (stderr, TTY only, non-blocking)
├── tests/
│   └── test_monitor.py         # Offline unit tests (unittest)
├── data/                       # Per-tweet reply snapshot for watch mode (state.json)
└── VERSION
```

Run the tests with `python3 -m unittest discover -s tests -v`.

## Companion Skills

- [x-tweet-fetcher](https://github.com/ythx-101/x-tweet-fetcher) — Fetch tweet content and stats

## License

MIT — see [LICENSE](LICENSE).
