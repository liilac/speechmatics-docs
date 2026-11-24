---
name: speech-intelligence
description: Adds summarization, sentiment analysis, topic detection, and auto chapters to a Speechmatics Batch API transcription job. Use when a developer wants a summary, sentiment per sentence or speaker, topic tags, or chapter titles and timings from pre-recorded audio, or mentions summarization_config (content_type, summary_length, summary_type), sentiment_analysis_config, topic_detection_config (topics), auto_chapters_config, or the summary, sentiment_analysis, topics, and chapters fields of the json-v2 transcript. Also covers language support, the 10-topic limit, and the summarization_errors, sentiment_analysis_errors, topic_detection_errors, and auto_chapters_errors metadata fields.
---

# Speech intelligence

Get a summary, sentiment, topics, or chapters from audio in the same Batch API call that transcribes it.

## When to use this skill

Use it to enable and parse any of the four speech intelligence features on a batch transcription job.

Use a sibling skill instead for:

- Creating jobs, polling, transcript formats, notifications, limits, and Batch API errors: `speechmatics:batch-transcription`
- API keys, regions, models, and languages: `speechmatics:get-started`
- Diarization concepts, punctuation settings, translation, Entity Detection, PII Redaction, audio events: `speechmatics:transcription-features`
- Live audio: `speechmatics:realtime-transcription`. The docs describe these four features for the Batch API only.

## Prerequisites

- A working batch transcription job. See `speechmatics:batch-transcription`.
- An API key sent as `Authorization: Bearer $API_KEY`.
- Results are only in the `json-v2` transcript (the default `format`). They are not in `txt` or `srt` output.

## How it works

Add one or more config objects at the top level of the job config, alongside `transcription_config`. An empty object enables the feature with defaults.

| Feature | Config key | Options | Result field in transcript | Errors field in `metadata` | Languages |
|---|---|---|---|---|---|
| Summarization | `summarization_config` | `content_type`, `summary_length`, `summary_type` | `summary.content` | `summarization_errors` | Not listed on the docs page; `unsupported_language` error exists |
| Sentiment analysis | `sentiment_analysis_config` | None | `sentiment_analysis` | `sentiment_analysis_errors` | English only |
| Topic detection | `topic_detection_config` | `topics` (max 10) | `topics` | `topic_detection_errors` | English only |
| Auto chapters | `auto_chapters_config` | None | `chapters` | `auto_chapters_errors` | All except Irish, Maltese, Urdu, Bengali, Swahili |

All four in one job:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker"
  },
  "summarization_config": {
    "content_type": "conversational",
    "summary_length": "brief",
    "summary_type": "bullets"
  },
  "sentiment_analysis_config": {},
  "topic_detection_config": {
    "topics": ["pricing", "deployment", "languages"]
  },
  "auto_chapters_config": {}
}
```

## Minimal working example

### curl

```bash
API_KEY="YOUR_API_KEY"
PATH_TO_FILE="example.wav"

curl -L -X POST "https://au1.asr.api.speechmatics.com/v2/jobs/" \
-H "Authorization: Bearer ${API_KEY}" \
-F data_file=@${PATH_TO_FILE} \
-F config='{"type": "transcription","transcription_config": { "model":"enhanced", "language": "en" },"summarization_config": {}}'

# When the job is done, fetch the default JSON transcript and read .summary.content
curl -L -X GET "https://au1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/transcript" \
-H "Authorization: Bearer ${API_KEY}"
```

### Python

The docs' speech intelligence samples use the older `speechmatics.batch_client` client, which takes the full job config as a dict:

```python
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"  # Transcription language

settings = ConnectionSettings(
    url="https://au1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {
    "type": "transcription",
    "transcription_config": {"language": LANGUAGE, "model": "enhanced"},
    "summarization_config": {},  # You can also configure the summary. See below for more detail.
}

# Open the client using a context manager
with BatchClient(settings) as client:
    try:
        job_id = client.submit_job(
            audio=PATH_TO_FILE,
            transcription_config=conf,
        )
        print(f"job {job_id} submitted successfully, waiting for transcript")

        # Note that in production, you should set up notifications instead of polling.
        # Notifications are described here: https://docs.speechmatics.com/speech-to-text/batch/notifications
        transcript = client.wait_for_completion(job_id, transcription_format="json-v2")
        summary = transcript["summary"]["content"]
        print(summary)  # print the returned summary
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key - Check your API_KEY at the top of the code!")
        elif e.response.status_code == 400:
            print(e.response.json()["detail"])
        else:
            raise e
