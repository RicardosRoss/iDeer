# Daily Recommender

> Chinese documentation: **[README.zh-CN.md](./README.zh-CN.md)**  
> 如果你更习惯中文，请直接跳转到 **[中文版说明](./README.zh-CN.md)**。

A personal multi-source recommendation and briefing system.

It pulls signals from GitHub, HuggingFace, X / Twitter, and other profile-driven sources, then uses your OpenAI-compatible LLM endpoint to:

- rank and summarize daily items
- generate source-level digests
- produce a cross-source narrative report
- generate research ideas from the day’s signals

## What It Does

This repository is useful in two modes:

1. `Daily digest engine`
   Generate daily digests from GitHub, HuggingFace, and X / Twitter, then send them by email.

2. `Personal intelligence workflow`
   Monitor a specific circle, merge signals across sources, and output a readable report with interpretation, predictions, and ideas.

## Supported Sources

| Source | Data | Notes |
| --- | --- | --- |
| GitHub | Trending repositories | Good for open-source tools, frameworks, and engineering momentum |
| HuggingFace | Daily papers + popular models | Good for research and model ecosystem tracking |
| X / Twitter | Account timelines via RapidAPI | Supports static account pools and profile-driven discovery |

## Project Layout

```text
daily-recommender/
├── main.py                  # CLI entry
├── main_gpt.sh              # Repo-local launcher script
├── config.py                # Shared config dataclasses
├── base_source.py           # Shared source pipeline
├── report_generator.py      # Cross-source narrative report
├── idea_generator.py        # Research idea generation
├── description.txt          # Simple interest profile
├── researcher_profile.md    # Richer profile for reports / ideas
├── sources/                 # GitHub / HuggingFace / Twitter sources
├── fetchers/                # Raw data fetch clients
├── email_utils/             # HTML templates
├── llm/                     # OpenAI-compatible + Ollama wrappers
└── history/                 # Generated daily outputs
```

## Quick Start

### 1. Create the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env`

```bash
cp .env.example .env
```

Minimum required LLM settings:

```env
PROVIDER=openai
MODEL_NAME=your-model-name
BASE_URL=https://your-openai-compatible-endpoint/v1
API_KEY=your_api_key
TEMPERATURE=0.5
```

### 3. Run the default pipeline

```bash
bash main_gpt.sh
```

## Configuration Guide

The project auto-loads `.env` from the repository root. Keep runtime settings there instead of hardcoding them in scripts.

### 1. LLM

The preferred path is the standard trio:

```env
PROVIDER=openai
MODEL_NAME=gemini-3-flash-preview
BASE_URL=http://your-endpoint/v1
API_KEY=your_api_key
TEMPERATURE=0.5
```

Notes:

- `PROVIDER` is usually `openai`
- `BASE_URL` must point to an OpenAI-compatible endpoint
- `MODEL_NAME` is the exact model string
- `API_KEY` is your provider credential

### 2. Email

If you want the main pipeline to actually send emails, SMTP is required:

```env
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_SENDER=you@example.com
SMTP_RECEIVER=you@example.com
SMTP_PASSWORD=your_smtp_password
```

Notes:

- `SMTP_RECEIVER` supports multiple emails separated by commas
- `465` uses SSL by default

### 3. X / Twitter

X currently uses RapidAPI `twitter-api45`:

```env
X_RAPIDAPI_KEY=your_rapidapi_key
X_RAPIDAPI_HOST=twitter-api45.p.rapidapi.com
X_ACCOUNTS_FILE=x_accounts.txt
```

To enable profile-driven account discovery:

```env
X_DISCOVER_ACCOUNTS=1
X_PROFILE_FILE=
X_PROFILE_URLS=
X_DISCOVERY_PERSIST_FILE=x_accounts.discovered.txt
```

### 4. Optional Defaults

```env
DAILY_SOURCES="github huggingface"
NUM_WORKERS=8
DESCRIPTION_FILE=description.txt

GH_LANGUAGES="all"
GH_SINCE=daily
GH_MAX_REPOS=30

HF_CONTENT_TYPES="papers models"
HF_MAX_PAPERS=30
HF_MAX_MODELS=15

GENERATE_REPORT=0
GENERATE_IDEAS=0
```

## Common Commands

### Run one source

```bash
.venv/bin/python main.py --sources github --save
.venv/bin/python main.py --sources huggingface --save
.venv/bin/python main.py --sources twitter --save
```

### Run multiple sources

```bash
.venv/bin/python main.py --sources github huggingface twitter --save
```

### Generate a cross-source report

```bash
.venv/bin/python main.py \
  --sources github huggingface twitter \
  --save \
  --generate_report
```

### Generate research ideas

```bash
.venv/bin/python main.py \
  --sources github huggingface twitter \
  --save \
  --generate_ideas \
  --researcher_profile researcher_profile.md
```

## Outputs

All generated artifacts are written into `history/`:

```text
history/
├── github/<date>/
├── huggingface/<date>/
├── twitter/<date>/
├── reports/<date>/
└── ideas/<date>/
```

Typical per-source outputs:

- `json/`: item-level caches
- `<date>.md`: Markdown digest
- `*_email.html`: HTML email rendering

Report directory:

- `report.json`
- `report.md`
- `report.html`

## Profile Files

### `description.txt`

A light interest profile used by source-level filtering and summarization.

### `researcher_profile.md`

A richer profile better suited for `--generate_report` and `--generate_ideas`.

### `x_accounts.txt`

Static monitoring account pool.

### `x_accounts.discovered.txt`

Persisted discovered account pool from profile-driven discovery. It is ignored by git by default.

## Sanity Check

If you only want to verify that the standard LLM trio works:

```bash
.venv/bin/python - <<'PY'
from main import load_dotenv, env_str
from llm.GPT import GPT

load_dotenv()
model = env_str("MODEL_NAME")
base_url = env_str("BASE_URL")
api_key = env_str("API_KEY")

client = GPT(model, base_url, api_key)
print(client.inference("Reply with exactly OK.", temperature=0))
PY
```

If the output is `OK` or `OK.`, the standard endpoint path is working.

## Current Boundaries

- The main pipeline sends email directly, so SMTP is required for full end-to-end runs
- X depends on RapidAPI stability
- GitHub / HuggingFace / Twitter digests are generated first, then optionally merged into a unified report
- `codex_bridge` has been removed; the repository now uses only the standard model configuration path
