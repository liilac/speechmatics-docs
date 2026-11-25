# Pipecat integration

Docs:

- Quickstart: https://docs.speechmatics.com/integrations-and-sdks/pipecat/
- STT: https://docs.speechmatics.com/integrations-and-sdks/pipecat/stt
- TTS: https://docs.speechmatics.com/integrations-and-sdks/pipecat/tts
- Pipecat's own references: https://docs.pipecat.ai/server/services/stt/speechmatics and https://docs.pipecat.ai/server/services/tts/speechmatics

[Pipecat](https://docs.pipecat.ai/) is a framework for building real-time voice bots using a pipeline architecture. `SpeechmaticsSTTService` uses agent STT on the Linden 1 model. Linden 1 requires Pipecat 1.11.0 or later.

## Contents

- [Quickstart](#quickstart)
- [STT service](#stt-service)
- [Turn detection](#turn-detection)
- [Speaker diarization](#speaker-diarization)
- [Connection handling](#connection-handling)
- [Deprecated and unsupported parameters](#deprecated-and-unsupported-parameters)
- [Full STT example](#full-stt-example)
- [TTS service](#tts-service)

## Quickstart

Runs a local WebRTC server; you connect to the bot from your browser. No cloud deployment or room setup required.

Prerequisites:

- Python 3.10+
- Speechmatics API key (https://portal.speechmatics.com)
- OpenAI API key (for the LLM)

### 1. Create project

```bash
mkdir voice-agent && cd voice-agent
```

### 2. Install dependencies

```text
# requirements.txt
pipecat-ai[local-smart-turn,silero,speechmatics,webrtc,openai,runner]~=1.14.0
pipecat-ai-small-webrtc-prebuilt
python-dotenv
loguru
```

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Configure environment

```text
# .env
SPEECHMATICS_API_KEY=your_speechmatics_key
OPENAI_API_KEY=your_openai_key
```

### 4. Create `main.py`

```python
import os

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.speechmatics.stt import SpeechmaticsSTTService
from pipecat.services.speechmatics.tts import SpeechmaticsTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import (
    TurnAnalyzerUserTurnStopStrategy,
)
from pipecat.turns.user_turn_strategies import UserTurnStrategies

load_dotenv(override=True)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting bot")

    async with aiohttp.ClientSession() as session:
        stt = SpeechmaticsSTTService(
            api_key=os.getenv("SPEECHMATICS_API_KEY"),
            settings=SpeechmaticsSTTService.Settings(
                # Default mode: the VAD on the user aggregator closes each turn
                turn_detection_mode=SpeechmaticsSTTService.TurnDetectionMode.EXTERNAL,
            ),
        )

        llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
        )

        tts = SpeechmaticsTTSService(
            api_key=os.getenv("SPEECHMATICS_API_KEY"),
            voice_id="sarah",
            aiohttp_session=session,
        )

        messages = [
            {
                "role": "system",
                "content": "You are a helpful voice assistant. Be concise and friendly.",
            },
        ]

        context = LLMContext(messages)
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            user_params=LLMUserAggregatorParams(
                # VADUserStoppedSpeakingFrame is broadcast upstream, so this
                # VAD still reaches the STT service placed before it
                vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
                user_turn_strategies=UserTurnStrategies(
                    stop=[
                        TurnAnalyzerUserTurnStopStrategy(
                            turn_analyzer=LocalSmartTurnAnalyzerV3()
                        )
                    ]
                ),
            ),
        )

        pipeline = Pipeline(
            [
                transport.input(),
                stt,
                user_aggregator,
                llm,
                tts,
                transport.output(),
                assistant_aggregator,
            ]
        )

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info("Client connected")
            await task.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info("Client disconnected")
            await task.cancel()

        runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
        await runner.run(task)


async def bot(runner_args: RunnerArguments):
    transport_params = {
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    }

    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
```

### 5. Run

```bash
python main.py
```

Open `http://localhost:7860/client` in your browser and allow microphone access. The first run can take a little longer while dependencies and models load.

Further resources:

- Working examples: https://github.com/speechmatics/speechmatics-academy/tree/main/integrations/pipecat
- More patterns and deployment options: https://docs.pipecat.ai/getting-started/quickstart

## STT service

### Install

```bash
uv add "pipecat-ai[speechmatics]~=1.14.0"
```

### Authentication

The service reads the API key from `SPEECHMATICS_API_KEY`, or pass `api_key=` to `SpeechmaticsSTTService()`.

```bash
# .env
SPEECHMATICS_API_KEY=your_speechmatics_key
```

### Endpoint

Default: `wss://eu2.rt.speechmatics.com/v2/agent`. Set `base_url`, or the `SPEECHMATICS_RT_URL` environment variable, to reach a different region or a self-hosted deployment. Agent STT sessions are served on the `/v2/agent` path, and the SDK appends `/agent` when your URL omits it.

```python
stt = SpeechmaticsSTTService(
    # The /v2/agent path is required; /v2 is the streaming endpoint
    base_url="wss://au.rt.speechmatics.com/v2/agent",
)
```

Region hostnames: https://docs.speechmatics.com/get-started/authentication#supported-endpoints (see `speechmatics:get-started`).

### Basic usage

Place the service after `transport.input()` in your pipeline. The defaults transcribe English on Linden 1.

```python
from pipecat.services.speechmatics.stt import SpeechmaticsSTTService
from pipecat.transcriptions.language import Language

stt = SpeechmaticsSTTService(
    settings=SpeechmaticsSTTService.Settings(language=Language.EN),
)

# The service belongs directly after the transport input
pipeline = Pipeline([transport.input(), stt, user_aggregator, llm, tts, transport.output()])
```

### Constructor parameters

Everything not listed here is a setting.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | string | env var | Speechmatics API key. Falls back to `SPEECHMATICS_API_KEY` |
| `base_url` | string | `wss://eu2.rt.speechmatics.com/v2/agent` | Endpoint to connect to. Falls back to `SPEECHMATICS_RT_URL` |
| `sample_rate` | number \| null | pipeline default | Audio sample rate in Hz. Agent STT accepts `8000` and `16000`; any other value fails the service permanently |
| `encoding` | AudioEncoding | `PCM_S16LE` | Audio encoding. Set at construction only, not a runtime setting |
| `settings` | Settings \| null | `null` | Runtime-configurable settings |
| `should_interrupt` | boolean | `true` | Interrupt bot output when Speechmatics detects user speech. Applies to `VAD` turn detection only |
| `ttfs_p99_latency` | number | `0.74` | P99 latency in seconds from speech end to final transcript. Override for your deployment |

### Transcription settings

Pass as `settings=SpeechmaticsSTTService.Settings(...)`. Change mid-conversation with an `STTUpdateSettingsFrame`.

| Setting | Type | Default | Description |
|---|---|---|---|
| `model` | string | `"linden-1"` | Transcription model. `linden-1` is the only model agent STT accepts |
| `language` | Language \| string | `Language.EN` | Language code for the input audio |
| `domain` | string \| null | `null` | Domain-specific language pack, for example `"finance"`, or a bilingual pack such as `"bilingual-en"` |
| `enable_partials` | boolean \| null | `true` | Emit interim segments that update until the final segment arrives |
| `emit_sentences` | boolean \| null | `false` | Close a segment at each sentence end, so each sentence arrives as its own `TranscriptionFrame` |
| `additional_vocab` | array | `[]` | `AdditionalVocabEntry` objects biasing recognition towards specific words |

Turn detection and diarization settings are listed in their sections below.

Notes:

- Every language is global: whichever you select, the model recognizes a range of accents and dialects. Language codes: https://docs.speechmatics.com/speech-to-text/languages
- A setting you leave unset is not sent, and agent STT applies its own default rather than the one in the Realtime API schema. Partials and diarization are both on unless you turn them off.

### Custom vocabulary

Each entry takes a `content` value and optional `sounds_like` pronunciation variants.

```python
stt = SpeechmaticsSTTService(
    settings=SpeechmaticsSTTService.Settings(
        additional_vocab=[
            # sounds_like helps when the spelling is unusual
            SpeechmaticsSTTService.AdditionalVocabEntry(
                content="Pipecat", sounds_like=["pipe cat"]
            ),
        ],
    ),
)
```

## Turn detection

Agent STT reports turn boundaries as `StartOfTurn` and `EndOfTurn` events. The `turn_detection_mode` setting sets which component decides where those boundaries fall.

| Mode | Detection method |
|---|---|
| `TurnDetectionMode.EXTERNAL` | Default. Pipecat closes the turn. A `VADUserStoppedSpeakingFrame` calls `finalize()` on the service |
| `TurnDetectionMode.VAD` | Speechmatics closes the turn server-side using its own voice activity detection |

The two modes fail in opposite directions. `EXTERNAL` returns the final transcript sooner and with a tighter tail, but can clip a word at a turn boundary and drops short backchannels such as "mm-hmm" that never cross your VAD's speech threshold. `VAD` is slightly more accurate and keeps backchannels, because Speechmatics applies its own, more patient endpointing.

### External turn detection

Pipecat's VAD drives `EXTERNAL` mode, so put a `vad_analyzer` on the transport or on the user aggregator. Either position works: the `VADUserStoppedSpeakingFrame` is broadcast both upstream and downstream, so it reaches the service even from a VAD that sits after it in the pipeline.

```python
transport_params = TransportParams(
    audio_in_enabled=True,
    audio_out_enabled=True,
    # Signals the end of each turn to the STT service
    vad_analyzer=SileroVADAnalyzer(),
)
```

The quickstart `main.py` instead puts the VAD on the user aggregator, with a smart turn analyzer as the stop strategy.

Warning: in `EXTERNAL` mode something must close each turn. With no VAD anywhere in the pipeline, nothing calls `finalize()` and the service produces no transcripts at all rather than failing.

### Server-side turn detection

Setting `turn_detection_mode` to `VAD` hands turn handling to Speechmatics, which runs server-side VAD. The service requests `ExternalUserTurnStrategies` when it starts, proposes each turn boundary, and lets those strategies resolve it, so `should_interrupt` becomes the control for barge-in.

```python
stt = SpeechmaticsSTTService(
    settings=SpeechmaticsSTTService.Settings(
        # Speechmatics endpoints server-side; no Pipecat VAD needed
        turn_detection_mode=SpeechmaticsSTTService.TurnDetectionMode.VAD,
    ),
)
```

In `VAD` mode, remove any competing `vad_analyzer` or `turn_analyzer` from your transport. A transport VAD is still useful if you want STT metrics, but it must not drive turns.

End-of-utterance timing in `VAD` mode belongs to the service and is not configurable.

## Speaker diarization

Diarization is enabled by default. It labels each transcript segment with one speaker, such as `S1`. The label arrives on the `TranscriptionFrame` as `user_id`. Segments the model cannot attribute are labeled `UU`, and with diarization disabled every segment is labeled `UU`. Agent STT reports one speaker per segment rather than per word, so there is no per-word speaker data.

### Diarization settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `enable_diarization` | boolean \| null | `true` | Attribute each segment to a speaker |
| `speaker_sensitivity` | number \| null | `null` | Speaker detection sensitivity, between `0` and `1`. Higher values help separate similar voices |
| `max_speakers` | number \| null | `null` | Maximum speakers to detect, between `2` and `100`. Unrestricted when unset |
| `prefer_current_speaker` | boolean \| null | `null` | Reduce switching between similar-sounding speakers |
| `known_speakers` | array | `[]` | `SpeakerIdentifier` objects from an earlier session |
| `speaker_active_format` | string | `"{text}"` | Template for speaker output |

### Format speaker labels

`speaker_active_format` folds the speaker label into the transcript text your language model receives.

```python
stt = SpeechmaticsSTTService(
    settings=SpeechmaticsSTTService.Settings(
        enable_diarization=True,
        # Renders as <S1>Good morning.</S1>
        speaker_active_format="<{speaker_id}>{text}</{speaker_id}>",
    ),
)
```

Include the format in your bot's system prompt so the model interprets the labels consistently. Template attributes:

| Attribute | Type | Description | Example |
|---|---|---|---|
| `{speaker_id}` | string | Label of the speaker | `S1` |
| `{text}` | string | Transcribed text | `Good morning.` |
| `{ts}` | float | Start time of the segment, in seconds from the start of the session | `12.34` |
| `{lang}` | string | Language of the transcription | `en` |

### Reuse speaker labels across sessions

Speechmatics assigns speaker labels per session, so the same person is `S1` in one session and something else in the next. Handle the `on_speakers_result` event to collect identifiers, then pass them as `known_speakers` when you build the service for the next session.

```python
@stt.event_handler("on_speakers_result")
async def on_speakers_result(service, speakers):
    # Persist these to reuse the same labels next session
    print(f"Speaker result: {speakers}")
```

Speaker identifiers are unique to your Speechmatics account.

## Connection handling

The service manages its own WebSocket connection. Transient failures trigger reconnection with exponential backoff while audio is buffered. Permanent errors, such as a rejected API key or a configuration agent STT refuses, mark the service unusable rather than retrying.

## Deprecated and unsupported parameters

- `params=SpeechmaticsSTTService.InputParams(...)` is deprecated as of Pipecat 0.0.105. Use `settings=SpeechmaticsSTTService.Settings(...)`, which is also what `STTUpdateSettingsFrame` updates at runtime.
- `operating_point` is a deprecated alias for `model` and is removed in Pipecat 2.0.0. Passing both raises a `ValueError` unless they name the same value.
- The `ADAPTIVE`, `FIXED`, and `SMART_TURN` turn detection modes are gone. Each selected a server-side endpointing strategy that agent STT does not expose. Use `EXTERNAL` or `VAD`.
- `update_params()` no longer changes speaker focus. Use an `STTUpdateSettingsFrame` to change settings at runtime.

The following are no longer settings. Passing any of them to `Settings(...)` raises a `TypeError`. Passing them as a constructor argument is silently ignored, except where noted.

| Parameter | Reason |
|---|---|
| `max_delay` | Transcript timing is the service's own. Warns as a constructor argument |
| `end_of_utterance_silence_trigger` | End-of-utterance timing is the service's own. Warns as a constructor argument |
| `end_of_utterance_max_delay` | End-of-utterance timing is the service's own |
| `split_sentences` | Not exposed by agent STT |
| `focus_speakers`, `ignore_speakers`, `focus_mode` | Agent STT does not support speaker focus |
| `speaker_passive_format` | A segment has no passive case to format |
| `extra_params` | Agent STT rejects configuration fields outside its fixed schema |

## Full STT example

Combines transcription, turn detection, diarization, and speaker formatting in one service.

```python
from pipecat.services.speechmatics.stt import SpeechmaticsSTTService
from pipecat.transcriptions.language import Language

stt = SpeechmaticsSTTService(
    settings=SpeechmaticsSTTService.Settings(
        # Transcription
        language=Language.EN,
        enable_partials=True,

        # Turn detection: a Pipecat VAD closes each turn
        turn_detection_mode=SpeechmaticsSTTService.TurnDetectionMode.EXTERNAL,

        # Diarization
        enable_diarization=True,
        speaker_sensitivity=0.6,
        max_speakers=4,
        prefer_current_speaker=True,

        # Renders each segment as <S1>Good morning.</S1>
        speaker_active_format="<{speaker_id}>{text}</{speaker_id}>",

        # Custom vocabulary
        additional_vocab=[
            SpeechmaticsSTTService.AdditionalVocabEntry(content="Speechmatics"),
            SpeechmaticsSTTService.AdditionalVocabEntry(
                content="Pipecat", sounds_like=["pipe cat"]
            ),
        ],
    ),
)
```

## TTS service

### Install

```bash
pip install "pipecat-ai[speechmatics]~=1.11.0"
```

The TTS page pins `~=1.11.0`, while the quickstart and STT pages pin `~=1.14.0`.

### Usage

```python
import aiohttp

from pipecat.services.speechmatics.tts import SpeechmaticsTTSService

async with aiohttp.ClientSession() as session:
    tts = SpeechmaticsTTSService(
        api_key="YOUR_API_KEY",
        voice_id="sarah",
        aiohttp_session=session,
    )
```

### Configuration

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | string | env var | Speechmatics API key (defaults to `SPEECHMATICS_API_KEY`) |
| `voice_id` | string | `"sarah"` | Voice to use |
| `base_url` | string | service default | Base URL for the Speechmatics TTS endpoint |
| `aiohttp_session` | `aiohttp.ClientSession` | none | Reuse a session for connection pooling and lower latency |

For available voices and detailed TTS options, see `speechmatics:text-to-speech` or https://docs.speechmatics.com/text-to-speech/quickstart.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| No transcripts at all, no error | `EXTERNAL` mode with no VAD in the pipeline. Add a `vad_analyzer` to the transport or user aggregator |
| `TypeError` from `Settings(...)` | A removed setting was passed. See [Deprecated and unsupported parameters](#deprecated-and-unsupported-parameters) |
| `ValueError` at construction | Both `operating_point` and `model` passed with different values |
| Service fails permanently on start | `sample_rate` is not `8000` or `16000`, the API key was rejected, or agent STT refused the configuration |
| Turns fight each other in `VAD` mode | Remove the competing `vad_analyzer` or `turn_analyzer` from the transport |
| Custom `base_url` or `SPEECHMATICS_RT_URL` | Agent STT is served on `/v2/agent`; `/v2` is the streaming endpoint. The docs also say the SDK appends `/agent` when the URL omits it |
| Linden 1 unavailable | Upgrade to Pipecat 1.11.0 or later |
