# Pretty Good AI Voice Tester

A Python voice bot that calls **only** the Pretty Good AI assessment line, behaves like
a realistic patient, records/transcribes both sides, and turns completed calls into an
evidence-backed QA report.

Gemini API usage is configured for Google's free tier. A real phone call still requires a
telephone provider such as SignalWire and may incur telephony charges.

## What it does

- Places outbound calls through one SignalWire number.
- Hard-locks the destination to `+1-805-439-8008`.
- Bridges SignalWire's bidirectional cXML media stream to Gemini Live using its free API tier.
- Includes 12 varied patient scenarios (scheduling, refills, insurance, interruptions,
  ambiguity, and safety routing).
- Saves dual-channel MP3 recordings, speaker-labeled transcripts, raw events, and metadata.
- Analyzes each transcript and compiles findings into `BUG_REPORT.md`.

## Prerequisites

- Python 3.11+
- A free Google AI Studio Gemini API key
- A SignalWire account, Space, API token, project ID, and one voice-capable SignalWire number
- A public HTTPS/WSS tunnel such as ngrok or Cloudflare Tunnel

Keep the same `SIGNALWIRE_FROM_NUMBER` for every submitted test call. Do not put real patient
information into the scenario files or recordings.

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

Fill in `.env`. Start a tunnel to local port 8000, then set `PUBLIC_BASE_URL` to its HTTPS
origin. The application converts it to WSS for SignalWire media streams.

Create the Gemini key at [Google AI Studio](https://aistudio.google.com/app/apikey). You do
not need to enable billing. Free-tier traffic may be used by Google to improve its products,
so use only the fictional patient details already included in this repository.

## Run

Terminal 1:

```bash
pgai-voice serve
```

Terminal 2:

```bash
# Inspect scenarios and validate setup without dialing.
pgai-voice scenarios
pgai-voice call 01-simple-scheduling --dry-run

# Place one real call.
pgai-voice call 01-simple-scheduling
```

After listening to early calls, tune scenario prompts or VAD settings before running the
required set. Then create ten calls:

```bash
pgai-voice batch --count 10 --delay 20
```

SignalWire calls are created sequentially. The delay controls creation time, not call completion;
for careful iteration, one-at-a-time calls are preferable.

## Analyze calls

Each call creates `artifacts/<run-id>/` containing:

```text
metadata.json
events.jsonl
transcript.jsonl
transcript.txt
recording.mp3
```

Once a transcript exists:

```bash
pgai-voice analyze <run-id>
pgai-voice report
```

The first command writes `analysis.json`; the second combines all analyses into
`BUG_REPORT.md`. Listen to the corresponding MP3 and manually verify every finding before
submission. Automated analysis is a triage aid, not the final judge.

## Submission checklist

- At least 10 coherent, complete calls lasting roughly 1–3 minutes
- MP3 recording and transcript for both sides of every submitted call
- Reviewed `BUG_REPORT.md` with useful evidence and call references
- This README and [ARCHITECTURE.md](ARCHITECTURE.md)
- One public GitHub repository with no secrets or real patient data
- Loom walkthrough (maximum five minutes)
- Separate five-minute screen recording showing AI-assisted debugging and the prompts used
- The single SignalWire caller number in E.164 format on the submission form

The application cannot create Loom videos, supply API credentials, or remove the cost of
calling a real telephone number. Those are the final manual steps.

## Verification

```bash
pytest
ruff check .
```

## Troubleshooting

- **Call connects but is silent:** confirm the tunnel supports WebSockets and that
  `PUBLIC_BASE_URL` is HTTPS.
- **SignalWire cannot reach callbacks:** keep the server and tunnel running for the full call and
  recording-processing period.
- **No practice-agent transcript:** inspect server logs for Gemini Live errors.
- **Bot talks over the greeting:** increase `silence_duration_ms` or change the initial
  `response.create` instruction in `server.py`.
- **Awkward interruption recovery:** inspect clear/truncate events and tune VAD against actual
  calls; telephony timing varies.

## Current API references

- [Gemini Live API](https://ai.google.dev/gemini-api/docs/live-api)
- [Gemini API pricing and free tier](https://ai.google.dev/gemini-api/docs/pricing)
- [SignalWire cXML Stream](https://signalwire.com/docs/compatibility-api/cxml/reference/voice/stream)
- [SignalWire Create a Call](https://signalwire.com/docs/compatibility-api/rest/calls/create-a-call)
