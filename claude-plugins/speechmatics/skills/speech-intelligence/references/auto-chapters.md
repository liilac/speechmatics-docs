# Auto chapters

Docs: https://docs.speechmatics.com/speech-to-text/batch/speech-intelligence/auto-chapters

Split the audio into distinct, continuous chapters, each with timings, a title, and a summary, in the same Batch API call that transcribes it.

## Enable

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "auto_chapters_config": {}
}
```

`auto_chapters_config` is an empty object. It has no options.

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
    url="https://au1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {
    "type": "transcription",
    "transcription_config": {"language": LANGUAGE, "model": "enhanced"},
    "auto_chapters_config": {},
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
        chapters = transcript["chapters"]
        for chapter in chapters:
            print(
                f"({chapter['start_time']} - {chapter['end_time']}) {chapter['title']}\n{chapter['summary']}\n\n"
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

Chapters are only available in the JSON output, as a top-level `chapters` array. Chapters are non-overlapping and exhaustive: they cover the entire audio file from start to end.

### `chapters[]`

| Field | Type | Description |
|---|---|---|
| `title` | string | The auto-generated title for the chapter |
| `summary` | string | An auto-generated, paragraph-style, short summary of the chapter |
| `start_time` | number | The start time of the chapter in the audio file, in seconds |
| `end_time` | number | The end time of the chapter in the audio file, in seconds |

```json
{
  "format": "2.9",
  "job": { ... },
  "metadata": {
    "created_at": "2023-07-17T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "en",
      "diarization": "speaker"
    },
    "auto_chapters_config": {}
  },
  "chapters": [
    {
      "end_time": 6.3,
      "start_time": 0.0,
      "summary": "The speaker begins by mentioning the 1961 summit between President Kennedy and Soviet Premier Khrushchev, noting that in hindsight it appeared to be a failure. However, the speaker says that summits like this often have long-term impacts that are not immediately clear.",
      "title": "The 1961 Kennedy-Khrushchev Summit"
    },
    {
      "end_time": 13.23,
      "start_time": 6.3,
      "summary": "The speaker then notes that the 1961 Kennedy-Khrushchev summit contributed to the later Cuban Missile Crisis, further illustrating the complex impacts summits can have.",
      "title": "The Cuban Missile Crisis"
    },
    {
      "end_time": 18.78,
      "start_time": 13.23,
      "summary": "The speaker argues that it is difficult to quickly assess the impact of summits like the recent one. The speaker says we will not be able to make definitive judgments about the impacts of this summit right away.",
      "title": "Assessing the Impact of Summits"
    },
    {
      "end_time": 25.53,
      "start_time": 18.78,
      "summary": "The speaker abruptly shifts topics to discuss a Supreme Court decision upholding Ohio's law to purge voter rolls, which are some of the strictest voter roll purge laws in the country.",
      "title": "Supreme Court Decision on Ohio Voter Rolls"
    }
  ],
  "results": [...]
}
```

The JSON transcript format version `2.9` is current at time of writing; check the docs.

## Considerations

- Chapters work best for longer-form content. A minimum of 10 minutes of transcribed speech is recommended.
- Chapters work best with speaker or channel diarization enabled.
- Punctuation plays a significant role in quality. Avoid disabling end-of-sentence punctuation or reducing punctuation sensitivity.

## Language support

Chapters are supported for all Speechmatics languages except Irish, Maltese, Urdu, Bengali, and Swahili. Language list: https://docs.speechmatics.com/speech-to-text/languages

## Errors

In both cases the transcription completes, no chapters are returned, and `metadata.auto_chapters_errors` holds the error.

| `type` | `message` | Cause |
|---|---|---|
| `unsupported_language` | `Auto chapters not supported for xx.` | Unsupported language |
| `auto_chapters_failed` | `Auto Chapters failed.` | Chapter generation failed |

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-05-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "xx"
    },
    "auto_chapters_config": {},
    "auto_chapters_errors": [
      {"type": "unsupported_language", "message": "Auto chapters not supported for xx."}
    ]
  },
  "results": [...]
}
```
