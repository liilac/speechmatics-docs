---
name: transcription-features
description: Configures Speechmatics Speech to Text features that apply across the Batch API and Realtime API - diarization overview, speaker identification, custom dictionary, translation, Entity Detection, PII Redaction, audio events, audio filtering, feature discovery, and output formatting. Use when a developer asks which modes or models support a feature, or mentions additional_vocab, sounds_like, translation_config, target_languages, AddTranslation, enable_entities, entities_config, detect_advanced_entities, enable_redaction, redaction_config, entity_classes, audio_events_config, audio_filtering_config, volume_threshold, output_locale, punctuation_overrides, transcript_filtering_config, remove_disfluencies, replacements, smart formatting, profanity or disfluency tags, or the /v1/discovery/features endpoint.
---

# Speechmatics transcription features

Feature configuration shared by the Batch API and Realtime API. Every feature here is switched on in the job config (Batch) or the `StartRecognition` message (Realtime).

## When to use another skill

- Accounts, API keys, first request: `speechmatics:get-started`
- Submitting jobs, polling, notifications, batch diarization and batch speaker identification details, language identification: `speechmatics:batch-transcription`
- WebSocket session, partials and finals, realtime diarization and realtime speaker identification details, turn detection: `speechmatics:realtime-transcription`
- Summaries, sentiment, topics, chapters: `speechmatics:speech-intelligence`
- Text to Speech: `speechmatics:text-to-speech`
- LiveKit, Pipecat and similar: `speechmatics:voice-agent-integrations`

