# Audio events and audio filtering

## Audio events

Docs: https://docs.speechmatics.com/speech-to-text/features/audio-events

Available in Batch and Realtime. Not available in agent STT. Detects and labels non-speech sounds: music, laughter, applause.

### Configuration

`audio_events_config` is a sibling of `transcription_config`. An empty object enables all types.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "audio_events_config": {}
}
```

Request specific types with `types`:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "audio_events_config": {
    "types": ["applause", "music"]
  }
}
```

### Supported events

| Event type | Availability |
|---|---|
| `laughter` | Batch and Realtime |
| `applause` | Batch and Realtime |
| `music` | Batch and Realtime. Realtime audio events can be overly sensitive to music. |
| `silence` | Batch audio event summary only |
| `speech` | Batch audio event summary only |

Only `applause`, `laughter` and `music` can be requested in `types`.

### Batch output

`audio_events` is an array of:

| Field | Description |
|---|---|
| `type` | `applause`, `laughter` or `music`. |
| `start_time` | Seconds from the start of the media. |
| `end_time` | Seconds from the start of the media. |
| `confidence` | Model confidence for the event. |
| `channel` | Only when channel diarization is enabled. |

`audio_event_summary` gives `count` and `total_duration` per event type, including `silence` and `speech`. Speech duration is the sum of the durations of all words spoken. With channel diarization, a `channels` object holds the same summary per channel.

Example from the docs (abridged there; `"format"` is the JSON output version, 2.9 at time of writing, check the docs):

```json
{
  "format": "2.9",
  "job": { ... },
  "metadata": {
    "created_at": "2022-09-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {...},
    "audio_events_config": {},
    ...
  },

  "results": [...],

  "audio_events": [
    {
      "channel": "channel_1",
      "confidence": 0.75,
      "end_time": 21.76,
      "start_time": 19.2,
      "type": "laughter"
    },
    {
      "channel": "channel_1",
      "confidence": 0.76,
      "end_time": 21.76,
      "start_time": 19.2,
      "type": "applause"
    },
    ...
  ],

  "audio_event_summary": {
      "applause": {
        "count": 6,
        "total_duration": 10.24
      },
      "laughter": {
        "count": 6,
        "total_duration": 19.84
      },
      "music": {
        "count": 8,
        "total_duration": 18.96
      },
      "silence": {
        "count": 5,
        "total_duration": 8.34
      },
      "speech": {
        "count": 135,
        "total_duration": 32.38
      }
    },

    "channels": {
      "channel_1": {
        "applause": {
          "count": 3,
          "total_duration": 5.12
        },
          ....
        }
      }
```

The docs example is not valid JSON and its nesting is ambiguous. `spec/batch.yaml` defines `audio_event_summary` as an object with `overall` (summary across all channels, keyed by event type) and `channels` (summary keyed by channel, only with channel diarization). Read the summary defensively: check for an `overall` key before assuming event types sit at the top level.

### Realtime output

Separate messages mark the start and end of each event. Only one event can be active at a time in Realtime: an ongoing `music` event takes precedence over an overlapping `laughter` event that starts later. Another event can be detected only after the terminating `AudioEventEnded`.

```json
{
    "message": "AudioEventStarted",
    "event": {
        "start_time": 4.2,
        "confidence": 0.8,
        "type": "music"
    },
    "channel": "London"
}
```

```json
{
    "message": "AudioEventEnded",
    "event": {
        "end_time": 10.2,
        "type": "music"
    },
    "channel": "London"
}
```

- `confidence` appears only on `AudioEventStarted` and ranges from 0.0 to 1.0.
- `channel` is returned only when `channel` or `channel_and_speaker` diarization is enabled.

### Python: Batch