```

Swap the config key and the result access for the other features:

| Feature | Config line | Read the result |
|---|---|---|
| Summarization | `"summarization_config": {}` | `transcript["summary"]["content"]` |
| Sentiment analysis | `"sentiment_analysis_config": {}` | `transcript["sentiment_analysis"]["segments"]`, `transcript["sentiment_analysis"]["summary"]` |
| Topic detection | `"topic_detection_config": {}` | `transcript["topics"]["segments"]`, `transcript["topics"]["summary"]["overall"]` |
| Auto chapters | `"auto_chapters_config": {}` | `transcript["chapters"]` |

The docs do not show these features with the `speechmatics-batch` package or the JavaScript client. With any client, request the `json-v2` transcript and read the same fields.

## Configuration

### `summarization_config`

| Field | Values | Default | Notes |
|---|---|---|---|
| `content_type` | `auto`, `informative`, `conversational` | Not stated | `conversational`: dialogues such as calls and meetings. `informative`: structured content such as videos, podcasts, lectures. `auto`: chosen from the transcript |
| `summary_length` | `brief`, `detailed` | `brief` | `brief`: a few sentences. `detailed`: longer and structured |
| `summary_type` | `paragraphs`, `bullets` | Not stated | |

### `topic_detection_config`

| Field | Type | Notes |
|---|---|---|
| `topics` | array of strings | Custom topics to detect. Maximum 10 |

Default topics when `topics` is omitted: Business & Finance, Education, Entertainment, Events & Attractions, Food & Drink, News & Politics, Science, Sports, Technology & Computing, Travel.

### `sentiment_analysis_config` and `auto_chapters_config`

Empty objects. No options.

## Result shapes

```json
{
  "summary": { "content": "Laura Perez called to seek assistance..." },
  "sentiment_analysis": {
    "segments": [
      { "text": "...", "sentiment": "positive", "confidence": 0.88, "start_time": 3.0, "end_time": 7.94, "speaker": "S1" }
    ],
    "summary": {
      "overall": { "positive_count": 1, "negative_count": 0, "neutral_count": 1 },
      "speakers": [ { "speaker": "S1", "positive_count": 1, "negative_count": 0, "neutral_count": 1 } ]
    }
  },
  "topics": {
    "segments": [
      { "text": "...", "start_time": 0.80, "end_time": 1.72, "topics": [ { "topic": "Events & Attractions" } ] }
    ],
    "summary": { "overall": { "Events & Attractions": 1, "Travel": 0 } }
  },
  "chapters": [
    { "title": "...", "summary": "...", "start_time": 0.0, "end_time": 6.3 }
  ]
}
```

## Gotchas

- A failed or unsupported feature does not fail the job. Transcription completes, the result field is absent, and an entry appears in the matching `metadata.*_errors` array. Always check for the errors array before reading the result.
- More than 10 topics: the job completes with no topics and an `unsupported_list_of_topics` error.
- Sentiment analysis and topic detection are English only. Other languages return `unsupported_language`.
- Without diarization, sentiment segments have `"speaker": "UU"`. Enable speaker or channel diarization for per-speaker or per-channel results.
- Chapters work best with at least 10 minutes of transcribed speech and with speaker or channel diarization enabled. Chapters are non-overlapping and cover the whole file.
- Punctuation drives quality for sentiment and chapters. Do not disable end-of-sentence punctuation or reduce punctuation sensitivity.
- Topic detection uses a large language model (LLM). Topics and segments can be inaccurate and can differ between runs of the same file.
- JSON has no comments. The docs' config snippets include `#` and `//` comments; remove them before sending.

## References

- [references/summarization.md](references/summarization.md): read when choosing `content_type`, `summary_length`, and `summary_type`, or to see sample outputs for each combination.
- [references/sentiment-analysis.md](references/sentiment-analysis.md): read when parsing sentiment segments and per-speaker or per-channel counts, or handling sentiment errors.
- [references/topic-detection.md](references/topic-detection.md): read when setting custom topics, parsing topic segments, or handling topic errors.
- [references/auto-chapters.md](references/auto-chapters.md): read when parsing chapters or handling chapter errors.
