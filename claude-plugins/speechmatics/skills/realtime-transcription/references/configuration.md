# Realtime configuration

Docs:

- Input: https://docs.speechmatics.com/speech-to-text/realtime/input
- StartRecognition reference: https://docs.speechmatics.com/api-ref/realtime-transcription-websocket#start-recognition

All configuration is sent in the `StartRecognition` message. Required top-level fields: `message`, `audio_format`, `transcription_config`. Optional: `translation_config`, `audio_events_config`.

Docs versus schema: several docs snippets wrap the config as `{ "type": "transcription", "transcription_config": {...} }` while saying to include it in `StartRecognition`. The API schema for `StartRecognition` has no `type` field: send `"message": "StartRecognition"`, `audio_format`, and the `transcription_config` object. Snippets in these reference files that start with `"type": "transcription"` are copied from the docs; use only their `transcription_config` part.

## audio_format

Two input types: `raw` and `file`. Use `raw` unless there is a specific reason to use `file`.

### raw

Raw audio samples. All three fields are mandatory.

| Field | Type | Values |
| --- | --- | --- |
| `type` | string | `raw` |
| `encoding` | string | `pcm_f32le`, `pcm_s16le`, `mulaw` |
| `sample_rate` | integer | The sample rate of the audio in Hz. |

```json
{ "type": "raw", "encoding": "pcm_s16le", "sample_rate": 44100 }
```

### file

| Field | Type | Values |
| --- | --- | --- |
| `type` | string | `file` |

Send audio encoded in a recognized format. The `AddAudio` messages must provide all the file contents, including any headers. Split the file into reasonably sized messages rather than sending it all at once.

Supported formats: `wav`, `mp3`, `aac`, `ogg`, `mpeg`, `amr`, `m4a`, `mp4`, `flac`.

### Sending audio

