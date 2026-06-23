from voice_tester.server import (
    build_signalwire_cxml,
    pcm24k_to_signalwire_mulaw,
    signalwire_audio_to_pcm,
)


def test_gemini_pcm_converts_to_signalwire_mulaw():
    # 20 ms of mono PCM16 at 24 kHz becomes about 20 ms / 160 bytes at 8 kHz.
    converted, _ = pcm24k_to_signalwire_mulaw(b"\x00\x00" * 480)
    assert len(converted) == 160


def test_signalwire_cxml_includes_stream_parameters():
    cxml = build_signalwire_cxml("wss://example.com/media", {"run_id": "abc"})
    assert '<Connect><Stream url="wss://example.com/media" codec="PCMU@8000h" realtime="true">' in cxml
    assert '<Parameter name="run_id" value="abc" />' in cxml


def test_signalwire_mulaw_audio_decodes_to_pcm():
    pcm, rate = signalwire_audio_to_pcm(
        b"\xff" * 160, {"encoding": "audio/x-mulaw", "sampleRate": 8000}
    )
    assert len(pcm) == 320
    assert rate == 8000
