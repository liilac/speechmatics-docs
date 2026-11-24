# Realtime diarization and speaker identification

Docs:

- Realtime diarization: https://docs.speechmatics.com/speech-to-text/realtime/realtime-diarization
- Realtime speaker identification: https://docs.speechmatics.com/speech-to-text/realtime/speaker-identification

For diarization and speaker identification as general features (including Batch), see `speechmatics:transcription-features`.

## Contents

- [Modes](#modes)
- [Speaker diarization](#speaker-diarization)
- [Channel diarization](#channel-diarization)
- [Channel and speaker diarization](#channel-and-speaker-diarization)
- [Closing channels](#closing-channels)
- [Tuning speaker diarization](#tuning-speaker-diarization)
- [speaker_diarization_config reference](#speaker_diarization_config-reference)
- [Speaker identification](#speaker-identification)
- [On-prem](#on-prem)

## Modes

Set `transcription_config.diarization`:

| Value | Behavior | Use when |
| --- | --- | --- |
| `none` (default) | No speaker labels. | |
| `speaker` | Identifies each speaker by voice. | Multiple speakers share one audio stream. |
| `channel` | Transcribes each audio channel separately. | Each speaker is recorded on their own channel. |
| `channel_and_speaker` | Transcribes each channel separately and identifies unique speakers within each channel. | Multiple speakers are present across multiple channels. |

## Speaker diarization

Picks out different speakers from the audio stream by acoustic matching.

The `"type": "transcription"` wrapper in the snippets in this file is as shown in the docs; `StartRecognition` itself has no `type` field, so send only the `transcription_config` part. See [configuration.md](configuration.md).

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker"
  }
}
```

Each `word` and `punctuation` result then carries a `speaker` property in its alternative:

- `S#`: `S` for speaker, `#` a sequential number. `S1` appears first in the results, then `S2`, `S3`, and so on.
- `UU`: the speaker cannot be identified or diarization is not applied, for example when background noise is transcribed as speech but no speaker can be determined.

```json
"results": [
  {
    "alternatives": [
      { "confidence": 0.93, "content": "hello", "language": "en", "speaker": "S1" }
    ]
  },
  {
    "alternatives": [
      { "confidence": 1.0, "content": "hi", "language": "en", "speaker": "S2" }
    ]
  }
]
```

## Channel diarization

Processes audio with multiple channels and returns a separate transcript for each. This gives perfect speaker separation at the channel level and more accurate handling of cross-talk.

Set `diarization` to `channel` and provide a label per channel in `channel_diarization_labels`:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "channel",
    "channel_diarization_labels": ["New_York", "Shanghai"]
  }
}
```

`RecognitionStarted` lists the requested channels:

```json
{
  "message": "RecognitionStarted",
  "channels": ["New_York", "Shanghai"]
}
```

The diarization page shows this field as `channels`; the API schema names it `channel_ids`. Handle both.

### Send audio to a channel

Send `AddChannelAudio` with the audio base64-encoded:

```json
{
  "message": "AddChannelAudio",
  "channel": "New_York",
  "data": "<base64-encoded audio>"
}
```

The server acknowledges with `ChannelAudioAdded`, carrying a sequence number for that channel:

```json
{
  "message": "ChannelAudioAdded",
  "channel": "New_York",
  "seq_no": 10
}
```

### Transcript response

Transcripts are returned independently for each channel. The `channel` property identifies the channel:

```json
{
  "message": "AddTranscript",
  "channel": "New_York",
  "results": [
    {
      "type": "word",
      "start_time": 1.45,
      "end_time": 1.8,
      "alternatives": [{
        "language": "en",
        "content": "Hello,",
        "confidence": 0.98
      }]
    }
  ]
}
```

The `channel` property is returned on `AddTranscript` and `AddPartialTranscript` only. Translation messages do not currently include it; contact [Support](https://support.speechmatics.com) to request this.

`ForceEndOfUtterance` accepts a `channel` field, and `EndOfUtterance`, `AudioEventStarted`, and `AudioEventEnded` can carry `channel` in multichannel sessions.

## Channel and speaker diarization

Splits transcripts per channel and also separates individual speakers in each channel. Set `diarization` to `channel_and_speaker`, provide `channel_diarization_labels`, and send audio with `AddChannelAudio` as for channel diarization.

```json
{
  "message": "AddTranscript",
  "channel": "New_York",
  "results": [
    {
      "alternatives": [{ "content": "Hello", "confidence": 0.98, "speaker": "S1" }]
    },
    {
      "alternatives": [{ "content": "Hi", "confidence": 0.98, "speaker": "S2" }]
    }
  ]
}
```

Speaker labels are specific to a channel. `S1` on one channel is not necessarily the same speaker as `S1` on another.

## Closing channels

Signal that a channel is finished with `EndOfChannel`:

```json
{
  "message": "EndOfChannel",
  "channel": "New_York",
  "last_seq_no": 2564
}
```

The channel then stops accepting or processing data. When all channels are closed, the session ends.

Alternatively send `EndOfStream` to close all channels at once.

Closing an individual channel currently has no impact on pricing.

### Channel limits

- SaaS: maximum 2 channels.
- On-prem containers: the maximum depends on the multi-session container's maximum number of connections.
- The Speechmatics Python client CLI can transcribe multichannel audio from files only, not from streaming or raw audio.

## Tuning speaker diarization

All settings live in `transcription_config.speaker_diarization_config`.

### Speaker sensitivity

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "speaker_sensitivity": 0.6
    }
  }
}
```

A value between 0 and 1, default 0.5. Higher sensitivity increases the likelihood of more unique speakers being returned.

### Prefer current speaker

```json
"speaker_diarization_config": {
  "prefer_current_speaker": true
}
```

Default `false`. When `true`, the system stays with the speaker of the previous word if they closely match the speaker of the new word. This reduces incorrect switching between similar-sounding speakers, but some shorter speaker turn changes between similar speakers may be missed.

### Max speakers

```json
{
  "message": "StartRecognition",
  "audio_format": {
    "type": "raw",
    "encoding": "pcm_f32le",
    "sample_rate": 48000
  },
  "transcription_config": {
    "language": "en",
    "model": "enhanced",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "max_speakers": 10
    }
  }
}
```

By default there is no limit on the number of speakers. When set, `max_speakers` can be any integer greater than or equal to 2.

### Punctuation

Speaker diarization uses punctuation to improve accuracy. Small corrections are applied to speaker labels based on sentence boundaries. For example, if 9 words of a sentence are assigned to S1 and 1 word to S2, the lone S2 word may be corrected to S1.

This only works when punctuation is enabled. Disabling punctuation through `punctuation_overrides.permitted_marks` can reduce diarization accuracy. Adjusting punctuation sensitivity can also affect speaker accuracy.

### Speaker change (legacy)

Speaker Change Detection was removed in July 2024. The `speaker_change` and `channel_and_speaker_change` parameters are no longer supported. Use speaker diarization instead.

## speaker_diarization_config reference

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `max_speakers` | integer, minimum 2 | no limit | Maximum number of speakers to detect. With speaker identification, applies only to generic (non-enrolled) speakers. |
| `prefer_current_speaker` | boolean | `false` | Reduces the likelihood of incorrectly switching between similar-sounding speakers. |
| `speaker_sensitivity` | number, 0 to 1 | 0.5 | Higher values increase the likelihood of more unique speakers. With speaker identification, lower values make a match to enrolled speakers more likely. |
| `get_speakers` | boolean | | If `true`, speaker identifiers are returned at the end of the transcript. Not supported by Melia 1 and Oak 1. |
| `speakers` | array | | Speaker labels linked to their identifiers. Maximum 50 speaker identifiers across all speakers. Not supported by Melia 1 and Oak 1. |

Each item in `speakers`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `label` | string, minimum length 1 | Yes | Must not match the internal format (`S1`, `S2`, ..., `UU`) and must not start or end with whitespace. |
| `speaker_identifiers` | array of unique strings, at least one | Yes | Identifiers obtained from `SpeakersResult`. |

## Speaker identification

Realtime speaker identification is not supported by Melia 1 and Oak 1.

### Enrollment

Run a transcription with speaker diarization enabled on an audio sample where the speaker is ideally speaking alone. Then obtain identifiers in one of two ways.

Option 1, recommended for enrollment: set `get_speakers` in the config. The engine sends the identifiers automatically once transcription is complete, equivalent to `GetSpeakers` with `final: true`.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "get_speakers": true
    }
  }
}
```

Option 2: send a `GetSpeakers` message.

```json
{
  "message": "GetSpeakers",
  "final": true
}
```

- `final: false` (default): returns identifiers generated up to the point of the request. To avoid empty results, wait until the server has sent at least one `AddTranscript` before sending.
- `final: true`: waits until the end of the stream and returns identifiers based on all audio.

If `get_speakers` is absent or `false`, an explicit `GetSpeakers` with `final: true` still works and takes precedence: the engine returns identifiers at the end of the transcription.

The server replies with `SpeakersResult`:

```json
{
  "message": "SpeakersResult",
  "speakers": [
    {"label": "S1", "speaker_identifiers": ["<id1>"]},
    {"label": "S2", "speaker_identifiers": ["<id2>"]}
  ]
}
```

### Identification

Provide stored identifiers in a later session through `speaker_diarization_config.speakers`:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "speakers": [
        {"label": "Alice", "speaker_identifiers": ["<alice_id1>", "<alice_id2>"]},
        {"label": "Bob", "speaker_identifiers": ["<bob_id1>"]}
      ],
      "speaker_sensitivity": 0.4
    }
  }
}
```

Words from enrolled speakers are tagged with the provided labels; any other speaker keeps an internal label:

```json
{
  "results": [
    { "alternatives": [{ "confidence": 1.0, "content": "Hello", "language": "en", "speaker": "Alice" }] },
    { "alternatives": [{ "confidence": 1.0, "content": "Hi", "language": "en", "speaker": "S1" }] },
    { "alternatives": [{ "confidence": 1.0, "content": "Nice", "language": "en", "speaker": "Bob" }] }
  ]
}
```

All speaker diarization options work with speaker identification:

- `max_speakers` applies only to generic (non-enrolled) speakers. If it is 10 and 10 speakers are enrolled, the system can still add up to 10 generic speakers.
- `speaker_sensitivity` adjusts how strongly the system prefers enrolled speakers over detecting new generic ones. Lower values make it more likely to match enrolled speakers.
- Issues are reported with a `Warning` of type `speaker_id`.

### Python example: enrollment

Uses the `speechmatics-python` package (`pip3 install speechmatics-python`).

```python
import asyncio
import speechmatics
import speechmatics.models
import speechmatics.client
from speechmatics.client import (
    ServerMessageType,
    ClientMessageType
)

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"
CONNECTION_URL = "wss://eu.rt.speechmatics.com/v2"

async def enroll_speakers():
    handler_tasks: list[asyncio.Task] = []

    transcription_config = speechmatics.models.TranscriptionConfig(**{
            "model": "enhanced",
            "language": LANGUAGE,
            "diarization": "speaker",
        }
    )

    # Create a transcription client
    client = speechmatics.client.WebsocketClient(
        speechmatics.models.ConnectionSettings(
            url=CONNECTION_URL,
            auth_token=API_KEY,
        )
    )
    # Register the event handler for RecognitionStarted
    # to send the GetSpeakers(final=True) request
    client.add_event_handler(
        ServerMessageType.RecognitionStarted,
        lambda _: handler_tasks.append(
            asyncio.create_task(client.send_message(ClientMessageType.GetSpeakers, {"final": True}))
        ),
    )
    # Register the event handler for SpeakersResult
    # to print the speaker identifiers obtained from the server
    client.add_event_handler(
        ServerMessageType.SpeakersResult,
        lambda message: print(f"[speaker identifiers] {message['speakers']}"),
    )

    with open(PATH_TO_FILE, "rb") as fh:
        await asyncio.create_task(client.run(fh, transcription_config))

    for task in handler_tasks:
        await task

if __name__ == "__main__":
    asyncio.run(enroll_speakers())
```

### Python example: identification

```python
import asyncio
import speechmatics
import speechmatics.models
import speechmatics.client
from speechmatics.client import ServerMessageType

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"
CONNECTION_URL = "wss://eu.rt.speechmatics.com/v2"

async def identify_speakers():
    handler_tasks: list[asyncio.Task] = []

    transcription_config = speechmatics.models.TranscriptionConfig(**{
            "model": "enhanced",
            "language": LANGUAGE,
            "diarization": "speaker",
            "speaker_diarization_config": {
                # add your speaker identifiers
                "speakers": [
                    {"label": "Alice", "speaker_identifiers": ["<alice_id1>", "<alice_id2>"]},
                    {"label": "Bob", "speaker_identifiers": ["<bob_id1>"]},
                ]
            }
        }
    )
    # Create a transcription client
    client = speechmatics.client.WebsocketClient(
        speechmatics.models.ConnectionSettings(
            url=CONNECTION_URL,
            auth_token=API_KEY,
        )
    )
    # Optionally, add transcript handler
    client.add_event_handler(
        ServerMessageType.AddTranscript,
        lambda message: print(f"[transcript] {message['results']}"),
    )

    with open(PATH_TO_FILE, "rb") as fh:
        await asyncio.create_task(client.run(fh, transcription_config))

    for task in handler_tasks:
        await task


if __name__ == "__main__":
    asyncio.run(identify_speakers())
```

## On-prem

To run `channel` or `channel_and_speaker` diarization on-prem:

- Use a GPU Speech to Text container. Handling multiple audio streams is computationally intensive and benefits from GPU acceleration.
- Set the `SM_MAX_CONCURRENT_CONNECTIONS` environment variable to match the number of channels to process.

See `speechmatics:container-deployment` for container setup.