After `RecognitionStarted`, send audio as binary WebSocket data, encoded as declared in `audio_format`. For browser capture of raw audio, use the [`@speechmatics/browser-audio-input`](https://www.npmjs.com/package/@speechmatics/browser-audio-input) package.

## transcription_config

`language` is the only required field.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `language` | string | required | Language model for the audio, normally an ISO language code. Must be consistent with any language code used in the endpoint URL. Use `multi` with `melia-1` and `oak-1`. |
| `model` | string | `standard` | `standard`, `enhanced`, `melia-1`, or `oak-1`. See `speechmatics:get-started` for model choice. |
| `operating_point` | string | | Deprecated. Kept for backward compatibility only. Use `model`. Same values as `model`. |
| `language_hints` | array of string | | Languages expected in the audio. `melia-1` and `oak-1` only. See [Language hints](#language-hints). |
| `domain` | string | | Requests a specialized model based on `language` but optimized for a field, for example `finance` or `medical`. |
| `output_locale` | string | | Locale for the output, for example `en-US`. Minimum length 1. |
| `additional_vocab` | array | empty | Custom dictionary. Maximum 20,000 items. Each item is a non-empty string, or an object with `content` (required) and `sounds_like` (array of at least one non-empty string). |
| `diarization` | string | `none` | `none`, `speaker`, `channel`, or `channel_and_speaker`. See [diarization.md](diarization.md). |
| `channel_diarization_labels` | array of string | | Labels for each channel, for `channel` and `channel_and_speaker` diarization. |
| `speaker_diarization_config` | object | | See [diarization.md](diarization.md#speaker_diarization_config-reference). |
| `max_delay` | number | 4 | 0.7 to 4. Delay in seconds between the end of a spoken word and its Final. See [output-and-latency.md](output-and-latency.md). |
| `max_delay_mode` | string | `flexible` | `flexible` or `fixed`. `flexible` allows extra time for smart formatting. |
| `enable_partials` | boolean | `false` | Whether to send `AddPartialTranscript` messages as well as Finals (per the output docs page; the schema description of this field names `AddPartialTranslation`/`AddTranslation` instead, which `translation_config.enable_partials` controls). |
| `enable_entities` | boolean | `true` | Exposes each smart formatting entity's structure (`entity` results with `entity_class`, `spoken_form`, `written_form`) in the output. |
| `audio_filtering_config` | object | | `volume_threshold` (number, 0 to 100): a lower limit on the volume of processed audio. |
| `transcript_filtering_config` | object | | `remove_disfluencies` (boolean); `replacements` (array of `{ "from": "...", "to": "..." }`, both required). |
| `punctuation_overrides` | object | | `permitted_marks` (array; each item a single character or `all`, the default; unsupported marks are ignored); `sensitivity` (number 0 to 1, default 0.5; higher values produce more punctuation). |
| `conversation_config` | object | | `end_of_utterance_silence_trigger` (number, 0 to 2, default 0; 0 disables). Enhanced and Standard only; Melia 1 and Oak 1 reject it. See [turn-detection.md](turn-detection.md). |

Performance note for `additional_vocab`: there is a latency and memory penalty, especially with a large list. Expect a delay of up to 15 seconds when a session with `additional_vocab` initializes, depending on list size.

For the behavior of the custom dictionary, formatting, punctuation, disfluency removal, word replacement, and audio filtering, see `speechmatics:transcription-features`.

Example:

```json
{
  "message": "StartRecognition",
  "audio_format": { "type": "raw", "encoding": "pcm_f32le", "sample_rate": 16000 },
  "transcription_config": {
    "language": "en",
    "model": "enhanced",
    "output_locale": "en-US",
    "additional_vocab": ["gnocchi", "bucatini", "bigoli"],
    "diarization": "speaker",
    "max_delay": 1.0,
    "enable_partials": true
  }
}
```

## Language hints

Language hints are optional and apply only to Melia 1 and Oak 1, which detect supported languages automatically. For Enhanced and Standard, set `language` to a supported language instead.

Set `language_hints` to the languages expected in the audio. Hints have two effects:

- Language labels are restricted to the hinted languages. Every word is labeled with one of the listed languages. With one hint, every word gets that label. With two or more, labels can switch between the hinted languages.
- Transcription is biased toward the hinted languages. This can improve accuracy, especially for short utterances and similar-sounding languages. Speech in other languages is less likely to be transcribed, but can still appear, labeled as one of the hinted languages.

```json
{
  "message": "StartRecognition",
  "audio_format": {
    "type": "raw",
    "encoding": "pcm_s16le",
    "sample_rate": 16000
  },
  "transcription_config": {
    "model": "melia-1",
    "language": "multi",
    "language_hints": ["en", "ar"]
  }
}
```

Hints restrict labels rather than only biasing detection: the model cannot label a word with a language that was not hinted. If the audio may contain unpredictable languages, omit `language_hints`.

To render each detected language correctly, handle the `LanguageInfo` message. See [output-and-latency.md](output-and-latency.md#languageinfo).

## translation_config

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `target_languages` | array of string | required | Languages to translate to from the source `language`, as ISO language codes. |
| `enable_partials` | boolean | `false` | Whether to send `AddPartialTranslation` messages as well as `AddTranslation`. |

```json
"translation_config": { "target_languages": ["es", "de"], "enable_partials": true }
```

Related warnings: `unsupported_translation_pair`, `empty_translation_target_list`. Requesting too many target languages gives an `invalid_config` error. See `speechmatics:transcription-features` for supported pairs and limits.

## audio_events_config

| Field | Type | Description |
| --- | --- | --- |
| `types` | array of string | Audio event types to enable. |

```json
"audio_events_config": { "types": ["applause", "music"] }
```

Results arrive as `AudioEventStarted` and `AudioEventEnded`. See `speechmatics:transcription-features` for the supported event types.

## Changing config mid-session

Send `SetRecognitionConfig` with a `transcription_config` containing only these fields: `language` (must match the original), `max_delay`, `max_delay_mode`, `audio_filtering_config`, `enable_partials`, `conversation_config`. Any other parameter, or a changed language, results in an error.

## Model-specific rules

| Rule | Standard / Enhanced | Melia 1 / Oak 1 |
| --- | --- | --- |
| `language` | A supported language code | `multi` |
| `language_hints` | Not used | Optional |
| `conversation_config.end_of_utterance_silence_trigger` | Supported | Rejected |
| `ForceEndOfUtterance` | Supported | Supported |
| Speaker identification (`GetSpeakers`, `get_speakers`, `speakers`) | Supported | Not supported |
| `LanguageInfo` message | Not sent | Sent once per detected language |
| `alternatives[].language` | Always the requested language | Detected per word |
