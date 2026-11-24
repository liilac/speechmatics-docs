# Language identification

Docs: https://docs.speechmatics.com/speech-to-text/batch/language-identification

Detect the predominant language spoken in a file and transcribe with the matching language. This page covers SaaS. For on-prem, see https://docs.speechmatics.com/deployments/container/language-id.

## Enable

Set `language` to `auto`:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "auto"
  }
}
```

- Melia 1 does not support `"language": "auto"` and returns an error. Use `"language": "multi"`; Melia 1 is multilingual and detects languages automatically.
- For reliable identification, the file should contain at least 60 seconds of speech in the predominant language.
- Language identification adds a small increase to turnaround time.

## `language_identification_config`

A top-level field of the job config, alongside `transcription_config`.

| Field | Type | Notes |
|---|---|---|
| `expected_languages` | array of strings | Restricts the result to a set of language codes. If the detected language is not in the list, the job is rejected |
| `low_confidence_action` | string | `allow` (use the highest-confidence language), `use_default_language` (use `default_language`), `reject`. Without it, a low-confidence result rejects the job |
| `default_language` | string | Used when no speech is detected, or when `low_confidence_action` is `use_default_language` |

### Expected languages

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "auto"
  },
  "language_identification_config": {
    "expected_languages": ["en", "es", "de", "fr"]
  }
}
```

### Low confidence action

Use the highest-confidence identified language:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "auto"
  },
  "language_identification_config": {
    "low_confidence_action": "allow"
  }
}
```

Use a predefined default language:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "auto"
  },
  "language_identification_config": {
    "low_confidence_action": "use_default_language",
    "default_language": "es"
  }
}
```

The job succeeds, and the transcript metadata records the condition:

```json
{
  "transcription_config": {
    "language": "auto"
  },
  "metadata": {
    "created_at": "2023-10-10T14:51:12.051413Z",
    "language_identification": {
      "error": "LOW_CONFIDENCE",
      "message": "Language identification could not identify any language with sufficient confidence."
    }
  },
  "results": []
}
```

### Default language

By default, a job with no detected speech is rejected. Set `default_language` to prevent that:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "auto"
  },
  "language_identification_config": {
    "default_language": "es"
  }
}
```

The job succeeds with this in the metadata:

```json
{
  "metadata": {
    "created_at": "2023-10-10T14:51:12.051413Z",
    "language_identification": {
      "error": "NO_SPEECH",
      "message": "No speech found for language identification"
    }
  }
}
```

## Unsupported languages

Language identification covers all Speechmatics languages except: Bengali (`bn`), Cantonese (`yue`), Esperanto (`eo`), Interlingua (`ia`), Irish (`ga`), Maltese (`mt`), Urdu (`ur`), Uyghur (`ug`), Swahili (`sw`). The docs page also lists Tagalog (`tl`) in one of its two lists; treat Tagalog as unsupported unless verified.

Language codes: https://docs.speechmatics.com/speech-to-text/languages

## Read the result

Find the language used from the first word in `results`:

```json
{
  "metadata": {
    "transcription_config": { "language": "auto" },
    "language_identification_config": {
      "expected_languages": ["en", "es", "de", "fr"]
    },
    "type": "transcription",
    "created_at": "2023-02-24T18:22:22.563358Z"
  },
  "results": [
    {
      "alternatives": [
        {
          "confidence": 1.0,
          "content": "It",
          "language": "en",
          "speaker": "UU"
        }
      ],
      "end_time": 0.72,
      "start_time": 0.6,
      "type": "word"
    }
  ]
}
```

`metadata.language_identification` (`LanguageIdentificationResult`):

| Field | Notes |
|---|---|
| `results` | Array of `{ "alternatives": [{ "language", "confidence" }], "start_time", "end_time" }` |
| `error` | `LOW_CONFIDENCE`, `UNEXPECTED_LANGUAGE`, `NO_SPEECH`, `FILE_UNREADABLE`, `OTHER` |
| `message` | Human-readable message |

API spec example:

```json
{
  "results": [
    {
      "alternatives": [
        { "language": "en", "confidence": 0.98 },
        { "language": "fr", "confidence": 0.02 }
      ],
      "start_time": 0.0,
      "end_time": 5.5
    },
    {
      "alternatives": [
        { "language": "en", "confidence": 0.95 },
        { "language": "fr", "confidence": 0.05 }
      ],
      "start_time": 5.6,
      "end_time": 10.0
    }
  ]
}
```

## Use with other features

| Feature | Behavior |
|---|---|
| Custom dictionary | Supported. Applied with the identified language. Language-specific features such as `sounds_like` might not behave as expected |
| Output locale | Not supported with language identification. Jobs combining the two are rejected |
| Translation | Supported. If the identified language matches the target language, the translation contains the transcription sentences. Target languages are not validated at submission; each unsupported pair produces an entry in `metadata.translation_errors`. If the language is specified explicitly and a target language is unsupported, the job is `rejected` |

## Errors

### At submission: unsupported expected language

HTTP 400 if any expected language is not supported:

```json
{
  "code": 400,
  "detail": "Job config JSON is invalid. Error: Language(s) [zz] are not supported for language id",
  "error": "Job rejected"
}
```

### After submission: job rejected

These appear in `job.errors[]` from `GET /jobs/{jobid}`, with `job.status` set to `rejected`.

| Cause | `message` |
|---|---|
| Predicted language is not in `expected_languages` | `The identified language 'en' is not one of the expected languages` |
| Not enough speech, and no `default_language` set | `No speech found for language identification` |
| Confidence too low, and no `low_confidence_action` set. Can occur with too little speech or several languages in similar proportions | `Language identification could not identify any language with sufficient confidence` |
| Predicted language cannot be transcribed | `The identified language 'uz' is not supported for transcription` |
| The language identification stage failed | `Language identification failed` |

```json
{
  "job": {
    "status": "rejected",
    "errors": [
      {
        "message": "The identified language 'en' is not one of the expected languages",
        "timestamp": "2023-02-27T11:57:20.321Z"
      }
    ],
    "config": {
      "language_identification_config": {
        "expected_languages": ["de", "es"]
      }
    },
    "id": "8eef82kaaa"
  }
}
```

### In the transcript: translation errors

Not every language pair can be translated. With `auto`, some targets may be unavailable. These errors appear in the transcript metadata:

```json
{
  "metadata": {
    "created_at": "2023-02-27T12:29:12.607814Z",
    "type": "transcription",
    "transcription_config": {
      "language": "auto"
    },
    "translation_config": {
      "target_languages": ["de", "nn"]
    },
    "translation_errors": [
      {
        "type": "unsupported_translation_pair",
        "message": "Translation from en to nn currently not supported"
      }
    ]
  }
}
```

Supported pairs: https://docs.speechmatics.com/speech-to-text/features/translation#languages