## Where config goes

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "translation_config": { "target_languages": ["es"] },
  "audio_events_config": {}
}
```

- Inside `transcription_config`: `output_locale`, `additional_vocab`, `punctuation_overrides`, `enable_entities`, `entities_config`, `enable_redaction`, `redaction_config`, `audio_filtering_config`, `transcript_filtering_config`, `diarization`, `speaker_diarization_config`.
- Sibling of `transcription_config`: `translation_config`, `audio_events_config`.
- Batch: this is the job config. Realtime: the same objects go in `StartRecognition`.

## Availability

| Feature | Batch | Realtime | Agent STT | Model limits |
|---|---|---|---|---|
| Speaker diarization | Yes | Yes | Yes | |
| Channel diarization | Yes | Yes | No | |
| Channel and speaker diarization | No | Yes | No | |
| Speaker identification | Yes | Yes | Yes | Not Melia 1 or Oak 1 |
| Custom dictionary | Yes | Yes | Yes | |
| Translation | Yes | Yes | No | |
| Entity Detection | Yes | No | No | All models |
| PII Redaction | Yes | No | No | |
| Smart formatting (applied to transcript) | Yes | Yes | | All models, on by default |
| Smart formatting entities (`enable_entities`) | Yes | Yes | No | Standard and Enhanced only |
| `punctuation_overrides` | Yes | Yes | No | |
| Audio events | Yes | Yes | No | On-prem containers: GPU models only |
| Audio filtering | Yes | Yes | No | Works better with Enhanced |
| Feature discovery | Covers Batch and Realtime; does not describe agent STT | | | |

Blank cells: the docs do not state it.

## Quick reference

### Custom dictionary

```json
"transcription_config": {
  "model": "enhanced",
  "language": "en",
  "additional_vocab": [
    { "content": "financial crisis" },
    { "content": "gnocchi", "sounds_like": ["nyohki", "nokey", "nochi"] },
    { "content": "CEO", "sounds_like": ["C.E.O."] }
  ]
}
```

- `content` is how the word appears in the transcript. `sounds_like` is optional.
- Recommended maximum 1000 words or phrases per job. SaaS on Cloud rejects more than 20,000 items.
- Any element over 6 words, or containing a word over 4000 characters, is dropped before transcription starts (Realtime sends a `validation_warning`).
- Details: [references/custom-dictionary.md](references/custom-dictionary.md)

### Translation

```json
"translation_config": {
  "target_languages": ["es", "de"],
  "enable_partials": true
}
```

- Maximum 5 target languages. Translation is to and from English (plus Norwegian Bokmål to Nynorsk in Batch).
- Batch: `translations` map in the JSON transcript. Realtime: `AddTranslation` and, with `enable_partials`, `AddPartialTranslation` messages.
- Only JSON output carries translations. TXT and SRT contain the source language only.
- Details: [references/translation.md](references/translation.md)

### Entity Detection and PII Redaction (Batch only)

```json
"transcription_config": {
  "language": "en",
  "enable_entities": true,
  "entities_config": { "detect_advanced_entities": true },
  "enable_redaction": true,
  "redaction_config": { "entity_classes": ["gdpr", "name_given", "credit_card"] }
}
```

- Entity Detection: `enable_entities: true` plus `entities_config.detect_advanced_entities: true`. Results get `"type": "entity"` and an `entity_class` such as `name_given`.
- PII Redaction: `enable_redaction: true` plus `redaction_config.entity_classes` (required, or the job is rejected). Values become labels such as `[name_given]`.
- PII Redaction works alone. If `enable_entities` is also `true`, `detect_advanced_entities` must be `true` or the job is rejected.
- `enable_entities` alone returns smart formatting entities (`cardinal`, `date`, `money`) with `spoken_form` and `written_form`. A job returns one kind or the other, never both.
- On Melia 1 and Oak 1, `enable_entities` is only accepted with `detect_advanced_entities: true`.
- Details and every class: [references/entity-detection-and-redaction.md](references/entity-detection-and-redaction.md)

### Audio events

```json
"audio_events_config": { "types": ["applause", "music"] }
```

- `{}` enables all types: `applause`, `laughter`, `music`.
- Batch: `audio_events` array and `audio_event_summary` (which also counts `silence` and `speech`). Realtime: `AudioEventStarted` and `AudioEventEnded` messages.
- JSON output only.
- Details: [references/audio-events-and-filtering.md](references/audio-events-and-filtering.md)

### Audio filtering

```json
"transcription_config": {
  "language": "en",
  "model": "enhanced",
  "audio_filtering_config": { "volume_threshold": 3.4 }
}
```

- Range `0` to `100`. `0` filters nothing, `100` removes all audio.
- When configured, every word result gains a `volume` field. Use `{}` or `0.0` to get volume labels without filtering.
- Details: [references/audio-events-and-filtering.md](references/audio-events-and-filtering.md)

### Formatting

```json
"transcription_config": {
  "model": "enhanced",
  "language": "en",
  "output_locale": "en-GB",
  "enable_entities": true,
  "punctuation_overrides": { "permitted_marks": [".", ","], "sensitivity": 0.4 },
  "transcript_filtering_config": {
    "remove_disfluencies": true,
    "replacements": [{ "from": "foo", "to": "bar" }]
  }
}
```

| Parameter | Values | Default |
|---|---|---|
| `output_locale` | `en-GB`, `en-US`, `en-AU`, `cmn-Hans`, `cmn-Hant`; an array for Melia 1 and Oak 1 | `cmn-Hans` for Mandarin |
| `enable_entities` | boolean | `false` per the docs page (`spec/realtime.yaml` lists `true` for Realtime; set it explicitly) |
| `punctuation_overrides.permitted_marks` | list of marks, `["all"]`, or `[]` for none | all |
| `punctuation_overrides.sensitivity` | `0` to `1` | `0.5` |
| `transcript_filtering_config.remove_disfluencies` | boolean | `false` |
| `transcript_filtering_config.replacements` | list of `{from, to}`; `from` may be `/regex/` | none |

- Set `output_locale` for English, or spelling may vary within one transcript.
- Profanities (`en`, `it`, `es`) and disfluencies are tagged in `alternatives[].tags`.
- Word replacement is case-sensitive and applied per word after transcription.
- Details: [references/formatting.md](references/formatting.md)

### Diarization and speaker identification

- Set `"diarization"` to `speaker` or `channel` (Realtime also accepts `channel_and_speaker`). Default `none`.
- Speaker identification requires `"diarization": "speaker"`, enrollment clips of 5 to 30 seconds, and at most 50 speaker identifiers per session. Identifiers are tied to model, customer and project.
- Overview and caveats: [references/diarization-and-speaker-identification.md](references/diarization-and-speaker-identification.md). Mode-specific config lives in `speechmatics:batch-transcription` and `speechmatics:realtime-transcription`.

### Feature discovery

```bash
curl "https://au1.asr.api.speechmatics.com/v1/discovery/features"
```

Returns supported languages, output locales, domains, translation pairs and language identification languages. It does not report formatting coverage. Details: [references/feature-discovery.md](references/feature-discovery.md)

## Gotchas

- Entity Detection and PII Redaction are Batch only. Do not add them to a Realtime session.
- `entities_config` is only accepted when `enable_entities` is `true`.
- PII Redaction cannot be combined with smart formatting entities, and redacted transcripts have no `spoken_form` or `written_form`.
- The `pii` group is broad: it also redacts dates, times, amounts of money and organization names.
- Per the docs, timestamps, confidence scores, word tagging and regional spelling are only available in the original language. Translated sentences carry only sentence-level `start_time` and `end_time`.
- Realtime sessions may take up to 5 seconds longer to close while translations finalize.
- Disabling punctuation may slightly reduce speaker diarization accuracy. Keep punctuation at defaults for best translation quality.
- Regex flags go inside the pattern: `/(?i)^hello$/` works, `/hello/i` is treated as a plain word.
- An invalid replacement rule fails the request before transcription starts.
- Realtime custom dictionaries are cached on SaaS; an identical dictionary initializes faster from the second use, and entries expire after 24 hours unused.

## References

- [references/custom-dictionary.md](references/custom-dictionary.md): `additional_vocab` rules, limits, caching, error payloads.
- [references/translation.md](references/translation.md): config, Batch and Realtime output, language list, full Python samples.
- [references/entity-detection-and-redaction.md](references/entity-detection-and-redaction.md): Entity Detection, PII Redaction, every entity class and group, unsupported languages, Python sample.
- [references/audio-events-and-filtering.md](references/audio-events-and-filtering.md): event types, Batch and Realtime output, Python samples, volume threshold mechanics.
- [references/formatting.md](references/formatting.md): output locale, profanities, disfluencies, word replacement and regex, smart formatting classes, punctuation.
- [references/diarization-and-speaker-identification.md](references/diarization-and-speaker-identification.md): modes, enrollment and identification, scoping rules, on-prem requirements.
- [references/feature-discovery.md](references/feature-discovery.md): endpoint and response structure.
