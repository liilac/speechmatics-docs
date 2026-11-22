# LiveKit Agents integration

Docs:

- Quickstart: https://docs.speechmatics.com/integrations-and-sdks/livekit/
- STT: https://docs.speechmatics.com/integrations-and-sdks/livekit/stt
- TTS: https://docs.speechmatics.com/integrations-and-sdks/livekit/tts
- LiveKit's own Speechmatics STT reference: https://docs.livekit.io/agents/models/stt/speechmatics/

[LiveKit Agents](https://docs.livekit.io/agents/) is a framework for building voice AI applications using WebRTC. The Speechmatics STT plugin uses agent STT on the Linden 1 model. Linden 1 requires LiveKit Agents v1.8.2 or later.

The plugin connects directly to Speechmatics with your own API key. To run transcription on LiveKit's infrastructure without a Speechmatics key, use [LiveKit Inference](https://docs.livekit.io/agents/models/inference/) instead.

## Contents

- [Quickstart](#quickstart)
- [STT plugin](#stt-plugin)
- [Turn detection](#turn-detection)
- [Speaker diarization](#speaker-diarization)
- [Deprecated parameters](#deprecated-parameters)
- [Full STT example](#full-stt-example)
- [TTS plugin](#tts-plugin)

## Quickstart

Prerequisites:

- Python 3.10+
- Speechmatics API key (https://portal.speechmatics.com)
- LiveKit Cloud account (https://cloud.livekit.io, free tier available)
- OpenAI API key (for the LLM)

The quickstart assumes LiveKit Cloud. To self-host, follow https://docs.livekit.io/transport/self-hosting/ and configure `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` for your deployment.

### 1. Create project

```bash
mkdir voice-agent && cd voice-agent
```

### 2. Install dependencies

```bash
uv init
uv add "livekit-agents[speechmatics,openai,silero]~=1.8.11" python-dotenv
```

The `silero` extra supplies the VAD that closes each turn.

### 3. Install and authenticate the LiveKit CLI

More install options: https://docs.livekit.io/home/cli/cli-setup/

```text
# macOS
brew install livekit-cli

# Linux
curl -sSL https://get.livekit.io/cli | bash

# Windows
winget install LiveKit.LiveKitCLI
```

Authenticate and link your LiveKit Cloud project:

```bash
lk cloud auth
```

### 4. Configure environment

Write your LiveKit Cloud credentials to `.env.local`:

```bash
lk app env -w
```

Then add your Speechmatics and OpenAI keys:

```bash
# .env.local
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SPEECHMATICS_API_KEY=your_speechmatics_key
OPENAI_API_KEY=your_openai_key
```

### 5. Create `main.py`

```python
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import openai, silero, speechmatics

load_dotenv(".env.local")


class VoiceAssistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful voice assistant. Be concise and friendly."
        )


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    # Voice Activity Detection: Silero, shared with the STT plugin below
    vad = silero.VAD.load()

    # Speech to Text: Speechmatics agent STT. The VAD closes each turn.
    stt = speechmatics.STT(vad=vad)

    # Language Model: OpenAI
    llm = openai.LLM(model="gpt-4o-mini")

    # Text to Speech: Speechmatics
    tts = speechmatics.TTS()

    # Create and start session
    session = AgentSession(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
    )

    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
        room_input_options=RoomInputOptions(),
    )

    await session.generate_reply(
        instructions="Say a short hello and ask how you can help."
    )


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(entrypoint_fnc=entrypoint),
    )
```

Both plugins run on their defaults here.

### 6. Run

```bash
# Connect to LiveKit; test in the Agents Playground at https://agents-playground.livekit.io
python main.py dev

# Speak to the agent locally in your terminal
python main.py console
```

Further resources:

- Working examples: https://github.com/speechmatics/speechmatics-academy/tree/main/integrations/livekit
- Production deployment: https://docs.livekit.io/agents/deployment/

## STT plugin

### Install

```bash
uv add "livekit-agents[speechmatics,silero]~=1.8.11"
```

The default turn detection mode needs a VAD running in your agent, and the plugin loads [Silero](https://docs.livekit.io/agents/build/turns/vad/) when you don't supply one. That is why the command includes the `silero` extra.

### Authentication

The plugin reads the API key from `SPEECHMATICS_API_KEY`, or pass `api_key=` to `speechmatics.STT()`.

```bash
# .env.local
SPEECHMATICS_API_KEY=your_speechmatics_key
```

### Endpoint

Default: `wss://eu2.rt.speechmatics.com/v2/agent`. Set `base_url` to reach a different region or a self-hosted deployment. Agent STT sessions are served on the `/v2/agent` path, and the SDK appends `/agent` when your URL omits it.

```python
stt = speechmatics.STT(
    # The /v2/agent path is required; /v2 is the streaming endpoint
    base_url="wss://eu2.rt.speechmatics.com/v2/agent",
)
```

### Basic usage

Pass the plugin as the `stt` of an `AgentSession`. The defaults transcribe English on Linden 1 with diarization and partial results enabled.

```python
from livekit.agents import AgentSession
from livekit.plugins import speechmatics

session = AgentSession(
    # Silero VAD is loaded automatically to close each turn
    stt=speechmatics.STT(language="en"),
    # ... llm, tts, etc.
)
```

### Transcription parameters

`speechmatics.STT` constructor:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | string | env var | Speechmatics API key. Falls back to `SPEECHMATICS_API_KEY` |
| `base_url` | string | `wss://eu2.rt.speechmatics.com/v2/agent` | Endpoint to connect to |
| `model` | Model \| string | `linden-1` | Transcription model. `linden-1` is the only model agent STT accepts |
| `language` | string | `"en"` | Language code for the input audio |
| `output_locale` | string \| null | `null` | BCP-47 locale controlling spelling and number formats, for example `"en-GB"` |
| `domain` | string \| null | `null` | Domain-specific language pack, for example `"finance"` |
| `include_partials` | boolean | `true` | Emit interim segments that update until the final segment arrives |
| `emit_sentences` | boolean | `false` | Close a segment at each sentence end, so each sentence arrives as its own final transcript instead of one per turn |
| `additional_vocab` | array \| null | `null` | `AdditionalVocabEntry` objects biasing recognition towards specific words |
| `sample_rate` | number | `16000` | Audio sample rate in Hz. Agent STT accepts `8000` and `16000`; any other value raises a `ValueError` |
| `audio_encoding` | AudioEncoding | `PCM_S16LE` | LiveKit frames are 16-bit PCM and are forwarded unconverted, so any other value raises a `ValueError` |

Notes:

- Every language is global: whichever you select, the model recognizes a range of accents and dialects. Language codes: https://docs.speechmatics.com/speech-to-text/languages
- A parameter you leave unset is not sent, and agent STT applies its own default rather than the one in the Realtime API schema. Partials and diarization are both on unless you turn them off.

### Custom vocabulary

Each entry takes a `content` value and optional `sounds_like` pronunciation variants.

```python
from livekit.plugins.speechmatics import AdditionalVocabEntry

stt = speechmatics.STT(
    additional_vocab=[
        # sounds_like helps when the spelling is unusual
        AdditionalVocabEntry(content="LiveKit", sounds_like=["live kit"]),
    ],
)
```

## Turn detection

Agent STT reports turn boundaries as `StartOfTurn` and `EndOfTurn` events. `turn_detection_mode` sets which component decides where those boundaries fall.

| Mode | Detection method |
|---|---|
| `TurnDetectionMode.EXTERNAL` | Default. A VAD running in your agent closes the turn. Works with LiveKit's own [turn detection](https://docs.livekit.io/agents/build/turns/) |
| `TurnDetectionMode.VAD` | Speechmatics closes the turn server-side using its own voice activity detection |

The two modes fail in opposite directions. `EXTERNAL` returns the final transcript sooner and with a tighter tail, but can clip a word at a turn boundary and drops short backchannels such as "mm-hmm" that never cross your VAD's speech threshold. `VAD` is slightly more accurate and keeps backchannels, because Speechmatics applies its own, more patient endpointing.

### Turn detection parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `turn_detection_mode` | TurnDetectionMode | `EXTERNAL` | Which component closes a turn |
| `vad` | VAD \| null | Silero | VAD that signals the end of a turn. Applies to `EXTERNAL` mode only; ignored in `VAD` mode |

End-of-utterance timing in `VAD` mode belongs to the service and is not configurable.

### External turn detection

`EXTERNAL` needs no configuration. The plugin loads Silero VAD when you don't pass a `vad`. Pass your own VAD to tune it, or reuse the one already on your session so a second model isn't loaded:

```python
from livekit.plugins import silero, speechmatics

vad = silero.VAD.load()

# Share one VAD between the session and the plugin
stt = speechmatics.STT(vad=vad)
```

To signal turn ends from your own logic instead, pass `vad=None` and call `finalize()` on the STT when the speaker stops.

Warning: in `EXTERNAL` mode something must close each turn. If Silero isn't installed and you pass no `vad`, the plugin logs a warning, nothing closes a turn, and the session produces no transcripts at all rather than failing.

### Server-side turn detection

Set `turn_detection_mode` to `VAD` to hand turn handling to Speechmatics. You must also set `turn_detection="stt"` in the session's turn handling options; without it the session ignores the end-of-speech events the plugin emits.

```python
from livekit.agents import AgentSession, TurnHandlingOptions
from livekit.plugins import speechmatics

session = AgentSession(
    stt=speechmatics.STT(
        turn_detection_mode=speechmatics.TurnDetectionMode.VAD,
    ),
    # Required, or the plugin's end-of-speech events are discarded
    turn_handling=TurnHandlingOptions(turn_detection="stt"),
)
```

## Speaker diarization

Diarization is enabled by default. Each transcript segment carries one speaker label, such as `S1`. Segments the model cannot attribute are labeled `UU`, and with diarization disabled every segment is labeled `UU`. Agent STT reports one speaker per segment rather than per word, so there is no per-word speaker data.

### Diarization parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `enable_diarization` | boolean | `true` | Attribute each segment to a speaker |
| `speaker_sensitivity` | number \| null | `null` | Speaker detection sensitivity, between `0` and `1`. Higher values help separate similar voices |
| `max_speakers` | number \| null | `null` | Maximum speakers to detect, between `2` and `100`. Unrestricted when unset |
| `prefer_current_speaker` | boolean | `false` | Reduce switching between similar-sounding speakers |
| `known_speakers` | array \| null | `null` | `SpeakerIdentifier` objects from an earlier session |
| `speaker_format` | string \| null | `null` | Template for speaker output |

All of these apply only while `enable_diarization` is `true`.

### Format speaker labels

`speaker_format` folds the speaker label into the transcript text your language model receives. The template accepts `{speaker_id}` and `{text}`.

```python
stt = speechmatics.STT(
    # Renders as <S1>Good morning.</S1>
    speaker_format="<{speaker_id}>{text}</{speaker_id}>",
)
```

Include the format in your agent instructions so the model interprets the labels consistently. To detect the primary speaker and format transcripts by speaker across providers, wrap the plugin with LiveKit's [`MultiSpeakerAdapter`](https://docs.livekit.io/agents/models/stt/#speaker-diarization).

### Reuse speaker labels across sessions

Speechmatics assigns speaker labels per session, so the same person is `S1` in one session and something else in the next. Call `get_speaker_ids()` once each speaker has said at least five words, then pass the result as `known_speakers` when you build the STT for the next session.

```python
# Returns one list per open stream, or a list of lists if several are open
speakers = await stt.get_speaker_ids()

stt = speechmatics.STT(known_speakers=speakers)
```

Speaker identifiers are unique to your Speechmatics account.

## Deprecated parameters

Parameters from plugin versions that predate agent STT are still accepted and each logs a warning. Unrecognized parameters are logged too, so a misspelled name isn't discarded silently.

The parameters below, along with the `ADAPTIVE`, `FIXED`, and `SMART_TURN` turn detection modes, are removed after October 5, 2026. Each of those three modes selected a server-side endpointing strategy that agent STT does not expose, so all three resolve to `EXTERNAL` with a warning. The `enhanced` and `standard` operating points resolve to `linden-1` the same way.

Renamed (the value still applies to the replacement):

| Parameter | Replacement |
|---|---|
| `operating_point` | `model` |
| `enable_partials` | `include_partials` |
| `diarization_sensitivity` | `speaker_sensitivity` |
| `speaker_active_format` | `speaker_format` |

Accepted and ignored:

| Parameter | Reason |
|---|---|
| `max_delay` | Agent STT rejects it |
| `punctuation_overrides` | Agent STT rejects it |
| `end_of_utterance_silence_trigger`, `end_of_utterance_max_delay`, `end_of_utterance_mode`, `end_of_turn_config` | End-of-utterance timing is the service's own |
| `focus_speakers`, `ignore_speakers`, `focus_mode` | Agent STT does not support speaker focus |
| `speaker_passive_format` | A segment has no passive case to format |
| `vad_config` | Turn detection is set with `turn_detection_mode` |
| `audio_settings`, `chunk_size`, `http_session`, `transcription_config` | Unused before agent STT |

The `update_speakers()` method is deprecated and does nothing, for the same reason as the speaker focus parameters.

## Full STT example

Combines transcription, turn detection, diarization, and speaker formatting in one STT instance.

```python
from livekit.agents import AgentSession
from livekit.plugins import silero, speechmatics
from livekit.plugins.speechmatics import (
    AdditionalVocabEntry,
    TurnDetectionMode,
)

# Shared between the session and the plugin so only one model is loaded
vad = silero.VAD.load()

stt = speechmatics.STT(
    # Transcription
    language="en",
    output_locale="en-US",
    include_partials=True,

    # Turn detection: the VAD above closes each turn
    turn_detection_mode=TurnDetectionMode.EXTERNAL,
    vad=vad,

    # Diarization
    enable_diarization=True,
    speaker_sensitivity=0.6,
    max_speakers=4,
    prefer_current_speaker=True,

    # Renders each segment as <S1>Good morning.</S1>
    speaker_format="<{speaker_id}>{text}</{speaker_id}>",

    # Custom vocabulary
    additional_vocab=[
        AdditionalVocabEntry(content="Speechmatics"),
        AdditionalVocabEntry(content="LiveKit", sounds_like=["live kit"]),
    ],
)

session = AgentSession(
    stt=stt,
    vad=vad,
    # ... llm, tts, etc.
)
```

## TTS plugin

### Install

```bash
uv add "livekit-agents[speechmatics]~=1.4"
```

### Usage

```python
from livekit.agents import AgentSession
from livekit.plugins import speechmatics

session = AgentSession(
    tts=speechmatics.TTS(),
    # ... stt, llm, etc.
)
```

### Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `voice` | string | `"sarah"` | Voice model to use |
| `api_key` | string | env var | Speechmatics API key (defaults to `SPEECHMATICS_API_KEY`) |

For available voices and detailed TTS options, see `speechmatics:text-to-speech` or https://docs.speechmatics.com/text-to-speech/quickstart.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| No transcripts at all, no error | `EXTERNAL` mode with no VAD. Install the `silero` extra, pass `vad=`, or call `finalize()` yourself |
| Agent never responds in `VAD` mode | `AgentSession` is missing `turn_handling=TurnHandlingOptions(turn_detection="stt")` |
| `ValueError` at construction | `sample_rate` is not `8000` or `16000`, or `audio_encoding` is not `PCM_S16LE` |
| Warnings about deprecated or unrecognized parameters | Rename or remove them per [Deprecated parameters](#deprecated-parameters) |
| Connected to the wrong API | `base_url` must use the `/v2/agent` path; `/v2` is the streaming endpoint |
| Linden 1 unavailable | Upgrade to LiveKit Agents v1.8.2 or later |
