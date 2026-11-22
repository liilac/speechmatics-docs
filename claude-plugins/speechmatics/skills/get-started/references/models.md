# Models

Source: https://docs.speechmatics.com/speech-to-text/models

Models come in two groups. The Batch API and Realtime API share a set of models selected with the `model` property. Agent STT has its own model, not available on Batch or Realtime.

| API | Models |
|---|---|
| Batch | `enhanced`, `standard`, `melia-1`, `oak-1` |
| Realtime | `enhanced`, `standard`, `melia-1`, `oak-1` |
| Agent STT | `linden-1` |

## Compare the Batch and Realtime models

| Capability | Enhanced | Standard | Melia 1 | Oak 1 |
|---|---|---|---|---|
| `model` value | `enhanced` | `standard` | `melia-1` | `oak-1` |
| Medical specialization | Medical variant available | No | No | Medical native model |
| Accuracy | Highest | High | High | High |
| Turnaround | Fast | Fastest | Fastest on Batch | Fastest on Batch |
| Processing modes | Batch and Realtime | Batch and Realtime | Batch and Realtime | Batch and Realtime |
| Regions | All | All | All | All |
| Language handling | Selected language or pack (auto-detect available) | Selected language or pack (auto-detect available) | Automatic multilingual | Automatic multilingual |
| Diarization | Speaker and channel | Speaker and channel | Speaker and channel | Speaker and channel |
| Language labeling | No | No | Per word | Per word |
| Custom dictionary | Yes | Yes | Not yet | Not yet |
| Confidence scores | Yes | Yes | Not yet | Not yet |
| Speaker identification | Yes | Yes | Not yet | Not yet |
| Speech intelligence | Yes | Yes | Not yet | Not yet |

- Enhanced and Standard are feature-identical. They differ only in accuracy and speed.
- Melia 1: automatic multilingual transcription for 55+ languages, reduced feature set. Accuracy on par with Standard.
- Oak 1: automatic multilingual transcription for healthcare audio, same reduced feature set.
- "Speech intelligence" here covers translation, summarization, topic detection, chapters, sentiment, and audio events.
- Check the release notes for the latest feature support: https://speechmatics.featurebase.app/en/changelog

## Choose a model

- Enhanced: highest accuracy on single-language audio, such as medical, legal, or subtitling work.
- Standard: throughput or latency matter more than maximum accuracy, such as archival transcription, content indexing, or large-scale captioning.
- Melia 1: audio that contains more than one language, including speakers who switch mid-conversation.
- Oak 1: multilingual healthcare audio, such as ambient scribes and dictation tools where speakers switch languages.
- Enhanced Medical: single-language healthcare audio that needs full feature support, such as custom dictionary or confidence scores.
- To transcribe a fixed, known pair of languages with full features, consider a bilingual pack on Enhanced or Standard. See [languages.md](languages.md).

## Specify a model

Set `model` in the transcription config. If omitted, `standard` is used.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  }
}
```

## Melia 1

Multilingual. Returns a single continuous transcript. No language pack selection.

Set `"model": "melia-1"` and `"language": "multi"`. Batch job config:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "melia-1",
    "language": "multi"
  }
}
```

Realtime `StartRecognition` message:

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
    "language": "multi"
  }
}
```

- `"language": "auto"` returns an error. Use `multi`.
- Supports output locale. On Batch and Realtime, `output_locale` also accepts an array of locales, one per language in the audio. See `speechmatics:transcription-features`.
- Supports language hints and per-language output. See `speechmatics:batch-transcription` and `speechmatics:realtime-transcription`.

## Oak 1

Multilingual and tuned for healthcare audio. Returns a single continuous transcript. No language pack selection.

Set `"model": "oak-1"` and `"language": "multi"`. Batch job config:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "oak-1",
    "language": "multi"
  }
}
```

Realtime `StartRecognition` message:

```json
{
  "message": "StartRecognition",
  "audio_format": {
    "type": "raw",
    "encoding": "pcm_s16le",
    "sample_rate": 16000
  },
  "transcription_config": {
    "model": "oak-1",
    "language": "multi"
  }
}
```

