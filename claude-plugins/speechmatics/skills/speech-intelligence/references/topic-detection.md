# Topic detection

Docs: https://docs.speechmatics.com/speech-to-text/batch/speech-intelligence/topic-detection

Identify topics and the segments of audio they apply to, in the same Batch API call that transcribes the audio. Use it to tag conversations or find trends.

## Enable

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "topic_detection_config": {}
}
```

## `topic_detection_config`

| Field | Type | Description |
|---|---|---|
| `topics` | array of strings | Topics to detect. Maximum 10. Omit to use the default topics |

Custom topics:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "topic_detection_config": {
    "topics": ["pricing", "deployment", "languages"]
  }
}
```

Default topics:

- Business & Finance
- Education
- Entertainment
- Events & Attractions
- Food & Drink
- News & Politics
- Science
- Sports
- Technology & Computing
- Travel

If more than 10 topics are provided, the transcription completes, no topics are returned, and an error is included in the JSON output.

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
    # You can also configure the list of topics you wish to detect. See below for more detail.
    "topic_detection_config": {},
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
        topics_detected = transcript["topics"]
        topic_segments = topics_detected["segments"]
        topic_summary = topics_detected["summary"]["overall"]

        # print the overall count for each topic
        print(topic_summary)

        # print the text and the corresponding topic(s) and timings for each segment
        for segment in topic_segments:
            print(
                f"({segment['start_time']} - {segment['end_time']}): {segment['text']} ({[t['topic'] for t in segment['topics']]})"
            )
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key - Check your API_KEY at the top of the code!")
        elif e.response.status_code == 400:
            print(e.response.json()["detail"])
        else:
            raise e
```

## Response

Topics are only present in the JSON output, under the top-level `topics` object.

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-05-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "en"
    },
    "topic_detection_config": {}
  },
  "results": [...],
  "topics": {
    "segments": [
      {
        "text": "The National Park Service on Twitter says it expects the closures to remain in effect ...",
        "start_time": 0.80,
        "end_time": 1.72,
        "topics": [{"topic": "Events & Attractions"}]
      },
      {
        "text": "Lawmakers in Canada have voted to regulate online streaming content ...",
        "start_time": 2.06,
        "end_time": 3.40,
        "topics": [{"topic": "News & Politics"}, {"topic": "Technology & Computing"}]
      }
    ],
    "summary": {
      "overall": {
        "Business & Finance": 1,
        "Education": 0,
        "Entertainment": 0,
        "Events & Attractions": 0,
        "Food & Drink": 0,
        "News & Politics": 1,
        "Science": 0,
        "Sports": 0,
        "Technology & Computing": 1,
        "Travel": 0
      }
    }
  }
}
```

### `topics.segments[]`

| Field | Type | Description |
|---|---|---|
| `text` | string | The transcript text of the segment |
| `start_time` | number | Start of the segment, in seconds |
| `end_time` | number | End of the segment, in seconds |
| `topics` | array | One or more `{ "topic": "<name>" }` objects. A segment can have several topics |

### `topics.summary.overall`

An object mapping each topic name to an integer count of segments. Topics with no segments appear with `0`.

With custom topics (API spec example):

```json
{
  "segments": [
    {
      "text": "I am happy with the product.",
      "start_time": 0.0,
      "end_time": 5.0,
      "topics": [{ "topic": "product" }]
    },
    {
      "text": "We will deploy this container for Spanish.",
      "start_time": 6.0,
      "end_time": 12.0,
      "topics": [{ "topic": "deployment" }, { "topic": "languages" }]
    }
  ],
  "summary": {
    "overall": {
      "deployment": 1,
      "languages": 1,
      "product": 1
    }
  }
}
```

## Sample outputs

Topics detected in a news segment.

Default topics:

| Topic(s) | Segment | Start (s) | End (s) |
|---|---|---|---|
| News & Politics | President Biden and the South Korean President Yoon Sung Yell have reaffirmed their commitment to extended deterrence in the face of the growing nuclear threat from North Korea. The two leaders have agreed to give South Korea a greater voice in how the US would respond to any nuclear incident. | 2.57 | 21.35 |
| News & Politics | President Zelensky says he's discussed ways to reach a fair and sustainable peace. In his first direct phone call with the Chinese leader Xi Jinping, since Russia invaded Ukraine. Mr. Zelensky stressed Ukraine would not accept any loss of territory. | 21.92 | 37.76 |
| News & Politics | Renewed fighting near Khartoum is threatening the three day ceasefire in Sudan. People in the capital are struggling to get food and water. Thousands are continuing to leave. | 38.33 | 49.16 |
| News & Politics | The UN's envoy to Haiti has told a meeting of the Security Council that gang violence is expanding at an alarming rate in areas previously considered safe. | 49.73 | 60.02 |
| Entertainment, News & Politics | The Walt Disney Corporation has sued the Republican governor of Florida, Ron DeSantis, seeking to overturn state efforts to exert control over its theme park. The entertainment giant says it's facing government retaliation after it criticized a Florida law that banned lessons and sexuality and gender identity in schools. | 61.1 | 82.13 |

Custom topics `["War", "Weather"]` on the same audio:

| Topic(s) | Segment | Start (s) | End (s) |
|---|---|---|---|
| War | President Biden and the South Korean President Yoon Sung Yell have reaffirmed their commitment to extended deterrence in the face of the growing nuclear threat from North Korea. | 2.57 | 13.7 |
| War | In his first direct phone call with the Chinese leader Xi Jinping, since Russia invaded Ukraine. Mr. Zelensky stressed Ukraine would not accept any loss of territory. | 26.99 | 37.76 |
| War | Renewed fighting near Khartoum is threatening the three day ceasefire in Sudan. | 38.33 | 43.25 |
| Weather | The European Union says in 2022, Southern Europe experienced the highest number of days on record with very strong heat stress. | 107.48 | 117.56 |

Custom topics change both which segments are returned and their boundaries. Segments that match no topic are not returned.

## Considerations

- Topics is only supported for English.
- Topics supports a custom list of up to 10 topics.
- Topics uses a large language model (LLM). This occasionally leads to inaccuracies in the topics detected and the corresponding segments, and you may receive different segments when running the same file multiple times.

## Errors

In every case the transcription completes, no topics are returned, and `metadata.topic_detection_errors` holds the error.

| `type` | `message` | Cause |
|---|---|---|
| `unsupported_language` | `Topic Detection not supported for cy.` | Language other than English |
| `unsupported_list_of_topics` | `List of topics cannot exceed 10 topics.` | More than 10 items in `topics` |
| `topic_detection_failed` | `Topic Detection failed.` | Topic detection failed |

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-05-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "en"
    },
    "topic_detection_config": {
      "topics": ["topic1", "topic2", "topic3", "topic4", "topic5", "topic6", "topic7", "topic8", "topic9", "topic10", "topic11"]
    },
    "topic_detection_errors": [
      {"type": "unsupported_list_of_topics", "message": "List of topics cannot exceed 10 topics."}
    ]
  },
  "results": [...]
}
```

## More examples

Speechmatics Academy: https://github.com/speechmatics/speechmatics-academy/tree/main/basics/04-audio-intelligence
