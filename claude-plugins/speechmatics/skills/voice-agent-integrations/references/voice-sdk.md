# Voice SDK (deprecated)

Docs: https://docs.speechmatics.com/integrations-and-sdks/voice-sdk

Source: https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/voice

The Voice SDK is deprecated and replaced by agent STT, which provides turn detection, segmentation, and diarization as part of the API rather than in a client library. Start new projects with `speechmatics:agent-stt` (https://docs.speechmatics.com/speech-to-text/agent-stt/quickstart). Use this file only to maintain existing integrations.

## Contents

- [Overview](#overview)
- [Install and quickstart](#install-and-quickstart)
- [Events and segments](#events-and-segments)
- [Presets](#presets)
- [Basic configuration](#basic-configuration)
- [Turn detection](#turn-detection)
- [Segment options](#segment-options)
- [Diarization and speaker management](#diarization-and-speaker-management)
- [Import and export configurations](#import-and-export-configurations)

## Overview

The Voice SDK is a Python library built on top of the Realtime API with features for conversational AI:

- **Intelligent segmentation**: groups words into readable, per-speaker speech segments, so you work with finalized segments rather than stitching word-by-word updates.
- **Turn detection**: detects when a speaker has finished a turn. When a turn is detected, speech is finalized into segments. The sooner a turn is finalized, the sooner you can send a final transcript to an LLM.
- **Speaker management**: focus on or ignore specific speakers, and provide known speakers for speaker identification.
- **Preset configurations**: ready-to-use settings for conversations, note-taking, and captions.

### Voice SDK or Realtime SDK

| Use the Voice SDK when | Use the Realtime SDK when |
|---|---|
| Building conversational AI | You need the raw stream of word-by-word transcription data |
| You need automatic turn detection | Building custom segmentation logic |
| You want speaker-focused transcription | You want fine-grained control over every event |
| You need ready-to-use presets | Processing audio files or custom workflows |

## Install and quickstart

Create an API key in the portal (https://portal.speechmatics.com/settings/api-keys) and store it as a managed secret.

```bash
# Standard installation
pip install speechmatics-voice

# With SMART_TURN (ML-based turn detection)
pip install speechmatics-voice[smart]
```

Stream microphone audio and print finalized segments with speaker ID. `Microphone` is imported from the Realtime SDK (`speechmatics.rt`); install it with `pip install speechmatics-rt`.

```python
import asyncio
import os
from speechmatics.rt import Microphone
from speechmatics.voice import VoiceAgentClient, AgentServerMessageType

async def main():
    """Stream microphone audio to Speechmatics using 'scribe' preset"""

    # Audio configuration
    SAMPLE_RATE = 16000         # Hz
    CHUNK_SIZE = 160            # Samples per read
    PRESET = "scribe"           # Configuration preset

    # Create client with preset
    client = VoiceAgentClient(
        api_key=os.getenv("SPEECHMATICS_API_KEY"),
        preset=PRESET
    )

    # Print finalized segments of speech with speaker ID
    @client.on(AgentServerMessageType.ADD_SEGMENT)
    def on_segment(message):
        for segment in message["segments"]:
            speaker = segment["speaker_id"]
            text = segment["text"]
            print(f"{speaker}: {text}")

    # Setup microphone
    mic = Microphone(SAMPLE_RATE, CHUNK_SIZE)
    if not mic.start():
        print("Error: Microphone not available")
        return

    # Connect to Speechmatics
    await client.connect()

    # Stream microphone audio (interruptible using keyboard)
    try:
        while True:
            audio_chunk = await mic.read(CHUNK_SIZE)
            if not audio_chunk:
                break  # Microphone stopped producing data
            await client.send_audio(audio_chunk)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

Client methods shown in the docs: `VoiceAgentClient(api_key=..., preset=...)` or `VoiceAgentClient(api_key=..., config=...)`, `client.on(event)`, `await client.connect()`, `await client.send_audio(chunk)`, `client.finalize()`, `await client.disconnect()`.

If no configuration or preset is provided, the client defaults to the `external` preset.

## Events and segments

| Event | Meaning |
|---|---|
| `AgentServerMessageType.ADD_PARTIAL_SEGMENT` | Interim results that stream as speech is recognized. Each new partial replaces the previous one |
| `AgentServerMessageType.ADD_SEGMENT` | Final results emitted when a turn ends. Use this for downstream processing such as sending to an LLM |

```text
Speaking: "Hello, how are you?"

Timeline:
  ADD_PARTIAL_SEGMENT: "Hello"
  ADD_PARTIAL_SEGMENT: "Hello, how"
  ADD_PARTIAL_SEGMENT: "Hello, how are"
  ADD_PARTIAL_SEGMENT: "Hello, how are you"
  (turn detected or finalize() called)
  ADD_SEGMENT: "Hello, how are you?"  <- Use this
```

Final segments are emitted when:

1. Turn detection triggers automatically (based on your preset or config).
2. You call `client.finalize()` manually (when using the `external` preset). This signals the Speechmatics servers to finalize the current speech immediately.

### Segment payload

Example `ADD_SEGMENT` payload:

```json
{
  "message": "AddSegment",
  "segments": [
    {
      "speaker_id": "S1",
      "is_active": true,
      "timestamp": "2025-11-11T23:18:37.189+00:00",
      "language": "en",
      "text": "Welcome to Speechmatics.",
      "metadata": {
        "start_time": 1.28,
        "end_time": 8.04
      }
    }
  ],
  "metadata": {
    "start_time": 1.28,
    "end_time": 8.04,
    "processing_time": 0.187
  }
}
```

| Field | Meaning |
|---|---|
| `speaker_id` | Speaker label (`S1`, `S2`, or a custom label if using known speakers) |
| `is_active` | Whether this speaker is in your focus list |
| `timestamp` | Absolute wall-clock time (ISO 8601) |
| `start_time` / `end_time` | Seconds relative to the start of the session |
| `processing_time` | Transcription latency in seconds |

### Subscribe to events

```python
@client.on(AgentServerMessageType.ADD_SEGMENT)
def on_final_segment(message):
    for segment in message["segments"]:
        print(f"[FINAL] {segment['speaker_id']}: {segment['text']}")

@client.on(AgentServerMessageType.ADD_PARTIAL_SEGMENT)
def on_partial_segment(message):
    for segment in message["segments"]:
        print(f"[PARTIAL] {segment['speaker_id']}: {segment['text']}")
```

## Presets

| Preset | Purpose |
|---|---|
| `FAST` | Low latency, fast responses |
| `FIXED` | General conversation with fixed, silence-based turn detection |
| `ADAPTIVE` | General conversation with adaptive timing |
| `SMART_TURN` | Complex conversation with ML-enhanced turn detection |
| `EXTERNAL` | User handles end of turn |
| `SCRIBE` | Note-taking |
| `CAPTIONS` | Live captioning |

List all available presets:

```python
presets = VoiceAgentConfigPreset.list_presets()
```

Presets include defaults for all settings (language defaults to English). To change the language or any other setting, use a custom configuration, or use a preset as a starting point and customize it with an overlay.

Pass a preset to the client by name (`preset="scribe"` in the quickstart) or build a config from `VoiceAgentConfigPreset.<NAME>(...)`. Preset name strings other than `"scribe"` and `"external"` are not confirmed by the docs page; call `VoiceAgentConfigPreset.list_presets()` to get the exact names for your SDK version.

### Custom configuration

```python
import os
from speechmatics.voice import VoiceAgentClient, VoiceAgentConfig, EndOfUtteranceMode

config = VoiceAgentConfig(
    language="en",
    enable_diarization=True,
    max_delay=0.7,
    end_of_utterance_mode=EndOfUtteranceMode.ADAPTIVE,
)

client = VoiceAgentClient(api_key=os.getenv("YOUR_API_KEY"), config=config)
```

### Preset with a custom overlay

```python
from speechmatics.voice import VoiceAgentConfigPreset, VoiceAgentConfig

# Use preset with custom overrides
config = VoiceAgentConfigPreset.SCRIBE(
    VoiceAgentConfig(
        language="es",
        max_delay=0.8
    )
)
```

## Basic configuration

All options are fields of `VoiceAgentConfig`.

| Option | Type | Default | Description |
|---|---|---|---|
| `language` | str | `"en"` | Language code for transcription (for example `"en"`, `"es"`, `"fr"`) |
| `output_locale` | str | `None` | Output locale for formatting (for example `"en-GB"`, `"en-US"`) |
| `operating_point` | OperatingPoint | `ENHANCED` | Accuracy level: `STANDARD` or `ENHANCED` |
| `domain` | str | `None` | Domain-specific model (for example `"finance"`, `"medical"`) |
| `additional_vocab` | list[AdditionalVocabEntry] | `[]` | Custom vocabulary for domain-specific terms |
| `punctuation_overrides` | dict | `None` | Custom punctuation rules. Keys are punctuation marks, values are replacement strings |
| `sample_rate` | int | `16000` | Audio sample rate in Hz |
| `audio_encoding` | AudioEncoding | `PCM_S16LE` | Audio encoding format |
| `max_delay` | float | `1.0` | Maximum transcription delay in seconds for word emission. Turn detection ensures finalization latency is not affected |
| `enable_diarization` | bool | `False` | Enable speaker diarization. When enabled, segments include a `speaker_id` field (for example `S1`, `S2`) |

Languages and locales: https://docs.speechmatics.com/speech-to-text/languages

### Custom vocabulary

```python
from speechmatics.voice import AdditionalVocabEntry, VoiceAgentConfig

config = VoiceAgentConfig(
    language="en",
    additional_vocab=[
        AdditionalVocabEntry(
            content="Speechmatics",
            sounds_like=["speech matters", "speech matics"]
        ),
        AdditionalVocabEntry(content="API"),
    ]
)
```

### Basic configuration example

```python
from speechmatics.voice import (
    AdditionalVocabEntry,
    AudioEncoding,
    OperatingPoint,
    VoiceAgentConfig,
    VoiceAgentConfigPreset,
)

overrides = VoiceAgentConfig(
    # Language and locale
    language="en",  # e.g. "en", "es", "fr"
    output_locale=None,  # e.g. "en-GB", "en-US"

    # Model selection
    operating_point=OperatingPoint.ENHANCED,  # STANDARD or ENHANCED
    domain=None,  # e.g. "finance", "medical"

    # Vocabulary
    additional_vocab=[
        AdditionalVocabEntry(
            content="Speechmatics",
            sounds_like=["speech matters", "speech matics"],
        ),
        AdditionalVocabEntry(content="API"),
    ],
    punctuation_overrides=None,

    # Audio
    sample_rate=16000,
    audio_encoding=AudioEncoding.PCM_S16LE,

    # Diarization
    enable_diarization=True,
)

config = VoiceAgentConfigPreset.ADAPTIVE(overrides)
```

## Turn detection

Presets configure turn detection under the hood. When a turn is detected (or you call `client.finalize()` using the `external` preset), the SDK signals the servers so the final transcript returns as quickly as possible. This works in multi-speaker scenarios, including when diarization is enabled.

| Option | Type | Default | Description |
|---|---|---|---|
| `end_of_utterance_mode` | EndOfUtteranceMode | `FIXED` | Base strategy for detecting turn endings |
| `end_of_utterance_silence_trigger` | float | `0.5` | Silence duration in seconds to trigger turn end |
| `end_of_utterance_max_delay` | float | `10.0` | Maximum delay before forcing turn end |
| `vad_config` | VoiceActivityConfig | `None` | Voice activity detection settings |
| `smart_turn_config` | SmartTurnConfig | `None` | ML model that detects acoustic turn-taking cues (intonation, rhythm patterns) on top of the base mode |

`EndOfUtteranceMode` values:

- `FIXED`: fixed silence threshold. Fast but may split slow speech.
- `ADAPTIVE`: adjusts delay based on speech rate, pauses, and disfluencies. Best for natural conversation.
- `EXTERNAL`: manual control via `client.finalize()`. For custom turn logic.

`VoiceActivityConfig` fields:

| Field | Type | Default | Description |
|---|---|---|---|
| `enabled` | bool | `False` | Enable VAD |
| `silence_duration` | float | `0.18` | Seconds of silence before considering speech ended |
| `threshold` | float | `0.35` | Sensitivity threshold for detecting speech |

### Smart turn

Smart turn can be combined with `FIXED` or `ADAPTIVE` modes, but not with `EXTERNAL` mode. Requires the `[smart]` extras: `pip install speechmatics-voice[smart]`.

```python
from speechmatics.voice import (
    EndOfUtteranceMode,
    SmartTurnConfig,
    VoiceAgentConfig,
    VoiceAgentConfigPreset,
)

# ADAPTIVE mode + ML-enhanced turn detection
config = VoiceAgentConfig(
    end_of_utterance_mode=EndOfUtteranceMode.ADAPTIVE,
    smart_turn_config=SmartTurnConfig(enabled=True),
)

# Or use the SMART_TURN preset which bundles this configuration
config = VoiceAgentConfigPreset.SMART_TURN()
```

## Segment options

Output:

| Option | Type | Default | Description |
|---|---|---|---|
| `include_partials` | bool | `True` | Emit partial segments via `ADD_PARTIAL_SEGMENT`. Set to `False` for final-only output |
| `include_results` | bool | `False` | Include word-level timing data in segments |
| `transcription_update_preset` | TranscriptionUpdatePreset | `COMPLETE` | Controls when partial segment updates are emitted. Options: `COMPLETE`, `COMPLETE_PLUS_TIMING`, `WORDS`, `WORDS_PLUS_TIMING`, `TIMING` |

Generation, via `speech_segment_config` (SpeechSegmentConfig, default `SpeechSegmentConfig()`):

| Field | Type | Default | Description |
|---|---|---|---|
| `add_trailing_eos` | bool | `False` | Append end-of-sentence markers to segments that are missing them |
| `emit_sentences` | bool | `True` | Emit a finalized segment as soon as a sentence ends. If a speaker continues during a turn, multiple segments may be emitted |
| `pause_mark` | Optional[str] | `None` | Insert a custom string when pauses are detected (for example `"..."` produces `"Hello ... how are you?"`) |

## Diarization and speaker management

Set `enable_diarization=True` to use any option in this section.

| Option | Type | Default | Description |
|---|---|---|---|
| `enable_diarization` | bool | `False` | Enable speaker diarization |
| `speaker_sensitivity` | float | `0.5` | Diarization sensitivity between 0.0 and 1.0. Higher values detect more speakers |
| `max_speakers` | int | `None` | Limit the maximum number of speakers to detect |
| `prefer_current_speaker` | bool | `False` | Give extra weight to the current speaker for word grouping |
| `speaker_config` | SpeakerFocusConfig | `SpeakerFocusConfig()` | Speaker focus and ignore rules |
| `known_speakers` | list[SpeakerIdentifier] | `[]` | Pre-enrolled speaker identifiers for speaker identification |

### Speaker focus

| Speaker type | Definition | Segment flag |
|---|---|---|
| Active | In your `focus_speakers` list. With no `focus_speakers` configured, all detected speakers are active | `is_active: true` |
| Passive | Not in `focus_speakers` but still included in output when using `SpeakerFocusMode.RETAIN` | `is_active: false` |
| Ignored | Completely excluded from output. Their speech does not appear in segments and does not trigger turn detection | none |

`SpeakerFocusMode` values:

- `RETAIN`: non-focused speakers are kept in output as passive speakers. Use to prioritize certain speakers but still see what others say.
- `IGNORE`: non-focused speakers are excluded entirely. Use when you only care about specific speakers.

```python
from speechmatics.voice import SpeakerFocusConfig, SpeakerFocusMode, VoiceAgentConfig

# Focus on specific speakers, keep others as passive
config = VoiceAgentConfig(
    enable_diarization=True,
    speaker_config=SpeakerFocusConfig(
        focus_speakers=["S1", "S2"],
        focus_mode=SpeakerFocusMode.RETAIN
    )
)

# Focus on specific speakers, exclude everyone else
config = VoiceAgentConfig(
    enable_diarization=True,
    speaker_config=SpeakerFocusConfig(
        focus_speakers=["S1", "S2"],
        focus_mode=SpeakerFocusMode.IGNORE
    )
)

# Blacklist specific speakers (exclude them from all processing)
config = VoiceAgentConfig(
    enable_diarization=True,
    speaker_config=SpeakerFocusConfig(
        ignore_speakers=["S3"],
    )
)
```

Route segments by `is_active` in the event handler:

```python
@client.on(AgentServerMessageType.ADD_SEGMENT)
def on_segment(message):
    for segment in message["segments"]:
        if segment["is_active"]:
            process_focused_speaker(segment["text"])
        else:
            process_passive_speaker(segment["speaker_id"], segment["text"])
```

### Known speakers

```python
from speechmatics.voice import SpeakerIdentifier, VoiceAgentConfig

config = VoiceAgentConfig(
    enable_diarization=True,
    known_speakers=[
        SpeakerIdentifier(label="Alice", speaker_identifiers=["XX...XX"]),
        SpeakerIdentifier(label="Bob", speaker_identifiers=["YY...YY"])
    ]
)
```

### Advanced configuration example

```python
from speechmatics.voice import (
    EndOfUtteranceMode,
    SpeakerFocusConfig,
    SpeakerFocusMode,
    SpeakerIdentifier,
    VoiceAgentConfig,
    VoiceAgentConfigPreset,
)

overrides = VoiceAgentConfig(
    end_of_utterance_mode=EndOfUtteranceMode.ADAPTIVE,
    enable_diarization=True,
    speaker_config=SpeakerFocusConfig(
        focus_speakers=["S1"],
        focus_mode=SpeakerFocusMode.RETAIN,
    ),
    known_speakers=[
        SpeakerIdentifier(label="Alice", speaker_identifiers=["XX...XX"]),
    ],
)

config = VoiceAgentConfigPreset.ADAPTIVE(overrides)
```

## Import and export configurations

```python
from speechmatics.voice import VoiceAgentConfigPreset, VoiceAgentConfig

# Export preset to JSON
config_json = VoiceAgentConfigPreset.SCRIBE().to_json()

# Load from JSON
config = VoiceAgentConfig.from_json(config_json)

# Or create from JSON string
config = VoiceAgentConfig.from_json('{"language": "en", "enable_diarization": true}')
```

## Migrating to agent STT

Agent STT does not support speaker focus (`focus_speakers`, `ignore_speakers`, `focus_mode`), `max_delay`, `punctuation_overrides`, or configurable end-of-utterance timing, and it replaces the `FIXED`, `ADAPTIVE`, and `SMART_TURN` strategies with two turn detection modes. This is documented for the LiveKit and Pipecat integrations in [livekit.md](livekit.md) and [pipecat.md](pipecat.md); for the agent STT API itself, use `speechmatics:agent-stt`.
