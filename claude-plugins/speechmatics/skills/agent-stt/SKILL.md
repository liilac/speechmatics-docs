---
name: agent-stt
description: Covers agent STT, the turn-based Speech to Text (STT) interaction pattern on the Speechmatics Realtime API (Linden 1 model) that returns punctuated, speaker-attributed segments and turn events ready to pass to an LLM. Includes the /v2/agent WebSocket endpoint, handshake and authentication, StartRecognition config, the Agent STT SDK (speechmatics-agent-stt), segmentation, turn detection modes, message schemas, errors, and close codes. Use when building the STT layer of a voice agent, choosing between agent STT and plain Realtime transcription, or when a user mentions linden-1, /v2/agent, AgentSttAsyncClient, AddSegment, AddPartialSegment, StartOfTurn, EndOfTurn, SpeechStarted, SpeechEnded, turn_config, turn_detection_mode, emit_sentences, or ForceEndOfUtterance in external mode.
---

# Agent STT

Agent STT is transcription designed for building voice agents. Stream audio in and receive speaker-labeled, turn-based transcription back, punctuated and ready to pass to an LLM. It is the Speech to Text (STT) layer only; the LLM and speech output are the application's responsibility.

- Model: Linden 1 (`"model": "linden-1"`). Not available on the Batch or plain Realtime endpoints.
- Deployment: SaaS only.

## When to use this skill

| Need | Use |
| --- | --- |
| Whole segments per speaker plus `StartOfTurn`/`EndOfTurn`, to drive an LLM | Agent STT (this skill) |
| Word-by-word Partials and Finals with timings and confidence, captions, dictation, translation, audio events, channel diarization, `max_delay` tuning, Standard/Enhanced/Melia 1/Oak 1 | `speechmatics:realtime-transcription` |
| A ready-made LiveKit, Pipecat, or Vapi integration (the fastest path to production) | `speechmatics:voice-agent-integrations` |
| Pre-recorded files | `speechmatics:batch-transcription` |
| API keys, temporary keys, regions, languages | `speechmatics:get-started` |

The Realtime API returns transcription word by word and leaves grouping to the client. Agent STT does the grouping and turn detection on the service.

Three ways to use agent STT: an integration (LiveKit, Pipecat, Vapi), the Agent STT SDK (a Python client), or the WebSocket API directly from any language.

## Prerequisites

