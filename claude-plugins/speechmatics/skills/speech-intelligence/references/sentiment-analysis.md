# Sentiment analysis

Docs: https://docs.speechmatics.com/speech-to-text/batch/speech-intelligence/sentiment-analysis

Label segments of the transcript as positive, negative, or neutral in the same Batch API call that transcribes the audio.

## Enable

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "sentiment_analysis_config": {}
}
```

`sentiment_analysis_config` is an empty object. It has no options.

## Python example

Uses the older `speechmatics.batch_client` client, as in the docs:

```python
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"  # Transcription language

settings = ConnectionSettings(
    url="https://eu1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {
    "type": "transcription",
    "transcription_config": {"language": LANGUAGE, "model": "enhanced"},
    "sentiment_analysis_config": {},
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
        sentiment = transcript["sentiment_analysis"]
        sentiment_summary = sentiment["summary"]
        sentiment_segments = sentiment["segments"]

        print(sentiment_summary["overall"])
        for segment in sentiment_segments:
            print(
                f" {segment['text']} ({segment['sentiment']})"
            )  # print the sentiment for each segment
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key - Check your API_KEY at the top of the code!")
        elif e.response.status_code == 400:
            print(e.response.json()["detail"])
        else:
            raise e
```

## Response

Sentiment results are only available in the JSON output, under the top-level `sentiment_analysis` object.

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-07-17T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "en",
      "diarization": "speaker"
    },
    "sentiment_analysis_config": {}
  },
  "results": [...],
  "sentiment_analysis": {
    "segments": [
      {
        "confidence": 0.88,
        "end_time": 7.94,
        "sentiment": "positive",
        "speaker": "S1",
        "start_time": 3.0,
        "text": "We're delighted that you've decided to try our speech to text software to get going."
      },
      {
        "confidence": 0.76,
        "end_time": 12.18,
        "sentiment": "neutral",
        "speaker": "S1",
        "start_time": 7.95,
        "text": "Just create an API key and submit a transcription request to our API."
      }
    ],
    "summary": {
      "overall": {
        "negative_count": 0,
        "neutral_count": 1,
        "positive_count": 1
      },
      "speakers": [
        {
          "speaker": "S1",
          "negative_count": 0,
          "neutral_count": 1,
          "positive_count": 1
        }
      ]
    }
  }
}
```

### `sentiment_analysis.segments[]`

| Field | Type | Description |
|---|---|---|
| `text` | string | The transcript of the analyzed segment |
| `sentiment` | string | `positive`, `neutral`, or `negative` |
| `confidence` | number, 0 to 1 | The model's certainty in the predicted sentiment |
| `start_time` | number | Start of the segment, in seconds |
| `end_time` | number | End of the segment, in seconds |
| `speaker` | string | Speaker label, if speaker diarization is enabled. `UU` when diarization is not enabled |
| `channel` | string | Channel label, if channel diarization is enabled |

### `sentiment_analysis.summary`

| Field | Type | Description |
|---|---|---|
| `overall` | object | `positive_count`, `negative_count`, `neutral_count` (integers) for the whole file |
| `speakers` | array | Per speaker: `speaker`, `positive_count`, `negative_count`, `neutral_count` |
| `channels` | array | Per channel: `channel`, `positive_count`, `negative_count`, `neutral_count` |

API spec example with both speaker and channel data:

```json
{
  "segments": [
    {
      "text": "I am happy with the product.",
      "start_time": 0.0,
      "end_time": 5.0,
      "sentiment": "positive",
      "speaker": "John Doe",
      "channel": "Chat",
      "confidence": 0.9
    },
    {
      "text": "I don't like the customer service.",
      "start_time": 6.0,
      "end_time": 12.0,
      "sentiment": "negative",
      "speaker": "John Doe",
      "channel": "Chat",
      "confidence": 0.8
    }
  ],
  "summary": {
    "overall": { "positive_count": 1, "negative_count": 1, "neutral_count": 0 },
    "speakers": [
      { "speaker": "John Doe", "positive_count": 1, "negative_count": 1, "neutral_count": 0 }
    ],
    "channels": [
      { "channel": "Chat", "positive_count": 1, "negative_count": 1, "neutral_count": 0 }
    ]
  }
}
```

## Considerations

- Sentiment is only supported for English.
- Segments typically equate to full sentences. Short utterances of 1-2 words can be combined with a neighboring sentence to form a segment.
- Punctuation plays a significant role in accuracy. Avoid disabling end-of-sentence punctuation or reducing punctuation sensitivity.
- Speaker or channel labels are only available if diarization is enabled. Without it, `"speaker": "UU"` is returned for each segment.
- The docs page states that Speaker Change is not supported in combination with Sentiment. Speaker change detection itself was removed in July 2024 (per the batch diarization page), so this no longer applies to new configs.

Schema note: the API spec's `SentimentAnalysisResult` schema nests `segments` and `summary` under an inner `sentiment_analysis` property (`sentiment_analysis.sentiment_analysis.segments`), while the spec's own example, the docs response example, and the docs Python sample all read them directly as `sentiment_analysis.segments` and `sentiment_analysis.summary`. Use the flat shape; tolerate the nested one if parsing defensively.

## Errors

In both cases the transcription completes, no sentiment is returned, and `metadata.sentiment_analysis_errors` holds the error.

| `type` | `message` | Cause |
|---|---|---|
| `unsupported_language` | `Sentiment analysis not supported for cy.` | Language other than English |
| `sentiment_analysis_failed` | `Sentiment Analysis failed.` | Sentiment analysis failed |

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-05-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "cy"
    },
    "sentiment_analysis_config": {},
    "sentiment_analysis_errors": [
      {"type": "unsupported_language", "message": "Sentiment analysis not supported for cy."}
    ]
  },
  "results": [...]
}
```

## More examples

Speechmatics Academy: https://github.com/speechmatics/speechmatics-academy/tree/main/basics/04-audio-intelligence
