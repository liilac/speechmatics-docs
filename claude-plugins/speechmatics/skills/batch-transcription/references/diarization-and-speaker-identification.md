# Batch diarization and speaker identification

Docs: https://docs.speechmatics.com/speech-to-text/batch/batch-diarization and https://docs.speechmatics.com/speech-to-text/batch/speaker-identification

For diarization as a feature across products, use `speechmatics:transcription-features`. This file covers the Batch API specifics.

| Mode | `diarization` value | Use when |
|---|---|---|
| Speaker diarization | `speaker` | Multiple speakers share one audio stream. Speakers are separated by voice |
| Channel diarization | `channel` | Each speaker is recorded on their own channel |
| Off (default) | `none` | |

## Speaker diarization

All audio channels are aggregated into a single stream, and speakers are picked out by acoustic matching. Disabled by default.

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

Each `word` and `punctuation` result gets a `speaker` property inside `alternatives`:

- `S#`: `S` for speaker and a sequential number. `S1` appears first in the results, then `S2`, `S3`, and so on.
- `UU`: the speaker cannot be identified or diarization is not applied, for example background noise transcribed as speech.

```json
"results": [
  {
    "alternatives": [
      {
        "confidence": 0.93,
        "content": "hello",
        "language": "en",
        "speaker": "S1"
      }
    ]
  },
  {
    "alternatives": [
      {
        "confidence": 1.0,
        "content": "hi",
        "language": "en",
        "speaker": "S2"
      }
    ]
  }
]
```

## Channel diarization

Each channel is transcribed on its own and merged into a single transcript. This gives perfect separation at channel level and cleaner results when speakers overlap. Batch channel diarization supports up to 100 separate input files.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "channel",
    "channel_diarization_labels": ["Agent", "Caller"]
  }
}
```

- Without labels, default names such as `Channel 1` are used.
- The number of labels should match the number of channels. Extra labels are ignored.
- Each label must match `^[A-Za-z0-9._]+$`.

Each result carries a top-level `channel` property:

```json
"results": [
  {
    "type": "word",
    "end_time": 1.8,
    "start_time": 1.45,
    "channel": "Agent",
    "alternatives": [
      {
        "language": "en",
        "content": "Hello",
        "confidence": 0.76
      }
    ]
  }
]
```

## Speaker diarization configuration

All settings go in `transcription_config.speaker_diarization_config`.

| Field | Type | Default | Effect |
|---|---|---|---|
| `speaker_sensitivity` | number, 0 to 1 | `0.5` | Higher values increase the likelihood of more unique speakers. Lower values combine similar speakers and may give fewer speakers |
| `prefer_current_speaker` | boolean | `false` | When `true`, stays with the speaker of the previous word if they closely match the speaker of the new word. Reduces false switches between similar voices; shorter turn changes between similar speakers may be missed |
| `get_speakers` | boolean | | Returns speaker identifiers at the end of the transcript. Not supported by Melia 1 and Oak 1 |
| `speakers` | array | | Known speakers to identify. Not supported by Melia 1 and Oak 1 |

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker",
    "speaker_diarization_config": {
      "speaker_sensitivity": 0.6,
      "prefer_current_speaker": true
    }
  }
}
```

### Punctuation

Speaker diarization uses punctuation to improve accuracy. Small corrections are applied to speaker labels based on sentence boundaries: if 9 words in a sentence are assigned to S1 and 1 word to S2, the lone S2 word may be corrected to S1.

This only works when punctuation is enabled. Disabling punctuation with `permitted_marks` in `punctuation_overrides` can reduce diarization accuracy. Adjusting punctuation sensitivity can also affect how accurately speakers are identified.

### Removed: speaker change

Speaker change detection was removed in July 2024. The `speaker_change` and `channel_and_speaker_change` values are no longer supported. Use speaker diarization.

### Processing time

Diarization typically increases overall processing time by 10-50%.

## Speaker identification

Batch speaker identification is not supported by Melia 1 and Oak 1.

Two steps: enroll a speaker to get identifiers, then pass the identifiers in later jobs.

### 1. Enrollment

Run a speaker diarization job on a sample where the speaker is ideally speaking alone, with `get_speakers` set:

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

The `json-v2` transcript includes a top-level `speakers` array:

```json
{
  "results": [
    {
      "alternatives": [
        { "confidence": 0.93, "content": "Hello", "language": "en", "speaker": "S1" }
      ]
    },
    {
      "alternatives": [
        { "confidence": 1.0, "content": "Hi", "language": "en", "speaker": "S2" }
      ]
    }
  ],
  "speakers": [
    {
      "label": "S1",
      "speaker_identifiers": ["<id1>"]
    },
    {
      "label": "S2",
      "speaker_identifiers": ["<id2>"]
    }
  ]
}
```

Store the `speaker_identifiers` values against your own speaker records.

### 2. Identification

Pass known speakers in `speaker_diarization_config.speakers`:

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

Rules:

- Each item needs `label` (at least 1 character) and `speaker_identifiers` (at least 1, unique).
- `label` must not match the internal format (`S1`, `S2`, and so on).
- A maximum of 50 speaker identifiers across all speakers can be provided.
- A speaker can have several identifiers.
- All other speaker diarization options remain supported.
- `speaker_sensitivity` adjusts how strongly the system prefers enrolled speakers over detecting new generic ones. Lower values make a match to an enrolled speaker more likely.

Words from known speakers are tagged with your labels. Other speakers keep internal labels:

```json
{
  "results": [
    {
      "alternatives": [
        { "confidence": 0.93, "content": "Morning", "language": "en", "speaker": "Alice" }
      ]
    },
    {
      "alternatives": [
        { "confidence": 0.93, "content": "Hi", "language": "en", "speaker": "S1" }
      ]
    },
    {
      "alternatives": [
        { "confidence": 1.0, "content": "Morning", "language": "en", "speaker": "Bob" }
      ]
    }
  ]
}
```