- `"language": "auto"` returns an error. Use `multi`.
- Supports output locale, including an array of locales on Batch and Realtime.
- Supports language hints and per-language output.
- Oak 1 is a standalone model, separate from Enhanced Medical. Do not set `domain` for Oak 1.
- Oak 1 transcribes all individual Speechmatics languages. The medical terminology uplift applies to the languages in the medical table in [languages.md](languages.md).

## Regions and endpoints for Melia 1 and Oak 1

| Region | Batch endpoint | Realtime endpoint |
|---|---|---|
| EU1 (Europe) | `eu1.asr.api.speechmatics.com` | `eu.rt.speechmatics.com` |
| US1 (USA) | `us1.asr.api.speechmatics.com` | `us.rt.speechmatics.com` |
| AU1 (Australia) | `au1.asr.api.speechmatics.com` | `au.rt.speechmatics.com` |
| Global | N/A | `global.rt.speechmatics.com` |

For Batch, use only these endpoints (not EU2 or US2).

## Melia 1 and Oak 1 feature gaps on Batch

On Batch they match Enhanced and Standard for core transcription features, including diarization, word timings, punctuation, notifications, and output locale.

Not yet supported on Batch:

- Custom vocabulary and formatting: custom dictionary, find and replace, spoken form output, profanity tagging
- Output detail: confidence scores, smart formatting entities (`enable_entities` without Entity Detection), audio filtering
- Speaker identification
- Speech intelligence: audio events, translation, summarization, chapters, topics, sentiment

## Melia 1 and Oak 1 on Realtime

Supported: Partials and Finals, speaker diarization, channel diarization, word timings, word-level language labeling, output locale, smart formatting, `ForceEndOfUtterance`, and language hints.

Turn handling: the client must detect when the speaker has finished (for example with voice activity detection) and send `ForceEndOfUtterance`. The server then returns a final transcript followed by an `EndOfUtterance` message.

Not yet supported on Realtime:

- Automatic silence-based end of utterance detection. Both models reject `end_of_utterance_silence_trigger` in `conversation_config`.
- Speaker identification
- `max_delay` and `max_delay_mode` latency control
- Custom dictionary
- Smart formatting entities (`enable_entities`) and punctuation overrides
- Disfluency removal, profanity tagging, and audio filtering
- Translation and audio events

Omit unsupported properties from `transcription_config`.

Speaker diarization with Melia 1 and Oak 1 is available on SaaS only, not in on-prem deployments.

## Enhanced Medical

High accuracy on healthcare audio such as ambient scribes and dictation tools. Kept up to date using officially maintained data sources to improve recognition of procedures, medications, conditions, and anatomy.

Set `domain` to `medical` on the Enhanced model:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "domain": "medical"
  }
}
```

- For languages outside the Enhanced Medical list, the Enhanced model still delivers high accuracy on healthcare audio without the medical domain.
- For multilingual healthcare audio, use Oak 1.
- Supported languages: see the medical table in [languages.md](languages.md).

## Operating points

`model` replaces `operating_point`. Existing configs that use `operating_point` continue to transcribe without changes. In SaaS deployments `operating_point` is deprecated; it maps to `model` and accepts the same `enhanced` and `standard` values. Use `model` going forward.

## Agent STT model: Linden 1

Linden 1 powers agent STT. It returns transcription as speaker-attributed segments with turn messages, rather than a running word stream, so the output is ready to pass to an LLM.

Connect to the agent STT endpoint at `/v2/agent` (not the Realtime `/v2` path) and set `"model": "linden-1"` in the `transcription_config` of the `StartRecognition` message:

```json
{
  "message": "StartRecognition",
  "transcription_config": {
    "model": "linden-1",
    "language": "en"
  }
}
```

The agent STT SDK sets the model if you do not. Linden 1 supports the same languages as Realtime transcription; translation is not available. Full configuration: `speechmatics:agent-stt` and https://docs.speechmatics.com/api-ref/agent-stt-websocket.

## Usage reporting names

In the portal usage charts, Enhanced Medical is reported under Enhanced, not as a separate line.
