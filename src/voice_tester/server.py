from __future__ import annotations

import asyncio
import audioop
import base64
import json
import logging
from contextlib import suppress
from xml.etree.ElementTree import Element, SubElement, tostring

import httpx
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from voice_tester.config import Settings, websocket_base_url
from voice_tester.scenarios import get_scenario
from voice_tester.storage import RunStore, TranscriptTurn, utc_now

LOGGER = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Pretty Good AI Voice Tester")
    app.state.settings = settings

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "voice_provider": "gemini"}

    @app.post("/cxml/{run_id}")
    async def cxml(run_id: str) -> Response:
        store = RunStore(settings.data_dir, run_id)
        metadata = json.loads((store.path / "metadata.json").read_text(encoding="utf-8"))
        scenario_id = metadata["scenario"]["id"]

        return Response(
            content=build_signalwire_cxml(
                f"{websocket_base_url(settings.public_base_url)}/media",
                {"run_id": run_id, "scenario_id": scenario_id},
            ),
            media_type="application/xml",
        )

    @app.websocket("/media")
    async def media(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            start_message = await _wait_for_start(websocket)
            parameters = start_message["start"].get("customParameters", {})
            run_id = parameters["run_id"]
            scenario = get_scenario(parameters["scenario_id"])
            stream_sid = start_message["start"]["streamSid"]
            call_sid = start_message["start"].get("callSid")
            store = RunStore(settings.data_dir, run_id)
            store.update_metadata(status="in-progress", stream_sid=stream_sid, call_sid=call_sid)
            media_format = start_message["start"].get("mediaFormat", {})
            await _bridge_call(
                websocket, stream_sid, scenario.prompt(), store, settings, media_format
            )
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as exc:
            LOGGER.exception("Media bridge failed")
            with suppress(UnboundLocalError):
                store.update_metadata(status="bridge-error", error=str(exc))
            with suppress(Exception):
                await websocket.close(code=1011)

    @app.post("/callbacks/call/{run_id}")
    async def call_callback(run_id: str, request: Request) -> dict:
        form = dict(await request.form())
        store = RunStore(settings.data_dir, run_id)
        store.append_event({"source": "signalwire-call-callback", "payload": form})
        updates = {"status": form.get("CallStatus", "unknown"), "call_sid": form.get("CallSid")}
        if form.get("CallDuration"):
            updates["duration_seconds"] = int(form["CallDuration"])
        store.update_metadata(**updates)
        return {"ok": True}

    @app.post("/callbacks/recording/{run_id}")
    async def recording_callback(run_id: str, request: Request) -> dict:
        form = dict(await request.form())
        store = RunStore(settings.data_dir, run_id)
        store.append_event({"source": "signalwire-recording-callback", "payload": form})
        recording_url = form.get("RecordingUrl")
        if recording_url and form.get("RecordingStatus") == "completed":
            output = store.path / "recording.mp3"
            async with httpx.AsyncClient(
                auth=(settings.signalwire_project_id, settings.signalwire_api_token), timeout=60
            ) as client:
                result = await client.get(f"{recording_url}.mp3")
                result.raise_for_status()
                output.write_bytes(result.content)
            store.update_metadata(
                recording_sid=form.get("RecordingSid"),
                recording_file=str(output),
                recording_duration_seconds=form.get("RecordingDuration"),
            )
        return {"ok": True}

    return app


async def _wait_for_start(websocket: WebSocket) -> dict:
    while True:
        message = json.loads(await websocket.receive_text())
        if message.get("event") == "start":
            return message


async def _bridge_call(
    signalwire_ws: WebSocket,
    stream_sid: str,
    instructions: str,
    store: RunStore,
    settings: Settings,
    media_format: dict | None = None,
) -> None:
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1alpha"},
    )
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=instructions,
        input_audio_transcription={},
        output_audio_transcription={},
        speech_config={
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": settings.live_voice}
            }
        },
    )

    async with client.aio.live.connect(model=settings.live_model, config=config) as session:
        input_rate_state = None
        output_rate_state = None
        input_transcript: list[str] = []
        output_transcript: list[str] = []

        async def signalwire_to_gemini() -> None:
            nonlocal input_rate_state
            while True:
                message = json.loads(await signalwire_ws.receive_text())
                event = message.get("event")
                if event == "media":
                    inbound_pcm, source_rate = signalwire_audio_to_pcm(
                        base64.b64decode(message["media"]["payload"]),
                        media_format,
                    )
                    pcm_16k = inbound_pcm
                    if source_rate != 16000:
                        pcm_16k, input_rate_state = audioop.ratecv(
                            inbound_pcm, 2, 1, source_rate, 16000, input_rate_state
                        )
                    await session.send_realtime_input(
                        audio=types.Blob(data=pcm_16k, mime_type="audio/pcm;rate=16000")
                    )
                elif event == "stop":
                    return

        async def gemini_to_signalwire() -> None:
            nonlocal output_rate_state
            while True:
                async for response in session.receive():
                    content = response.server_content
                    if not content:
                        continue

                    if content.input_transcription and content.input_transcription.text:
                        input_transcript.append(content.input_transcription.text)
                    if content.output_transcription and content.output_transcription.text:
                        output_transcript.append(content.output_transcription.text)

                    if content.interrupted:
                        await signalwire_ws.send_json({"event": "clear", "streamSid": stream_sid})
                        store.append_event({"source": "gemini-live", "event": "interrupted"})

                    model_turn = content.model_turn
                    if model_turn:
                        for part in model_turn.parts:
                            if not part.inline_data or not part.inline_data.data:
                                continue
                            pcm_24k = part.inline_data.data
                            pcm_8k, output_rate_state = audioop.ratecv(
                                pcm_24k, 2, 1, 24000, 8000, output_rate_state
                            )
                            mulaw = audioop.lin2ulaw(pcm_8k, 2)
                            await signalwire_ws.send_json(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": base64.b64encode(mulaw).decode()},
                                }
                            )

                    if content.turn_complete:
                        _save_transcript(input_transcript, "practice_agent", store)
                        _save_transcript(output_transcript, "patient", store)
                        input_transcript.clear()
                        output_transcript.clear()
                        store.append_event({"source": "gemini-live", "event": "turn-complete"})

        tasks = [
            asyncio.create_task(signalwire_to_gemini()),
            asyncio.create_task(gemini_to_signalwire()),
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            with suppress(WebSocketDisconnect, asyncio.CancelledError):
                task.result()
        store.update_metadata(status="stream-ended", stream_ended_at=utc_now())


def _save_transcript(chunks: list[str], speaker: str, store: RunStore) -> None:
    text = "".join(chunks).strip()
    if text:
        store.append_turn(TranscriptTurn(utc_now(), speaker, text))


def build_signalwire_cxml(stream_url: str, parameters: dict[str, str]) -> str:
    response = Element("Response")
    connect = SubElement(response, "Connect")
    stream = SubElement(
        connect,
        "Stream",
        {"url": stream_url, "codec": "PCMU@8000h", "realtime": "true"},
    )
    for name, value in parameters.items():
        SubElement(stream, "Parameter", {"name": name, "value": value})
    return '<?xml version="1.0" encoding="UTF-8"?>' + tostring(response, encoding="unicode")


def signalwire_audio_to_pcm(payload: bytes, media_format: dict | None) -> tuple[bytes, int]:
    media_format = media_format or {}
    encoding = str(media_format.get("encoding", "audio/x-mulaw")).lower()
    sample_rate = int(media_format.get("sampleRate", 8000))
    if "mulaw" in encoding or "pcmu" in encoding:
        return audioop.ulaw2lin(payload, 2), sample_rate
    return payload, sample_rate


def pcm24k_to_signalwire_mulaw(pcm: bytes, state=None) -> tuple[bytes, object]:
    """Convert Gemini's 24 kHz signed PCM16 output to SignalWire's 8 kHz μ-law."""
    pcm_8k, state = audioop.ratecv(pcm, 2, 1, 24000, 8000, state)
    return audioop.lin2ulaw(pcm_8k, 2), state


app = create_app()
