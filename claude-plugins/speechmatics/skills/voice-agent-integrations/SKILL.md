---
name: voice-agent-integrations
description: Builds voice agents, telephony transcription, and no-code automations with Speechmatics through third-party frameworks and SDKs. Covers the LiveKit Agents plugin (speechmatics.STT, speechmatics.TTS), Pipecat services (SpeechmaticsSTTService, SpeechmaticsTTSService), the Twilio Media Streams reference proxy, the Vapi transcriber, the Zapier actions, the deprecated Speechmatics Voice SDK (speechmatics-voice, VoiceAgentClient), and the SDK overview. Use when the user mentions LiveKit, Pipecat, Twilio, Vapi, Zapier, livekit-agents[speechmatics], pipecat-ai[speechmatics], turn_detection_mode, TurnDetectionMode.EXTERNAL or VAD, Silero VAD, speaker_format, speaker_active_format, known_speakers, get_speaker_ids, STTUpdateSettingsFrame, VoiceAgentConfig presets, or asks which Speechmatics SDK or integration to use.
---

# Voice agent integrations

Connect Speechmatics Speech to Text (STT) and Text to Speech (TTS) to voice agent frameworks, telephony, and no-code tools. Speechmatics supplies the STT and TTS layers; the framework supplies the LLM and orchestration.

Docs: https://docs.speechmatics.com/integrations-and-sdks/

## When to use

| Goal | Use | Reference |
|---|---|---|
| Voice agent on LiveKit's WebRTC infrastructure (engineers) | LiveKit Agents plugin | [references/livekit.md](references/livekit.md) |
| Full control of the voice pipeline in code (power builders) | Pipecat services | [references/pipecat.md](references/pipecat.md) |
| No-code voice agent platform | Vapi transcriber | [references/vapi.md](references/vapi.md) |
| Transcribe both sides of a live phone call | Twilio reference proxy | [references/twilio.md](references/twilio.md) |
| Transcribe audio inside a no-code workflow | Zapier actions (beta) | [references/zapier.md](references/zapier.md) |
| Maintain an existing `speechmatics-voice` integration | Voice SDK (deprecated) | [references/voice-sdk.md](references/voice-sdk.md) |
| Pick an SDK for direct API calls | SDK overview | [references/sdks.md](references/sdks.md) |

Do not use this skill for:

- Calling agent STT directly (messages, segmentation, turn events): `speechmatics:agent-stt`.
- Raw streaming over the Realtime API WebSocket: `speechmatics:realtime-transcription`.
- TTS voices, formats, and the TTS API itself: `speechmatics:text-to-speech`.
- Diarization, custom dictionary, and other feature semantics: `speechmatics:transcription-features`.
- API keys, regions, and endpoints: `speechmatics:get-started`.

## Prerequisites

