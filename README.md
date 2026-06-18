# Phistory

[中文](README_zh.md)

Phistory tracks how system prompts change across popular coding-agent CLIs like Claude Code, Codex, Kimi, opencode, OpenClaw, Hermes, and Pi.

Open the web viewer to compare prompt snapshots across versions and see how agent design changes through prompts, tools, policies, and runtime instructions.

**Start here:** [phistory.cc](https://phistory.cc/)

> Checks for new releases hourly. Archive last updated: **2026-06-18 19:04 UTC**.

![Phistory prompt diff viewer](docs/screenshot.png)

## Why Use It

- Follow how Anthropic, OpenAI, and other agent builders iterate on system prompts over time.
- See when new tools, permission checks, model defaults, and user-confirmation rules are added.
- Compare how different CLIs structure agent behavior, tool use, and developer-facing constraints.
- Cite stable prompt snapshots in posts, research notes, audits, or debugging reports.

## How It Works

For each supported release, Phistory installs the exact CLI package, runs it once through [`claude-tap`](https://github.com/liaohch3/claude-tap), captures the prompt-bearing HTTP request without calling the real model provider, and stores the result under `captures/<agent>/<version>/` with `prompt.md`, `trace.jsonl`, and `meta.json`.

GitHub Actions checks supported CLI releases every hour and commits new snapshots when they appear.

## Local Development

Use the hosted viewer at [phistory.cc](https://phistory.cc/). These commands are for local development, capture reproduction, historical backfills, and regenerating generated files.

```bash
# Install the locked development environment.
uv sync --all-groups

# Capture the latest supported CLI releases.
uv run phistory capture --latest --agents claude-code,codex,openclaw,hermes,kimi,opencode,pi

# Capture a historical version range for one agent.
uv run phistory backfill claude-code --from 2.1.113 --to latest

# Regenerate README.md, README_zh.md, docs/captures.md, and captures/index.json.
uv run phistory render-index

# Regenerate the static web viewer at index.html.
uv run phistory render-site
```

## Supported Agents

- Claude Code (`@anthropic-ai/claude-code`)
- Codex CLI (`@openai/codex`)
- OpenClaw (`openclaw`)
- Hermes Agent (`hermes-agent`)
- Kimi CLI (`MoonshotAI/kimi-cli`)
- opencode (`opencode-ai`)
- Pi (`@earendil-works/pi-coding-agent`)

## Capture Status

Last capture update: 2026-06-18 19:04 UTC

| Agent | Latest | Captures | Last Captured |
| --- | --- | ---: | --- |
| Claude Code | [2.1.181 - 2026-06-17](captures/claude-code/2.1.181/prompt.md) | 344 | 2026-06-17 22:24 UTC |
| Codex CLI | [0.141.0 - 2026-06-18](captures/codex/0.141.0/prompt.md) | 56 | 2026-06-18 05:21 UTC |
| Hermes Agent | [v2026.6.5 - 2026-06-06](captures/hermes/v2026.6.5/prompt.md) | 15 | 2026-06-06 05:06 UTC |
| Kimi CLI | [1.47.0 - 2026-06-05](captures/kimi/1.47.0/prompt.md) | 19 | 2026-06-05 13:28 UTC |
| OpenClaw | [2026.6.8 - 2026-06-16](captures/openclaw/2026.6.8/prompt.md) | 64 | 2026-06-16 17:36 UTC |
| opencode | [1.17.8 - 2026-06-17](captures/opencode/1.17.8/prompt.md) | 74 | 2026-06-17 22:24 UTC |
| Pi | [0.79.7 - 2026-06-18](captures/pi/0.79.7/prompt.md) | 21 | 2026-06-18 19:04 UTC |

## Project Trend

![Phistory star history](https://api.star-history.com/svg?repos=WEIFENG2333/phistory&type=Date)
