# Architecture

The harness uses SignalWire's Compatibility API/cXML for the outbound phone leg, call
lifecycle callbacks, and dual-channel recording. When the assessment line answers,
SignalWire connects a bidirectional Stream to the FastAPI server. The server converts the
assessment agent's 8 kHz mu-law telephone audio to 16 kHz PCM for a Gemini Live session,
then converts Gemini's 24 kHz PCM speech back to mu-law for SignalWire. Gemini handles voice
activity and interruption; the bridge clears queued SignalWire audio when Gemini reports an
interruption. A destination allowlist is deliberately enforced both in configuration
validation and at call creation.

Each call is represented by a run directory containing immutable event logs, speaker-labeled
transcript turns, SignalWire metadata, and the downloaded MP3. Scenarios are structured data
plus a behavioral prompt, so tests remain diverse without becoming rigid scripts. After a
call, a separate Gemini Flash-Lite pass scores quality and extracts evidence-backed issues
into JSON; the report compiler ranks those issues by severity. Analysis is intentionally
offline so it cannot add latency or steer the live conversation, and every generated finding
is expected to be checked against the recording before submission.