- A Speechmatics API key from the portal (https://portal.speechmatics.com/settings/api-keys). LiveKit, Pipecat, and the Twilio proxy read it from `SPEECHMATICS_API_KEY` (LiveKit and Pipecat also accept `api_key=`); Vapi and Zapier take it in their dashboards.
- LiveKit and Pipecat quickstarts: Python 3.10+ and an OpenAI API key (`OPENAI_API_KEY`) for the LLM.
- LiveKit: a LiveKit Cloud account, or self-hosted LiveKit with `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`.

## Key facts shared by LiveKit and Pipecat STT

Both STT integrations use agent STT, the turn-based interaction pattern on the Realtime API, on the Linden 1 model.

- Endpoint: the LiveKit and Pipecat integrations connect to `wss://eu2.rt.speechmatics.com/v2/agent` by default. These skills default to AU1, so set `base_url="wss://au.rt.speechmatics.com/v2/agent"` unless the user names another region. Override with `base_url` (Pipecat also reads `SPEECHMATICS_RT_URL`) for another region or a self-hosted deployment. The `/v2/agent` path is required (`/v2` is the streaming endpoint); the SDK appends `/agent` when the URL omits it.
- `model`: `linden-1` is the only model agent STT accepts.
- Minimum versions for Linden 1: LiveKit Agents v1.8.2, Pipecat 1.11.0.
- Sample rate: `8000` or `16000` only.
- Defaults: English, diarization on, partials on. An unset parameter is not sent, and agent STT applies its own default rather than the one in the Realtime API schema.
- Every language is global: the model recognizes a range of accents and dialects.
- One speaker label per segment (for example `S1`), no per-word speaker data. Unattributable segments, and all segments with diarization off, are labeled `UU`.

### Turn detection modes (both frameworks)

| Mode | Who closes the turn | Trade-off |
|---|---|---|
| `TurnDetectionMode.EXTERNAL` (default) | A VAD in your agent (LiveKit: Silero by default; Pipecat: a `vad_analyzer`) | Final transcript sooner with a tighter tail, but can clip a word at a turn boundary and drops short backchannels such as "mm-hmm" |
| `TurnDetectionMode.VAD` | Speechmatics, server-side | Slightly more accurate and keeps backchannels; timing is not configurable |

Gotchas:

- In `EXTERNAL` mode something must close each turn. With no VAD, the session produces no transcripts at all rather than failing.
- LiveKit `VAD` mode also needs `turn_handling=TurnHandlingOptions(turn_detection="stt")` on the `AgentSession`, or the plugin's end-of-speech events are discarded.
- Pipecat `VAD` mode: remove any competing `vad_analyzer` or `turn_analyzer` from the transport; `should_interrupt` controls barge-in.
- The `ADAPTIVE`, `FIXED`, and `SMART_TURN` modes, speaker focus (`focus_speakers`, `ignore_speakers`, `focus_mode`), `max_delay`, and end-of-utterance timing parameters are not supported by agent STT. See each reference for exact deprecation behavior.

### Parameter name differences

| Purpose | LiveKit `speechmatics.STT(...)` | Pipecat `SpeechmaticsSTTService.Settings(...)` |
|---|---|---|
| Partials | `include_partials` | `enable_partials` |
| Speaker template | `speaker_format` (`{speaker_id}`, `{text}`) | `speaker_active_format` (`{speaker_id}`, `{text}`, `{ts}`, `{lang}`) |
| Output locale | `output_locale` | not documented |
| Audio encoding | `audio_encoding` | constructor `encoding` |
| Collect speaker identifiers | `await stt.get_speaker_ids()` | `on_speakers_result` event |
| Runtime updates | not documented | `STTUpdateSettingsFrame` |

## LiveKit minimal example

```bash
uv init
uv add "livekit-agents[speechmatics,openai,silero]~=1.8.11" python-dotenv
```

```bash
# .env.local
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SPEECHMATICS_API_KEY=your_speechmatics_key
OPENAI_API_KEY=your_openai_key
```

```python
from livekit.agents import AgentSession
from livekit.plugins import openai, silero, speechmatics

# Share one VAD between the session and the plugin
vad = silero.VAD.load()

session = AgentSession(
    stt=speechmatics.STT(vad=vad),   # agent STT; the VAD closes each turn
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=speechmatics.TTS(),          # voice defaults to "sarah"
    vad=vad,
)
```

Run with `python main.py dev` (LiveKit Agents Playground) or `python main.py console` (local terminal). Full `main.py`, CLI setup, and every parameter: [references/livekit.md](references/livekit.md).

## Pipecat minimal example

```text
# requirements.txt
pipecat-ai[local-smart-turn,silero,speechmatics,webrtc,openai,runner]~=1.14.0
pipecat-ai-small-webrtc-prebuilt
python-dotenv
loguru
```

```python
import aiohttp

from pipecat.services.speechmatics.stt import SpeechmaticsSTTService
from pipecat.services.speechmatics.tts import SpeechmaticsTTSService
from pipecat.transcriptions.language import Language

stt = SpeechmaticsSTTService(
    settings=SpeechmaticsSTTService.Settings(language=Language.EN),
)

async with aiohttp.ClientSession() as session:
    tts = SpeechmaticsTTSService(
        api_key="YOUR_API_KEY",
        voice_id="sarah",
        aiohttp_session=session,
    )

# The STT service belongs directly after the transport input
pipeline = Pipeline([transport.input(), stt, user_aggregator, llm, tts, transport.output()])
```

In the default `EXTERNAL` mode, put a `vad_analyzer` (for example `SileroVADAnalyzer()`) on the transport or the user aggregator. Run with `python main.py` and open `http://localhost:7860/client`. Full `main.py` and every setting: [references/pipecat.md](references/pipecat.md).

## TTS in both frameworks

| Framework | Class | Parameters |
|---|---|---|
| LiveKit | `speechmatics.TTS()` | `voice` (default `"sarah"`), `api_key` |
| Pipecat | `SpeechmaticsTTSService(...)` | `api_key`, `voice_id` (default `"sarah"`), `base_url`, `aiohttp_session` |

For available voices and TTS options, use `speechmatics:text-to-speech`.

## Other integrations at a glance

- **Twilio**: clone `https://github.com/speechmatics/speechmatics-twilio-integration`, fill `.env` (`SPEECHMATICS_API_KEY`, `NGROK_AUTHTOKEN`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `FORWARD_TO_NUMBER`), run `python proxy.py` or `npm start`. The proxy forwards Twilio's μ-law 8 kHz audio unconverted to the Realtime API with `diarization: "channel"` and channel labels `["inbound", "outbound"]`. It is a reference implementation, not a hosted service. See [references/twilio.md](references/twilio.md).
- **Vapi**: select Speechmatics as the transcriber provider in the assistant's transcriber settings, or create an assistant with `SpeechmaticsTranscriber(provider="speechmatics", language="en")`. See [references/vapi.md](references/vapi.md).
- **Zapier** (beta): two actions, **Get Transcript from Audio** (short audio, transcript returned in the Zap) and **Submit Audio (Webhook)** (longer recordings, transcript delivered to a webhook URL). See [references/zapier.md](references/zapier.md).
- **Voice SDK** (`pip install speechmatics-voice`): deprecated and replaced by agent STT. Start new projects with `speechmatics:agent-stt`; use [references/voice-sdk.md](references/voice-sdk.md) only for existing integrations.

## Reference files

- [references/livekit.md](references/livekit.md): LiveKit quickstart, CLI setup, full `main.py`, all STT and TTS parameters, turn detection, diarization, speaker label reuse, deprecated parameters.
- [references/pipecat.md](references/pipecat.md): Pipecat quickstart, full `main.py`, constructor parameters, settings, turn detection, diarization, connection handling, deprecated parameters, TTS.
- [references/twilio.md](references/twilio.md): proxy architecture, credentials, install and run for Python and Node.js, audio format, troubleshooting.
- [references/vapi.md](references/vapi.md): dashboard setup, Python usage, best practices.
- [references/zapier.md](references/zapier.md): Zap setup, actions, settings, troubleshooting.
- [references/voice-sdk.md](references/voice-sdk.md): presets, events, segment payload, every `VoiceAgentConfig` option, speaker focus, known speakers, JSON serialization.
- [references/sdks.md](references/sdks.md): every Speechmatics SDK by language with repository links, and how to choose an integration.
