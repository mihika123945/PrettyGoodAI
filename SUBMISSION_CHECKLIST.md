# Submission Checklist

## Completed assets

- Source code for the SignalWire + Gemini voice testing harness
- `README.md`
- `ARCHITECTURE.md`
- `BUG_REPORT.md`
- 10 completed call artifact folders in `artifacts/`
- Each artifact folder contains:
  - `recording.mp3`
  - `transcript.txt`
  - `transcript.jsonl`
  - `metadata.json`
  - `events.jsonl`
- Tests pass with `python -m pytest -q`
- Lint passes with `python -m ruff check .`

## Submission form details

- Caller number used for all real calls: `+12086685764`
- Assessment destination: `+18054398008`
- Telephony provider: SignalWire
- Voice/model provider: Google Gemini API

## Remaining manual tasks

1. Push this repository to GitHub.
2. Record a Loom walkthrough under 5 minutes using `LOOM_OUTLINE.md`.
3. Record a separate AI-debugging video showing the real debugging process:
   - SignalWire migration
   - ngrok setup issues
   - recording download fallback
   - Gemini quota/rate-limit handling
4. Submit the GitHub URL, videos, and caller number.

## Before pushing

Confirm `.env` is not staged:

```powershell
git status --short
```

The `.env` file should not appear.
