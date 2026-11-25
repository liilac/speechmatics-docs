# Output: job status, transcripts, and SRT

Docs: https://docs.speechmatics.com/speech-to-text/batch/output and https://docs.speechmatics.com/speech-to-text/batch/srt-format

Jobs are asynchronous by default: submit, check status, then fetch the transcript. To block for the result in one request, see [synchronous.md](synchronous.md). To be called back on completion, see [notifications.md](notifications.md).

## Check a single job

A job can be retrieved by ID for up to 7 days, after which it is deleted automatically.

```bash
# $JOB_ID is from the submit command output
curl -L -X GET "https://au1.asr.api.speechmatics.com/v2/jobs/$JOB_ID" \
-H "Authorization: Bearer $API_KEY"
```

The endpoint applies a short default wait and returns as soon as the job reaches a terminal state. Pass `wait` to control the duration, or `wait=0` to return immediately.

`job.status` values:

| Value | Meaning |
|---|---|
| `running` | The job is still processing |
| `done` | The job completed. The transcript is available at `/jobs/{jobid}/transcript` |
| `rejected` | Transcription was not possible. Accompanied by an error message in `job.errors` |
| `deleted` | The user deleted the job |
| `expired` | The system deleted the job, usually because it was in the `done` state for a very long time |

Example response:

```json
{
  "job": {
    "config": {
      "notification_config": null,
      "transcription_config": {
        "additional_vocab": null,
        "channel_diarization_labels": null,
        "language": "en"
      },
      "type": "transcription"
    },
    "created_at": "2019-01-17T17:50:54.113Z",
    "data_name": "example.wav",
    "duration": 275,
    "id": "yjbmf9kqub",
    "status": "running"
  }
}
```

`JobDetails` fields: `created_at` (UTC date-time), `data_name`, `text_name`, `duration` (integer seconds; may be missing for fetch URL jobs), `id`, `status`, `config` (the `JobConfig`), `lang` (backward compatibility with the v1 API), `errors` (array of `{ "timestamp", "message" }`, for example when audio could not be fetched or a notification could not be sent).

## Check multiple jobs

Returns the 100 most recent jobs submitted in the past 7 days. Deleted jobs are excluded unless you pass `include_deleted=true`.

```bash
curl -L -X GET "https://au1.asr.api.speechmatics.com/v2/jobs/" \
     -H "Authorization: Bearer $API_KEY"
```

Paginate with `limit` (1 to 100) and `created_before` (UTC timestamp cursor). See [api-reference.md](api-reference.md).

## Get the transcript

```bash
curl -L -X GET "https://au1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/transcript?format=txt" \
  -H "Authorization: Bearer ${API_KEY}"
```

| `format` | Returns | Use for |
|---|---|---|
| `json-v2` (default) | JSON | Word timestamps, speakers, translations, speech intelligence results |
| `txt` | Plain text | Quick access to the text |
| `srt` | SubRip subtitles | Subtitle files |

The endpoint applies a short default wait. Pass `wait` alongside `format` to block for the transcript instead of polling. While the transcript is not ready, the response is HTTP 404.

## `json-v2` transcript schema

Top-level fields (`RetrieveTranscriptResponse`):

| Field | Type | Notes |
|---|---|---|
| `format` | string, required | JSON transcript format version, `2.9` (current at time of writing; check the docs) |
| `job` | object, required | `created_at`, `data_name`, `duration` (seconds), `id`, `tracking` |
| `metadata` | object, required | See below |
| `results` | array, required | Recognition results. See below |
| `speakers` | array | Speaker identifiers: `{ "label", "speaker_identifiers": [...] }`. Present with `get_speakers` |
| `translations` | object | Map of language code to array of `{ "start_time", "end_time", "content", "speaker", "channel" }`. Configured with `translation_config` |
| `summary` | object | `{ "content" }`. Configured with `summarization_config` |
| `sentiment_analysis` | object | Configured with `sentiment_analysis_config` |
| `topics` | object | Configured with `topic_detection_config` |
| `chapters` | array | Configured with `auto_chapters_config` |
| `audio_events` | array | `{ "type", "start_time", "end_time", "confidence", "channel" }`. Only set if `audio_events_config` is in the config |
| `audio_event_summary` | object | `overall` and `channels` (channel diarization only), keyed by event type with `total_duration` and `count` |

`metadata` (`RecognitionMetadata`):

| Field | Notes |
|---|---|
| `created_at` | UTC date-time the transcription output was created. Required |
| `type` | `transcription`. Required |
| `transcription_config` | The config used |
| `output_config` | The output config used |
| `language_pack_info` | `word_delimiter` (required), `writing_direction` (`left-to-right`, `right-to-left`), `language_description` (for example `Japanese`), `itn` (whether inverse text normalization is available), `adapted` (whether language model adaptation was applied), `per_language_word_delimiters`, `per_language_writing_direction` |
| `language_identification` | Result of language identification. See [language-identification.md](language-identification.md) |
| `translation_errors` | Items: `type` (`translation_failed`, `unsupported_translation_pair`), `message` |
| `summarization_errors` | Items: `type` (`summarization_failed`, `unsupported_language`), `message` |
| `sentiment_analysis_errors` | Items: `type` (`sentiment_analysis_failed`, `unsupported_language`), `message` |
| `topic_detection_errors` | Items: `type` (`topic_detection_failed`, `unsupported_list_of_topics`, `unsupported_language`), `message` |
| `auto_chapters_errors` | Items: `type` (`auto_chapters_failed`, `unsupported_language`), `message` |
| `orchestrator_version` | PEP 440 version string, or `version_not_found` |

