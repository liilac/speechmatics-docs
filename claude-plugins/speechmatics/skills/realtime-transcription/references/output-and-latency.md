# Realtime output and latency

Docs: https://docs.speechmatics.com/speech-to-text/realtime/output

Which messages the server returns, and how often, depends on the `StartRecognition` configuration.

## Finals and Partials

- Finals (`AddTranscript`) are the best transcription for a span of audio and are never updated once emitted.
- Partials (`AddPartialTranscript`) are emitted immediately as audio arrives and may be revised as more context is processed.

| Type | Latency | Stability | Best for |
| --- | --- | --- | --- |
| Final | ~0.7–2 s | Definitive, never revised | Accurate transcripts, subtitles |
| Partial | <500 ms | May be revised | Live captions, voice interfaces |

With both enabled, Partials arrive first, then the Final:

```
[Partial]: Hello
[Partial]: Hello welcome to
[Final]:   Hello, welcome to Speechmatics.
```

## Latency settings

Low-latency configuration. The `"type": "transcription"` wrapper below is as shown in the docs; `StartRecognition` itself has no `type` field, so send only the `transcription_config` part. See [configuration.md](configuration.md).

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en",
    "model": "enhanced",
    "max_delay": 0.7,
    "max_delay_mode": "flexible",
    "enable_partials": true
  }
}
```

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `max_delay` | number | 4 | Allowed 0.7 to 4 seconds. The delay between the end of a spoken word and returning the Final. A very small additional latency applies while the server sends the transcript to the client. |
| `max_delay_mode` | string | `flexible` | `fixed` or `flexible`. `flexible` allows additional time for smart formatting. |
| `enable_partials` | boolean | `false` | Whether to receive Partials before Finals. |

### Accuracy and latency trade-offs

Experiment with `max_delay` to find the right trade-off. Starting points:

| `max_delay` | Use | Accuracy relative to Batch |
| --- | --- | --- |
| 0.7–1.5 s | Ultra-fast response, for example in voice agent applications | Minor degradation, less than 5% |
| 2.0 s | Most use cases, such as captioning or contact centers | Negligible degradation, around 1% |
| 4.0 s | Accuracy over latency, such as legal transcription | Equivalent. Use Partials for early feedback. |

## Partial transcripts

Enable with `enable_partials: true`:

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en",
    "model": "enhanced",
    "max_delay": 2,
    "enable_partials": true
  }
}
```

- Partials are typically returned in less than 500 milliseconds.
- Partial latency is not affected by `max_delay`.
- On each Final, the server immediately sends a Partial with any remaining words that have not been finalized.
- Accuracy is usually 10–25% lower than the Final, including punctuation and capitalization.
- The `confidence` field on Partials has no meaning. Do not rely on it.

## Smart formatting and max_delay_mode

Smart formatting writes numbers, dates, currencies, and other entities in their written form.

- `flexible` (default): when an entity is being spoken, the Final is delayed until the entity is fully spoken so it can be formatted properly. Use in most cases.
- `fixed`: for strict latency requirements. The Final is not delayed, with some reduction in accuracy and readability for numbers, currencies, and dates.

Example outputs for the phrase "I am 35.":

Finals only, default `max_delay_mode`:

- (Final): I am 35.

Partials enabled, default `max_delay_mode`:

- (Partial): I
- (Partial): I am
- (Partial): I am third
- (Partial): I am 30
- (Final): I am 35.

Partials enabled, `max_delay_mode: "fixed"`:

- (Partial): I
- (Final): I am
- (Partial): third
- (Final): 30
- (Partial): five
- (Final): five.

Resulting text: "I am 30 five."

## Reading a transcript message

- `metadata.transcript`: the formatted text for the message, ready to concatenate.
- `results[]`: one item per `word`, `punctuation`, or `entity`, with `start_time`, `end_time`, and `alternatives[0]` holding `content`, `confidence`, and optionally `language`, `speaker`, `display`, `tags`.
- Punctuation items carry `attaches_to` and `is_eos` (end of sentence).

Building text from `results` (from the docs' JavaScript radio example): write a space before each `word`, write `alternatives[0].content`, and break the line when `is_eos` is true.

```javascript
for (const result of data.results) {
  if (result.type === "word") {
    process.stdout.write(" ");
  }
  process.stdout.write(`${result.alternatives?.[0].content}`);
  if (result.is_eos) {
    process.stdout.write("\n");
  }
}
```

Full schemas: [protocol.md](protocol.md#addtranscript-and-addpartialtranscript).

## LanguageInfo

Melia 1 and Oak 1 label each word with the language it was spoken in, so one session can return words in more than one language. `LanguageInfo` tells the client how to render words of a given language. The server sends it once per language code, immediately before that language first appears in an `AddPartialTranscript` or `AddTranscript`.

Use it to set word spacing and text direction while building the transcript. This matters for right-to-left scripts such as Arabic and Hebrew.

```json
{
  "message": "LanguageInfo",
  "language": "ar",
  "word_delimiter": " ",
  "writing_direction": "right-to-left",
  "partial": true
}
```

| Field | Type | Description |
| --- | --- | --- |
| `language` | string | The detected language code. |
| `word_delimiter` | string | The delimiter to place between words of this language. |
| `writing_direction` | string | `left-to-right` or `right-to-left`. |
| `partial` | boolean | Optional. Present only when `true`: a Partial transcript triggered the message. |

`RecognitionStarted.language_pack_info` also carries a `word_delimiter` and `writing_direction` for the session's language pack.

## App usage tracking

For integrations where customers use their own Speechmatics API keys, aggregate application usage (unique users, processing hours, languages used, and more). Contact [Support](https://support.speechmatics.com) to enable the feature first.

Once enabled, add the `sm-app` query parameter to the connection URL:

```bash
wss://au.rt.speechmatics.com/v2?sm-app=YourAppID
```
