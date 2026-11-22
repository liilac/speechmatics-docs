# Translation

Docs: https://docs.speechmatics.com/speech-to-text/features/translation

Available in Batch and Realtime. Not available in agent STT. Works on SaaS and on-prem (GPU translation container: https://docs.speechmatics.com/deployments/container/gpu-translation).

## Configuration

`translation_config` is a sibling of `transcription_config`.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "translation_config": {
    "target_languages": ["es", "de"],
    "enable_partials": true
  }
}
```

| Field | Required | Description |
|---|---|---|
| `target_languages` | Yes | ISO language codes to translate into. Maximum 5. |
| `enable_partials` | No | Realtime. Send `AddPartialTranslation` messages as well as finals. Default `false`. |

## Batch output

The JSON transcript gains a `translations` property: a map of ISO language code to an array of translated sentences.

| Sentence field | Description |
|---|---|
| `start_time`, `end_time` | Seconds. |
| `content` | Translated text. |
| `speaker` | Speaker label when diarization is enabled. |
| `channel` | Channel label (in `spec/batch.yaml`). |

```json
{
    "format": "2.9",
    "job": {
        "created_at": "2023-01-23T19:31:19.354Z",
        "data_name": "example.wav",
        "duration": 15,
        "id": "ggqjaazkqf"
    },
    "metadata": {
        "created_at": "2023-01-23T19:31:44.766Z",
        "type": "transcription",
        "transcription_config": {
            "language": "en",
            "diarization": "speaker"
        },
        "translation_config": {
            "target_languages": [
                "es"
            ]
        }
    },
    "results": [
        {
            "start_time": 0.78,
            "end_time": 1.32,
            "type": "word",
            "alternatives": [
                {
                    "content": "Welcome",
                    "confidence": 1.0,
                    "language": "en",
                    "speaker": "S1"
                }
            ]
        },
        ...
    ],
    "translations": {
        "es": [
            {
                "start_time": 0.78,
                "end_time": 2.58,
                "content": "Bienvenidos a Speechmatics.",
                "speaker": "S1"
            },
            {
                "start_time": 3.0,
                "end_time": 7.94,
                "content": "Esperamos que tengas un gran día.",
                "speaker": "S1"
            },
            ...
        ]
      }
}
```

`"format": "2.9"` is the JSON output version current at time of writing; check the docs.

## Realtime output

One stream of translation messages per requested language. Translation messages arrive after transcription messages and do not delay transcription.

Message fields: `message` (required), `format`, `language` (required, ISO code), `results` (required). Each result has `content`, `start_time`, `end_time` (all required; times refer to the original transcribed audio segment) and `speaker` when speaker diarization is enabled.

### Partials

Lower latency, typically unfinished sentences. Off by default; set `translation_config.enable_partials`.

```json
{
  "format": "2.9",
  "message": "AddPartialTranslation",
  "language": "es",
  "results": [
    {
      "start_time": 5.45999987795949,
      "end_time": 5.889999870583415,
      "content": "Bienvenidos a",
      "speaker": "S1"
    }
  ]
}
```

### Finals

Most accurate, usually a complete sentence. Never updated afterwards.

```json
{
  "format": "2.9",
  "message": "AddTranslation",
  "language": "es",
  "results": [
    {
      "start_time": 5.45999987795949,
      "end_time": 6.189999870583415,
      "content": "Bienvenidos a Speechmatics.",
      "speaker": "S1"
    }
  ]
}
```

## Python: Batch

```python
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en" # Transcription language
TRANSLATION_LANGUAGES = ["es","de"]

settings = ConnectionSettings(
    url="https://eu1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {
    "type": "transcription",
    "transcription_config": {
        "language": LANGUAGE,
        "model": "enhanced"
    },
    "translation_config": {
        "target_languages":TRANSLATION_LANGUAGES
    }
}

# Open the client using a context manager
with BatchClient(settings) as client:
    try:
        job_id = client.submit_job(
            audio=PATH_TO_FILE,
            transcription_config=conf,
        )
        print(f'job {job_id} submitted successfully, waiting for transcript')

        # Note that in production, you should set up notifications instead of polling.
        transcript = client.wait_for_completion(job_id, transcription_format='json-v2')
        for language in TRANSLATION_LANGUAGES:
          # Print the translation for each language from the JSON
          print(f"Translation for {language}")
          translation = ""
          for translated_segment in transcript["translations"][language]:
              translation += translated_segment["content"] + " "
          print(translation)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print('Invalid API key - Check your API_KEY at the top of the code!')
        elif e.response.status_code == 400:
            print(e.response.json()['detail'])
        else:
            raise e