```python
from speechmatics.models import ConnectionSettings, BatchTranscriptionConfig, AudioEventsConfig
from speechmatics.batch_client import BatchClient

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"

settings = ConnectionSettings(
    url="https://eu1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

with BatchClient(settings) as client:
    job_id = client.submit_job(
        audio=PATH_TO_FILE,
        transcription_config=BatchTranscriptionConfig(audio_events_config=AudioEventsConfig()),
    )
    print(f'Job {job_id} submitted successfully, waiting for analysis')

    # In production, consider using notifications instead of polling
    analysis = client.wait_for_completion(job_id, transcription_format='json-v2')
    print(f"Detected audio event summary: \n{analysis['audio_event_summary']}",)
    print("Detected audio events:")
    for event in analysis["audio_events"]:
        print(f"{event['type']} from {event['start_time']} to {event['end_time']}, confidence: {event['confidence']}")
```

### Python: Realtime

```python
import speechmatics.client
import speechmatics.models
from speechmatics.models import AudioEventsConfig, TranscriptionConfig

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
CONNECTION_URL = "wss://eu.rt.speechmatics.com/v2"

# Create a real-time client
ws = speechmatics.client.WebsocketClient(
    speechmatics.models.ConnectionSettings(
        url=CONNECTION_URL,
        auth_token=API_KEY,
    )
)

config = TranscriptionConfig(audio_events_config=AudioEventsConfig())

# Define an event handler for detected audio events
def handle_audio_event(msg):
    event = msg["event"]
    if msg['message'] == "AudioEventStarted":
        print(f"{event['type']} event started at {event['start_time']}, confidence: {event['confidence']}")
    elif msg['message'] == "AudioEventEnded":
        print(f"{event['type']} event ended at {event['end_time']}")

# Register the event handler for audio events
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AudioEventStarted,
    event_handler=handle_audio_event,
)

ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AudioEventEnded,
    event_handler=handle_audio_event,
)

print("Starting analysis (type Ctrl-C to stop):")

with open(PATH_TO_FILE, 'rb') as fd:
    try:
        ws.run_synchronously(fd, config)
    except KeyboardInterrupt:
        print("\nAnalysis stopped.")
```

### Considerations

- Gaps under 1 second between two occurrences of the same event type merge them into one event. Two music sequences separated by 500 ms are returned as one event.
- Silence is detected only for gaps of at least 1 second with no other event (speech, music, laughter, applause).
- Overlapping events of different types, including speech, can be detected simultaneously (music, applause and speech at once). In Realtime only one event is active at a time, as described above.

### Limitations

- JSON output only.
- Music is detected, but title, artist and genre are not identified.
- Only one instance of an event type is tracked at a time. Consecutive songs with no gap are one `music` event.
- On-prem containers: available only for GPU models.

## Audio filtering

Docs: https://docs.speechmatics.com/speech-to-text/features/audio-filtering

Available in Batch and Realtime. Not available in agent STT. Removes low-volume background speech before transcription, for example other agents in a call center.

### Configuration

`audio_filtering_config` goes inside `transcription_config`.

```json
{
  "type": "transcription",
  "transcription_config": {
    "audio_filtering_config": {
        "volume_threshold": 3.4
    },
    "language": "en",
    "model": "enhanced"
  }
}
```

| Field | Range | Description |
|---|---|---|
| `volume_threshold` | `0` to `100` | Audio below the threshold is not processed. `0` filters nothing; `100` removes all audio. |

### Volume labeling

When audio filtering is configured, each word carries a `volume` value in the range 0 to 100:

```json
    {
      "alternatives": [
        {
          "confidence": 0.99,
          "content": "Hello",
          "language": "en",
        }
      ],
      "end_time": 0.39,
      "start_time": 0.15,
      "volume": 12.34,
      "type": "word"
    },
```

- To get volume labels without filtering, pass an empty object (`{}`) or `"volume_threshold": 0.0`.
- Use the labels as a guide for the threshold, then tune with your own domain-specific audio.

### How it works

1. Audio is converted to raw 16 kHz 16-bit mono and split into 0.01 s chunks.
2. The root mean square amplitude of each chunk is calculated and scaled to 0 to 100.
3. Chunks below the threshold are replaced with silence.

Word volume is a weighted average of the chunk volumes between the word's start and end times. The weighting tries to ignore silence inside long words.

### Caveats

- Background speech must be significantly quieter than foreground speech, or filtering may remove audio that should be transcribed.
- Works better with the Enhanced model, which is more robust to damaged audio.
