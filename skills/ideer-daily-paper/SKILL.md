---
name: ideer-daily-paper
description: "Use iDeer as a daily paper-reading automation. Configure .env, choose paper-focused sources, run one-off or recurring digests, verify history outputs, and send summary emails or reports. 适用于每日论文摘要阅读、自动整理、邮件发送、Codex automation 配置。"
argument-hint: "[--dry-run] [--send-email] [--sources ...] [--with-report] [--with-ideas] [--date YYYY-MM-DD]"
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, Skill
---

# iDeer Daily Paper

Use this skill when the user wants Codex to operate this repository as a daily paper-reading system, especially for:

- first-time setup of a paper digest workflow
- recurring daily or weekday automation
- dry runs that save artifacts without sending email
- debugging failed runs or missing outputs
- switching between paper-only, paper+report, and paper+ideas modes

## Core rule

Do not re-implement the recommender pipeline inside the skill. This repo already has the execution path:

- `main.py`: canonical CLI entrypoint
- `scripts/run_daily.sh`: preferred daily launcher for env-driven runs

The skill should teach Codex how to configure, run, validate, and schedule that pipeline.

## Default operating assumptions

- Repo root is the current workspace unless the user specifies another checkout.
- For paper reading, default sources are `arxiv semanticscholar huggingface`.
- Add `github` only when the user also wants repo/code signals.
- Add `twitter` only when the user explicitly wants social signals and `X_RAPIDAPI_KEY` is configured.
- The repo defaults are already paper-first in `.env.example` and `scripts/run_daily.sh`.
- The first validation run should be a dry run: save outputs, skip email sending, then inspect `history/`.
- For recurring runs with stable config, prefer `bash scripts/run_daily.sh` over reconstructing a long `python main.py ...` command.

## Files to inspect before running

Always check these first:

- `.env`
- `profiles/description.txt`

Check these when the feature needs them:

- `profiles/researcher_profile.md`: needed for stronger report/idea generation
- `profiles/x_accounts.txt`: needed for Twitter/X monitoring

If `.env` does not exist, copy from `.env.example`. Do not invent secrets or overwrite existing credentials.

## Minimum config matrix

- Base run: `MODEL_NAME`, `BASE_URL`, `API_KEY`
- Source email sending: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_SENDER`, `SMTP_RECEIVER`, `SMTP_PASSWORD`
- Twitter/X: `X_RAPIDAPI_KEY`
- Cross-source report: `GENERATE_REPORT=1`
- Report email: `GENERATE_REPORT=1` and `SEND_REPORT_EMAIL=1`
- Idea generation: `GENERATE_IDEAS=1` and a valid `RESEARCHER_PROFILE`

Use [references/presets.md](references/presets.md) when you need concrete presets.

## Workflow

### Step 1: Classify the request

Map the user to one of these modes:

- **Dry run**: produce artifacts only, no outbound email
- **Full digest**: run the configured daily pipeline and send email
- **Setup/fix**: fill missing config, correct sources, or debug failures
- **Recurring automation**: create or update a scheduled Codex automation if the environment supports it

### Step 2: Choose the safest command

Prefer these command patterns:

```bash
# Safe first run for paper reading
python main.py \
  --sources arxiv semanticscholar huggingface \
  --save \
  --skip_source_emails
```

```bash
# Stable env-driven daily run
bash scripts/run_daily.sh
```

```bash
# Custom paper-focused run
python main.py \
  --sources arxiv semanticscholar huggingface \
  --save \
  --generate_report \
  --send_report_email \
  --generate_ideas
```

If email config is missing, fall back to a dry run instead of attempting SMTP and failing late.

### Step 3: Apply source defaults intentionally

- `arxiv`: use for fresh preprints. Default categories should match the user's field. For CS users, start with `cs.AI cs.CL cs.LG` unless the profile clearly points elsewhere.
- `semanticscholar`: use for broader venue coverage beyond arXiv. Prefer explicit `--ss_queries` when the interest profile is broad or ambiguous.
- `huggingface`: for paper reading, prefer `HF_CONTENT_TYPES="papers"`. Add `models` only when the user wants shipping/model ecosystem signals.
- `github`: useful when the user cares about code releases alongside papers.
- `twitter`: useful for commentary, fast-moving discourse, and conference chatter, but not required for a clean paper digest.

### Step 4: Validate artifacts after every run

Check today's date directory under:

- `history/<source>/<date>/`
- `history/<source>/<date>/<source>_email.html`
- `history/reports/<date>/report.md`
- `history/reports/<date>/report.html`
- `history/ideas/<date>/ideas.json`
- `history/ideas/<date>/ideas_email.html`

When reporting back, include:

- the date that actually ran
- which sources ran
- whether email was sent or intentionally skipped
- the artifact paths that were created
- the first concrete blocker if the run failed

### Step 5: Handle recurring automation

If the user explicitly asks for a Codex automation:

- prefer the automation feature exposed by the Codex app instead of editing system cron
- use the repo root as the automation working directory
- make the automation prompt self-sufficient: it should inspect `.env`, run the repo's launcher, verify outputs, and surface missing config
- default to every day at 13:00 Asia/Shanghai unless the user specifies otherwise

For a ready-to-use schedule and prompt, see [references/automation.md](references/automation.md).

Use this prompt shape:

```text
Run the iDeer daily paper digest in the repo root. Use .env as the source of truth. Prefer bash scripts/run_daily.sh. If SMTP configuration is incomplete, switch to a dry run that saves outputs without sending emails. After the run, verify today's history artifacts and summarize what was produced, what was emailed, and any missing configuration or failed sources.
```

If the environment does not support Codex automation, give the user a cron alternative that calls `scripts/run_daily.sh`.

## Safety rules

- Never print API keys, SMTP passwords, or auth tokens back to the user.
- Never send email on the first validation run unless the user explicitly asks for a live send.
- Never claim a report or idea digest exists before checking `history/`.
- Do not rewrite `profiles/researcher_profile.md` unless the user asked for profile updates.
- Prefer changing `.env` defaults and `scripts/run_daily.sh` defaults over embedding secrets in commands.

## Good defaults for first-time paper users

Start with the `paper-plus-ideas` preset in [references/presets.md](references/presets.md). It matches the repo default: paper summaries plus cross-source report plus ideas.
