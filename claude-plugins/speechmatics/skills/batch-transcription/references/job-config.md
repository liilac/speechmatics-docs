# Job config and input

Docs: https://docs.speechmatics.com/speech-to-text/batch/input

Configure a job by passing a JSON string in the `config` form field of `POST /jobs`. Send the audio in the `data_file` form field, or point to it with `fetch_data`.

## Supported file types

Exhaustive list. Any other format is not supported.

`wav`, `mp3`, `aac`, `ogg`, `mpeg`, `amr`, `m4a`, `mp4`, `flac`

- The type must be determinable by data inspection. Raw audio where the codec is not embedded in the file cannot be processed in batch mode, including files with extensions such as `.raw` or `.g729`.
- The optimal format for speed is 16-bit 16 kHz mono WAV. It needs no preprocessing, which matters most for very short files.
- A file uploaded in the request body must be under 1 GB. Use `fetch_data` for larger files.

## `JobConfig`

| Field | Type | Notes |
|---|---|---|
| `type` | string, required | `transcription` |
| `transcription_config` | object | Required for transcription jobs. See below |
| `fetch_data` | object | `url` (required), `auth_headers` (array of strings) |
| `fetch_text` | object | Same shape as `fetch_data`. Used by alignment; see [alignment.md](alignment.md) |
| `notification_config` | array | List of callbacks. See [notifications.md](notifications.md) |
| `tracking` | object | Your own metadata. See [Tracking metadata](#tracking-metadata) |
| `output_config` | object | `srt_overrides.max_line_length`, `srt_overrides.max_lines`. See [output.md](output.md) |
| `language_identification_config` | object | See [language-identification.md](language-identification.md) |
| `translation_config` | object | `target_languages` (required, array, max 5 items). See `speechmatics:transcription-features` |
| `audio_events_config` | object | `types` (array of strings). See `speechmatics:transcription-features` |
| `summarization_config` | object | See `speechmatics:speech-intelligence` |
| `sentiment_analysis_config` | object | See `speechmatics:speech-intelligence` |
| `topic_detection_config` | object | See `speechmatics:speech-intelligence` |
| `auto_chapters_config` | object | See `speechmatics:speech-intelligence` |

No assumptions should be made about the order in which `notification_config` callbacks occur.

## `transcription_config`

`language` is the only required field.

| Field | Type | Notes |
|---|---|---|
| `language` | string, required | Language model to process the audio, normally an ISO language code. `multi` for Melia 1 and Oak 1. `auto` for language identification |
| `model` | string | `standard`, `enhanced`, `melia-1`, `oak-1` |
| `operating_point` | string | Deprecated. Use `model`. Kept for backward compatibility; same values |
| `domain` | string | Requests a specialized model based on `language` but optimized for a field, for example `finance` or `medical` |
| `output_locale` | string | Locale used when generating the output, normally an ISO language code (for example `en-GB`). Not supported with `"language": "auto"` |
| `language_hints` | array of strings | Languages expected in the audio, as ISO language codes. Melia 1 and Oak 1 only |
| `language_hints_strict` | boolean | Whether to treat the provided language hints as strict |
| `additional_vocab` | array | Custom dictionary. Items: `content` (required), `sounds_like` (array of strings). Maximum 20,000 items |
| `punctuation_overrides` | object | `sensitivity` (0 to 1, default 0.5; higher produces more punctuation), `permitted_marks` (array of single characters, or `all`, the default) |
| `diarization` | string | `none` (default), `speaker`, `channel` |
| `channel_diarization_labels` | array of strings | Labels for channels. Each must match `^[A-Za-z0-9._]+$` |
| `speaker_diarization_config` | object | `prefer_current_speaker` (boolean), `speaker_sensitivity` (0 to 1, default 0.5), `get_speakers` (boolean), `speakers` (array). See [diarization-and-speaker-identification.md](diarization-and-speaker-identification.md) |
| `enable_entities` | boolean | Adds `entity` results. On Melia 1 and Oak 1, only accepted together with `entities_config.detect_advanced_entities: true` |
| `entities_config` | object | `detect_advanced_entities` (boolean). Switches `enable_entities` to Entity Detection |
| `enable_redaction` | boolean | PII Redaction. Must be set together with `redaction_config.entity_classes` |
| `redaction_config` | object | `entity_classes` (array, at least 1 item, unique) |
| `audio_filtering_config` | object | `volume_threshold` (0 to 100). Lower limit of audio volume at which speech and audio events are transcribed |
| `transcript_filtering_config` | object | `remove_disfluencies` (boolean, default `false`: disfluencies are tagged `disfluency` rather than removed), `replacements` (array of `{ "from": "...", "to": "..." }`) |
| `max_delay_mode` | string | `fixed`, `flexible` |

For custom dictionary, Entity Detection, PII Redaction, translation, audio events, punctuation, and formatting behavior, use `speechmatics:transcription-features`. For model and language choice, use `speechmatics:get-started`.

## Language hints

Docs: https://docs.speechmatics.com/speech-to-text/batch/input#language-hints

Language hints are optional and apply only to Melia 1 and Oak 1, which detect supported languages automatically. For Enhanced and Standard, set `language` to a supported language instead.

Hints have two effects:

- **Language labels are restricted to the hinted languages.** Every word is labeled with one of the languages you list. With one hint, every word gets that label. With two or more, labels can switch between the hinted languages.
- **Transcription is biased toward the hinted languages.** This can improve accuracy, especially for short clips and similar-sounding languages. Speech in other languages is less likely to be transcribed, but can still appear, labeled as one of the hinted languages.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "melia-1",
    "language": "multi",
    "language_hints": ["en", "ar"]
  }
}
```

The model cannot label a word with a language you did not hint. If the audio may contain languages you cannot predict, omit `language_hints`.

## Fetch URL

Docs: https://docs.speechmatics.com/speech-to-text/batch/input#fetch-url

If the media is in cloud storage (for example AWS S3 or Azure Blob Storage), submit the job with a URL instead of uploading the file.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "fetch_data": {
    "url": "${URL}/{FILENAME}"
  }
}
```