- An API key from the [portal](https://portal.speechmatics.com/settings/api-keys). Store it as a managed secret. Enterprise customers may need to contact [Support](https://support.speechmatics.com).

## Endpoint and authentication

```
wss://global.rt.speechmatics.com/v2/agent
```

The global endpoint routes to the nearest region. Pin a region for data residency: `wss://eu.rt.speechmatics.com/v2/agent`, `wss://us.rt.speechmatics.com/v2/agent`, `wss://au.rt.speechmatics.com/v2/agent`.

- Server side: `Authorization: Bearer YOUR_API_KEY` on the handshake request.
- Browser: a Realtime (`type=rt`) temporary key in the query string, `wss://global.rt.speechmatics.com/v2/agent?jwt=<temporary-key>`. There is no separate agent STT key type. See `speechmatics:get-started`.
- Handshake responses: `101` connected, `400` malformed request, `401` invalid API key or temporary key, `405` method is not `GET`.

## Quickstart: Agent STT SDK (Python)

The SDK manages the WebSocket session, streams audio, and delivers segments and turn events to callbacks. It runs no voice activity detection or turn detection of its own: either the service closes turns, or the application does. Source: [speechmatics-agent-stt on GitHub](https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/agent_stt).

```
pip install speechmatics-agent-stt pyaudio
export SPEECHMATICS_API_KEY=<your-api-key>
```
`pyaudio` is required for microphone input.

```python
import asyncio

from speechmatics.agent_stt import (
    AgentSttAsyncClient, Microphone, Model, ServerMessageType, TranscriptionConfig,
)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024


async def main() -> None:
    mic = Microphone(sample_rate=SAMPLE_RATE, chunk_size=CHUNK_SIZE)
    if not mic.start():
        print("PyAudio not installed - install with: pip install pyaudio")
        return

    # Uses SPEECHMATICS_API_KEY from the environment
    client = AgentSttAsyncClient(
        transcription_config=TranscriptionConfig(
            model=Model.LINDEN_1,
            language="en",
            enable_partials=True,
            diarization="speaker",
        )
    )

    # Register handlers before the session opens, so no message arrives unhandled
    @client.on(ServerMessageType.ADD_PARTIAL_SEGMENT)
    def handle_partial_segment(message):
        print(f"[partial] {message['segment']['transcript']}")

    @client.on(ServerMessageType.ADD_SEGMENT)
    def handle_segment(message):
        speaker = message["segment"].get("speaker", "?")
        print(f"[final]   {speaker}: {message['segment']['transcript']}")

    @client.on(ServerMessageType.END_OF_TURN)
    def handle_end_of_turn(message):
        print(f"[turn]    end at {message['metadata']['end_time']}s")

    async with client:
        print("\nMicrophone ready - speak now (Ctrl+C to stop)\n")
        try:
            while True:
                await client.send_audio(await mic.read(CHUNK_SIZE))
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        finally:
            mic.stop()

    print(f"\nTranscript: {client.transcript_text(speaker_labels=True)}")


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
```

Expected output:

```
[partial] hello I'd like to check on my
[final]   S1: Hello, I'd like to check on my order.
[turn]    end at 3.24s
```

## Using the WebSocket API directly

1. Open the connection with the API key or temporary key.
2. Send `StartRecognition` with `audio_format`, `transcription_config`, and optionally `turn_config`.
3. Wait for `RecognitionStarted`.
4. Stream audio as binary `AddAudio` messages. Each is acknowledged by `AudioAdded` with a `seq_no`.
5. Handle segments and turn events as they arrive.
6. Send `EndOfStream` with `last_seq_no`; the server sends the remaining segments, then `EndOfTranscript`.

```json
{
  "message": "StartRecognition",
  "audio_format": { "type": "raw", "encoding": "pcm_s16le", "sample_rate": 16000 },
  "transcription_config": {
    "model": "linden-1",
    "language": "en",
    "enable_partials": true,
    "diarization": "speaker"
  },
  "turn_config": { "turn_detection_mode": "vad" }
}
```

## Essential configuration

`audio_format` (required): raw audio only.

| Field | Values |
| --- | --- |
| `type` | `raw` |
| `encoding` | `pcm_f32le`, `pcm_s16le` |
| `sample_rate` | `8000`, `16000` |

`transcription_config` (required fields: `language`, `model`):

| Field | Values | Default | Notes |
| --- | --- | --- | --- |
| `model` | `linden-1` | required | Required by the API schema. The docs' `external` mode SDK sample omits it from `TranscriptionConfig`; pass `Model.LINDEN_1` to be explicit. |
| `language` | language code | required | See `speechmatics:get-started` for languages. |
| `enable_partials` | boolean | `false` | Sends `AddPartialSegment`. |
| `diarization` | `none`, `speaker` | `none` | `speaker` adds `segment.speaker` labels (`S1`, `S2`, ...). |
| `emit_sentences` | boolean | `false` | One sentence per segment. |
| `speaker_diarization_config` | object | | `speaker_sensitivity`, `max_speakers`, `prefer_current_speaker`, `get_speakers`, `speakers`. Requires `diarization: "speaker"` when `speakers` or `get_speakers` is set. |
| `additional_vocab`, `domain`, `output_locale`, `transcript_filtering_config` | | | See [references/api-reference.md](references/api-reference.md). |

`turn_config.turn_detection_mode`:

| Mode | Who decides | Use it when |
| --- | --- | --- |
| `vad` (default) | The service, from voice activity | The application streams audio and has no endpointing of its own. |
| `external` | The application, with `ForceEndOfUtterance` | Something upstream already detects turn ends: Pipecat, LiveKit, or a push-to-talk control. |

## Server messages to act on

| Group | Messages | Meaning |
| --- | --- | --- |
| Speech signals | `SpeechStarted`, `SpeechEnded` | Voice activity. `vad` mode only. Not turn boundaries. Use for interruption handling and UI feedback. |
| Segments | `AddPartialSegment`, `AddSegment` | The transcript. Each partial replaces the last. `AddSegment` is final. |
| Turn signals | `StartOfTurn`, `EndOfTurn` | Turn boundaries. `EndOfTurn` is the turn's last message and the cue to respond. |

Segment payload:

```json
{
  "message": "AddSegment",
  "segment": { "transcript": "Hello, I'd like to check on my order.", "speaker": "S1" },
  "metadata": { "start_time": 1.02, "end_time": 3.24 }
}
```

Pass `AddSegment` text to the LLM. Use `AddPartialSegment` only for display.

## Closing turns from the application (external mode)

```python
from speechmatics.agent_stt import TurnConfig, TurnDetectionMode

client = AgentSttAsyncClient(
    transcription_config=TranscriptionConfig(language="en"),
    turn_config=TurnConfig(turn_detection_mode=TurnDetectionMode.EXTERNAL),
)
```

Close each turn when the application decides speech has ended:

```python
client.finalize()
```

The call is stamped with the audio position at the moment it is made, so the service cuts the turn where speech stopped rather than wherever the message lands.

Over the raw WebSocket, send `ForceEndOfUtterance` with the required `timestamp` (seconds from session start):

```json
{ "message": "ForceEndOfUtterance", "timestamp": 3.24 }
```

The flushed text arrives as a normal `AddSegment`, followed by `EndOfTurn`.

## Gotchas

- Never concatenate `AddPartialSegment` messages. Each one replaces the previous. Display the latest and discard the rest.
- One turn often produces several `AddSegment` messages (speaker change, sentence boundary with `emit_sentences`, two-minute cap). To reconstruct a turn, join the segments between `StartOfTurn` and `EndOfTurn`.
- Respond on `EndOfTurn`, not `SpeechEnded`. A mid-sentence pause produces `SpeechEnded` while the turn stays open.
- `StartOfTurn` fires on the first word of transcript, not the first sound.
- In `external` mode nothing else closes a turn. If the application stops calling `finalize()` or sending `ForceEndOfUtterance`, it receives segments but never `EndOfTurn`. No `SpeechStarted` or `SpeechEnded` is sent in this mode.
- In `vad` mode `ForceEndOfUtterance` is not supported, and voice activity detection is not currently configurable.
- Do not run two turn detectors against the same audio. Pick the one that owns the decision.
- `ForceEndOfUtterance` timestamps must increase. An earlier or equal timestamp is rejected with a `Warning`.
- A segment that reaches the two-minute cap is a sign that turns are not being closed.
- `segment.speaker` is present only when diarization attributed a speaker. Custom speaker labels must not look like `S1`, `S2`, or `UU`.
- Audio must be raw PCM at 8000 or 16000 Hz. `mulaw` and `file` input are not accepted on this endpoint.
- `SetRecognitionConfig` can change only `enable_partials` mid-session (`language` may be included but must match).
- Retry only after close codes `4005`, `4013`, and `1011`, waiting at least 5–10 seconds.

## Reference files

| Read | When |
| --- | --- |
| [references/api-reference.md](references/api-reference.md) | Implementing the WebSocket protocol directly: handshake, full `StartRecognition` schema, every client and server message, `Info`/`Warning`/`Error` types, close codes. |
| [references/segmentation-and-turns.md](references/segmentation-and-turns.md) | Deciding how to consume segments and turns: segment boundaries, speaker labels and speaker identification, sentence-level segments, `vad` versus `external` mode in depth. |

## Docs

- Overview: https://docs.speechmatics.com/speech-to-text/agent-stt
- Quickstart: https://docs.speechmatics.com/speech-to-text/agent-stt/quickstart
- Turn detection: https://docs.speechmatics.com/speech-to-text/agent-stt/turn-detection
- Segmentation: https://docs.speechmatics.com/speech-to-text/agent-stt/segmentation
- API reference: https://docs.speechmatics.com/api-ref/agent-stt-websocket
