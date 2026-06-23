from __future__ import annotations

import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx

from voice_tester.config import Settings, normalize_phone
from voice_tester.scenarios import Scenario
from voice_tester.storage import RunStore, find_run


def create_run_id(scenario_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_id = re.sub(r"[^a-zA-Z0-9-]", "-", scenario_id)
    return f"{timestamp}-{safe_id}-{secrets.token_hex(4)}"


def place_call(settings: Settings, scenario: Scenario, dry_run: bool = False) -> dict:
    destination = normalize_phone(settings.allowed_test_number)
    if destination != "+18054398008":
        raise RuntimeError("Safety lock refused a destination other than the assessment number")

    run_id = create_run_id(scenario.id)
    store = RunStore(settings.data_dir, run_id)
    metadata = {
        "run_id": run_id,
        "scenario": scenario.to_dict(),
        "destination": destination,
        "from_number": settings.signalwire_from_number or "(not configured)",
        "telephony_provider": "signalwire",
        "status": "dry-run" if dry_run else "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    store.write_json("metadata.json", metadata)

    if dry_run:
        return metadata

    settings.require_call_credentials()
    base = settings.public_base_url
    call = _signalwire_create_call(
        settings,
        {
            "To": destination,
            "From": normalize_phone(settings.signalwire_from_number),
            "Url": f"{base}/cxml/{run_id}",
            "Method": "POST",
            "Record": "true",
            "RecordingChannels": "dual",
            "RecordingStatusCallback": f"{base}/callbacks/recording/{run_id}",
            "RecordingStatusCallbackEvent": "completed",
            "StatusCallback": f"{base}/callbacks/call/{run_id}",
            "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
            "Timeout": "30",
        },
    )
    store.update_metadata(call_sid=call["sid"], status=call["status"])
    return {**metadata, "call_sid": call["sid"], "status": call["status"]}


def _signalwire_create_call(settings: Settings, payload: dict) -> dict:
    url = (
        f"https://{settings.signalwire_space_url}"
        f"/api/laml/2010-04-01/Accounts/{settings.signalwire_project_id}/Calls.json"
    )
    response = httpx.post(
        url,
        content=urlencode(payload, doseq=True),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(settings.signalwire_project_id, settings.signalwire_api_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def hangup_call(settings: Settings, run_id: str) -> dict:
    store = find_run(settings.data_dir, run_id)
    metadata = store.read_json("metadata.json")
    call_sid = metadata.get("call_sid")
    if not call_sid:
        raise RuntimeError(f"No call_sid found for run {run_id}")

    url = (
        f"https://{settings.signalwire_space_url}"
        f"/api/laml/2010-04-01/Accounts/{settings.signalwire_project_id}"
        f"/Calls/{call_sid}.json"
    )
    current_response = httpx.get(
        url,
        auth=(settings.signalwire_project_id, settings.signalwire_api_token),
        timeout=30,
    )
    current_response.raise_for_status()
    current_call = current_response.json()
    if current_call.get("status") == "completed":
        store.update_metadata(status="completed")
        return current_call

    response = httpx.post(
        url,
        content=urlencode({"Status": "completed"}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(settings.signalwire_project_id, settings.signalwire_api_token),
        timeout=30,
    )
    response.raise_for_status()
    call = response.json()
    store.update_metadata(status=call.get("status", "completed"))
    store.append_event({"source": "signalwire-call-update", "payload": call})
    return call


def fetch_recording(settings: Settings, run_id: str) -> Path:
    store = find_run(settings.data_dir, run_id)
    metadata = store.read_json("metadata.json")
    call_sid = metadata.get("call_sid")
    if not call_sid:
        raise RuntimeError(f"No call_sid found for run {run_id}")

    list_url = (
        f"https://{settings.signalwire_space_url}"
        f"/api/laml/2010-04-01/Accounts/{settings.signalwire_project_id}/Recordings.json"
    )
    list_response = httpx.get(
        list_url,
        params={"CallSid": call_sid},
        auth=(settings.signalwire_project_id, settings.signalwire_api_token),
        timeout=30,
    )
    list_response.raise_for_status()
    payload = list_response.json()
    recordings = payload.get("recordings", [])
    if not recordings:
        raise RuntimeError(
            "No recording found yet. Make sure the call is completed, then wait 1-2 minutes."
        )

    recording = recordings[0]
    recording_sid = recording["sid"]
    if recording.get("status") != "completed":
        raise RuntimeError(
            "Recording exists but is not ready yet. "
            f"SignalWire status={recording.get('status')}, duration={recording.get('duration')}. "
            "Wait until the call ends, or run: "
            f"python -m voice_tester hangup {run_id}"
        )

    media_response = _download_signalwire_recording(settings, call_sid, recording_sid)

    output = store.path / "recording.mp3"
    output.write_bytes(media_response.content)
    store.update_metadata(
        recording_sid=recording_sid,
        recording_file=str(output),
        recording_duration_seconds=recording.get("duration"),
    )
    store.append_event({"source": "signalwire-recording-fetch", "payload": recording})
    return output


def _download_signalwire_recording(
    settings: Settings,
    call_sid: str,
    recording_sid: str,
) -> httpx.Response:
    base = (
        f"https://{settings.signalwire_space_url}"
        f"/api/laml/2010-04-01/Accounts/{settings.signalwire_project_id}"
    )
    candidates = [
        f"{base}/Calls/{call_sid}/Recordings/{recording_sid}.mp3",
        f"{base}/Recordings/{recording_sid}.mp3",
    ]
    last_response: httpx.Response | None = None
    for media_url in candidates:
        media_response = httpx.get(
            media_url,
            auth=(settings.signalwire_project_id, settings.signalwire_api_token),
            follow_redirects=True,
            timeout=60,
        )
        if media_response.status_code == 200:
            return media_response
        last_response = media_response
    if last_response:
        last_response.raise_for_status()
    raise RuntimeError("Recording download failed before making a request")