- `fetch_data.auth_headers` is a list of additional headers added to the fetch request over http or https, for example an OAuth2 bearer token.
- In SaaS, fetch requests have the user agent `Speechmatics-API/2.0`.
- Omit the `data_file` form field when using `fetch_data`.
- `duration` in job details may be missing for fetch URL jobs.

### Fetch failure

If the audio cannot be retrieved, the job fails with `status` `rejected` and no transcript is generated. `GET /jobs/{jobid}` returns an `errors` array with every failure message. A retry mechanism is in place, so one job can have several entries.

```json
{
  "job": {
    "config": {
      "fetch_data": {
        "url": "https://example.com/average-files/punctuation1.mp3"
      },
      "notification_config": [
        {
          "contents": ["jobinfo"],
          "url": "https://example.com/"
        }
      ],
      "transcription_config": {
        "language": "de"
      },
      "type": "transcription"
    },
    "created_at": "2021-07-19T12:55:03.754Z",
    "data_name": "",
    "duration": 0,
    "errors": [
      {
        "message": "unable to fetch audio: http status code 404",
        "timestamp": "2021-07-19T12:55:05.425Z"
      },
      {
        "message": "unable to fetch audio: http status code 404",
        "timestamp": "2021-07-19T12:55:07.649Z"
      },
      {
        "message": "unable to fetch audio: http status code 404",
        "timestamp": "2021-07-19T12:55:17.665Z"
      },
      {
        "message": "unable to fetch audio: http status code 404",
        "timestamp": "2021-07-19T12:55:37.643Z"
      }
    ],
    "id": "a81ko4eqjl",
    "status": "rejected"
  }
}
```

## Tracking metadata

Docs: https://docs.speechmatics.com/speech-to-text/batch/output#tracking-metadata

Add `tracking` to follow a job through your own workflow. It is returned when you check job status and when you get the transcript (under `job.tracking`), and is available where possible in callbacks.

| Field | Type | Notes |
|---|---|---|
| `title` | string | The title of the job |
| `reference` | string | External system reference |
| `tags` | array of strings | |
| `details` | object | Customer-defined JSON structure |

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "tracking": {
    "title": "ACME Q12018 Statement",
    "reference": "/data/clients/ACME/statements/segs/2018Q1-seg8",
    "tags": [
      "quick-review",
      "segment"
    ],
    "details": {
      "user_type": "agent",
      "client": {
        "name": "ACME Corp",
        "type": "enterprise"
        },
      "seg_start": 963.201,
      "seg_end": 1091.481
    }
  }
}
```

## App usage tracking

Docs: https://docs.speechmatics.com/speech-to-text/batch/output#app-usage-tracking

For integrations where customers use their own Speechmatics API keys, aggregate usage by application (unique users, processing hours, languages used, and more). Contact Support (https://support.speechmatics.com) to enable the feature first, then pass the `sm-app` query parameter when starting a job:

```bash
APP_ID="YourAppID"
API_KEY="YOUR_API_KEY"
PATH_TO_FILE="example.wav"

curl -L -X POST "https://au1.asr.api.speechmatics.com/v2/jobs/?sm-app=${APP_ID}" \
    -H "Authorization: Bearer ${API_KEY}" \
    -F data_file=@${PATH_TO_FILE} \
    -F config='{"type": "transcription","transcription_config": { "model": "enhanced","language": "en" }}'
```

The JavaScript client samples pass an `appId` option to the `BatchClient` constructor. The docs do not state whether it maps to `sm-app`.

## On-prem only: `X-SM-Processing-Data` header

`POST /jobs` accepts an `X-SM-Processing-Data` header on on-prem deployments only. It is a JSON dictionary of processing settings for the job worker: `parallel_engines` (integer, the number of engines the worker can use in parallel for this job) and `user_id` (string). Example: `{"parallel_engines": 4}`.

## Try a config in the portal

Set up a job in the portal (https://portal.speechmatics.com/jobs/create/batch) and select **View config** on the output page to get the equivalent config for the API.