```

## Python: Realtime

In this client, `translation_config` is passed as an argument of `TranscriptionConfig`.

```python
import speechmatics
from httpx import HTTPStatusError

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en" # Transcription language
TRANSLATION_LANGUAGES = ["es","de"]
CONNECTION_URL = f"wss://eu.rt.speechmatics.com/v2/{LANGUAGE}"

# Create a transcription client
ws = speechmatics.client.WebsocketClient(
    speechmatics.models.ConnectionSettings(
        url=CONNECTION_URL,
        auth_token=API_KEY,
    )
)

# Define an event handler to print the translations
def print_translation(msg):
    msg_type="Final"
    if msg['message'] == "AddPartialTranslation":
        msg_type="Partial"

    language = msg['language'] # language for translation message
    translations = []
    for translation_segment in msg['results']:
        translations.append(translation_segment['content'])

    translation = " ".join(translations).strip()
    print(f"{msg_type} translation for {language}: {translation}")

# Register the event handler for partial translation
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AddPartialTranslation,
    event_handler=print_translation,
)

# Register the event handler for full translation
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AddTranslation,
    event_handler=print_translation,
)

settings = speechmatics.models.AudioSettings()

# Define transcription parameters with translation
# Full list of parameters described here: https://speechmatics.github.io/speechmatics-python/models

translation_config = speechmatics.models.RTTranslationConfig(
    target_languages=TRANSLATION_LANGUAGES,
    #enable_partials=True # Optional argument to provide translation of partial sentences
)

transcription_config = speechmatics.models.TranscriptionConfig(
    model="enhanced",
    language=LANGUAGE,
    translation_config=translation_config
)

print("Starting transcription (type Ctrl-C to stop):")
with open(PATH_TO_FILE, 'rb') as fd:
    try:
        ws.run_synchronously(fd, transcription_config, settings)
    except KeyboardInterrupt:
        print("\nTranscription stopped.")
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print('Invalid API key - Check your API_KEY at the top of the code!')
        else:
            raise e
```

## Languages

Translated to and from English in Realtime and Batch:

| Language | Code | Language | Code |
|---|---|---|---|
| Bulgarian | `bg` | Japanese | `ja` |
| Catalan | `ca` | Korean | `ko` |
| Mandarin | `cmn` | Lithuanian | `lt` |
| Czech | `cs` | Latvian | `lv` |
| Danish | `da` | Malay | `ms` |
| German | `de` | Dutch | `nl` |
| Greek | `el` | Norwegian | `no` |
| Spanish | `es` | Polish | `pl` |
| Estonian | `et` | Portuguese | `pt` |
| Finnish | `fi` | Romanian | `ro` |
| French | `fr` | Russian | `ru` |
| Galician | `gl` | Slovakian | `sk` |
| Hindi | `hi` | Slovenian | `sl` |
| Croatian | `hr` | Swedish | `sv` |
| Hungarian | `hu` | Turkish | `tr` |
| Indonesian | `id` | Ukrainian | `uk` |
| Italian | `it` | Vietnamese | `vi` |

Batch can also translate from Norwegian Bokmål to Nynorsk.

For the live list of pairs, query feature discovery: [feature-discovery.md](feature-discovery.md).

## Best practices

- Use the Enhanced model. Higher transcription accuracy gives better translations.
- Keep punctuation settings at their defaults.
- Each extra target language increases Batch processing time.
- Realtime sessions may have a 5-second delay on closing while translations finalize.

## Limitations

- Maximum 5 target languages per transcription.
- Only JSON output includes translations. Text and SRT contain the source language only.
- Timestamps per word, confidence scores, word tagging and regional spelling are available only in the original language.

## More

- Speechmatics Academy example: https://github.com/speechmatics/speechmatics-academy/tree/main/basics/05-translation
- Combine with diarization to get `speaker` on translated sentences.