`results[]` (`RecognitionResult`):

| Field | Notes |
|---|---|
| `type` | `word`, `punctuation`, `entity`. Required. New types may appear without being requested; ignore unrecognized types |
| `start_time`, `end_time` | Seconds. Required |
| `alternatives` | Array ordered by likelihood. Each has `content`, `confidence`, `language` (all required), and optional `speaker`, `display.direction` (`ltr`, `rtl`), `tags` (array of strings) |
| `channel` | Channel label, with channel diarization |
| `volume` | 0 to 100. Indication of audio volume across the period the word was spoken |
| `is_eos` | Punctuation only. Whether the mark ends a sentence |
| `attaches_to` | Punctuation only: `previous`, `next`, `both`, `none`. Use with `language_pack_info.word_delimiter` to place delimiters on the correct side of the mark |
| `entity_class` | `entity` results only. The smart formatting class (for example `date`, `money`) or the Entity Detection class (for example `name_given`, `dob`) |
| `spoken_form` | `entity` results only. Array of `word` or `punctuation` items with `start_time`, `end_time`, `type`, `alternatives` |
| `written_form` | `entity` results only. Array of `word` items with `start_time`, `end_time`, `type`, `alternatives` |

Spoken and written forms are not available with Entity Detection or when PII Redaction is enabled. For entities, see `speechmatics:transcription-features`.

### Example response

Output for the docs' `example.wav` (47 results; abbreviated here):

```json
{
  "format": "2.9",
  "job": {
    "created_at": "2025-06-30T11:43:54.135Z",
    "data_name": "example.wav",
    "duration": 15,
    "id": "650krlru2e"
  },
  "metadata": {
    "created_at": "2025-06-30T11:44:08.133526Z",
    "language_pack_info": {
      "adapted": false,
      "itn": true,
      "language_description": "English",
      "word_delimiter": " ",
      "writing_direction": "left-to-right"
    },
    "orchestrator_version": "2025.06.28+1eb4127132+13.4.0",
    "transcription_config": {
      "language": "en",
      "model": "enhanced"
    },
    "type": "transcription"
  },
  "results": [
    {
      "alternatives": [
        { "confidence": 1, "content": "Welcome", "language": "en", "speaker": "UU" }
      ],
      "end_time": 1.36,
      "start_time": 0.72,
      "type": "word"
    },
    {
      "alternatives": [
        { "confidence": 1, "content": "to", "language": "en", "speaker": "UU" }
      ],
      "end_time": 1.44,
      "start_time": 1.36,
      "type": "word"
    },
    {
      "alternatives": [
        { "confidence": 0.98, "content": "Speechmatics", "language": "en", "speaker": "UU" }
      ],
      "end_time": 2.44,
      "start_time": 1.48,
      "type": "word"
    },
    {
      "alternatives": [
        { "confidence": 1, "content": ".", "language": "en", "speaker": "UU" }
      ],
      "attaches_to": "previous",
      "end_time": 2.44,
      "is_eos": true,
      "start_time": 2.44,
      "type": "punctuation"
    }
  ]
}
```

`speaker` is `UU` when diarization is not applied.

### Rebuild text from `results`

The docs' JavaScript sample joins words with a space:

```javascript
response.results.map((r) => r.alternatives?.[0].content).join(" ")
```

This puts a space before punctuation ("Speechmatics ."). For well-formed text, use `attaches_to` on punctuation items with the `word_delimiter` from `language_pack_info`, or request `format=txt`.

### Multilingual transcript output

For a Melia 1 job, `language` on each word is the language detected for that word, so it can change across the transcript. For Enhanced and Standard jobs, the same language is reported for every word.

```json
{
  "results": [
    {
      "alternatives": [
        { "content": "Hello", "confidence": 0.98, "language": "en" }
      ],
      "start_time": 0.20,
      "end_time": 0.52,
      "type": "word"
    },
    {
      "alternatives": [
        { "content": "مرحبا", "confidence": 0.95, "language": "ar" }
      ],
      "start_time": 0.60,
      "end_time": 1.04,
      "type": "word"
    }
  ]
}
```

For multilingual transcripts, `language_pack_info` reports the word delimiter and writing direction per language:

```json
{
  "metadata": {
    "language_pack_info": {
      "per_language_word_delimiters": {
        "en": " ",
        "ar": " "
      },
      "per_language_writing_direction": {
        "en": "left-to-right",
        "ar": "right-to-left"
      }
    }
  }
}
```

## Plain text

`format=txt` returns `text/plain`. The API reference example with diarization:

```
SPEAKER: S1
Hello world.
```

## SRT

Docs: https://docs.speechmatics.com/speech-to-text/batch/srt-format

SubRip (SRT) output contains the transcript with alignment timestamps. Default line length and line count follow broadcaster best practice.

```bash
curl -L -X GET "https://au1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/transcript?format=srt" \
    -H "Authorization: Bearer ${API_KEY}"
```

Override the defaults in the job config at submission time:

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en"
  },
  "output_config": {
    "srt_overrides": {
      "max_line_length": 37,
      "max_lines": 2
    }
  }
}
```

| Field | Default | Meaning |
|---|---|---|
| `max_line_length` | `37` | Maximum characters per subtitle line, including white space |
| `max_lines` | `2` | Maximum lines in a subtitle section |

## Data retention

Audio files, transcripts, and configuration data are stored for 7 days. Later requests for a transcript or file fail and the job status is `expired`. Delete earlier with `DELETE /jobs/{jobid}`. See [limits-and-troubleshooting.md](limits-and-troubleshooting.md).
