# Custom dictionary

Docs: https://docs.speechmatics.com/speech-to-text/features/custom-dictionary

Available in Batch, Realtime and agent STT.

Adds a list of custom words per job or session through `transcription_config.additional_vocab`. Use it for words outside the language's vocabulary, such as company or person names.

## Configuration

```json
"transcription_config": {
  "model": "enhanced",
  "language": "en",
  "additional_vocab": [
    {
      "content": "financial crisis"
    },
    {
      "content": "gnocchi",
      "sounds_like": [
        "nyohki",
        "nokey",
        "nochi"
      ]
    },
    {
      "content": "CEO",
      "sounds_like": [
        "C.E.O."
      ]
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `content` | Yes | How the word or phrase is written in the transcript. |
| `sounds_like` | No | Alternative pronunciations. Use when pronunciation is not obvious or there are several. |

The Realtime API also accepts a plain non-empty string as an item, for example `"additional_vocab": ["gnocchi", "bucatini", "bigoli"]` (per `spec/realtime.yaml`).

Rules for `sounds_like`:

- It only works with the main script for the language.
- Japanese (`ja`) supports only full-width Hiragana or Katakana.

## Limits

| Limit | Value | What happens |
|---|---|---|
| Recommended size | No more than 1000 words or phrases per job | Best performance. |
| Maximum items (SaaS on Cloud) | 20,000 | Job or session is rejected. |
| Words per element | 6 | Longer elements are dropped before transcription starts. |
| Characters per word | 4000 | Elements containing a longer word are dropped. |

The per-element limits apply to both `content` and each `sounds_like` entry.

### Dropped elements

```
[{"content":"this is a element that surpasses the limit"}, {"content":"this is ok"}]
```

becomes

```
[{"content":"this is ok"}]
```

For `sounds_like`:

```
[{"content":"this is ok", "sounds_like":["this is ok", "this is a element that surpasses the limit"]}]
```

becomes

```
[{"content":"this is ok", "sounds_like":["this is ok"]}]
```

This dictionary is unaffected: seven elements, each under the 6 word limit.

```
["apple", "orange", "banana", "lemon", "lime", "melon", "pear"]
```

In the Realtime API the server sends an in-band warning message of type `validation_warning` before `RecognitionStarted` when elements are dropped.

### Exceeding 20,000 items

Batch API returns `HTTP 400 Bad Request`:

```json
{
  "code": 400,
  "detail": "Job config JSON is invalid. Error: additional_vocab contains 20001 items which exceeds the maximum allowed (20000)",
  "error": "Job rejected"
}
```

Realtime API sends an in-band error message of type `protocol_error` and closes the WebSocket connection with code `1003`:

```text
additional_vocab has more items (20001) than allowed (20000)
```

## Caching (Realtime)

- Realtime SaaS caches custom dictionaries to reduce session initialization time.
- Reusing an identical dictionary is faster from the second use onwards.
- Cache entries expire when unused for 24 hours.
- On-prem Realtime containers can use a shared custom dictionary cache: https://docs.speechmatics.com/deployments/container/cpu-speech-to-text#how-to-use-a-shared-custom-dictionary-cache

## Performance (Realtime)

Per `spec/realtime.yaml`: `additional_vocab` carries a latency and memory penalty, larger with large lists. Expect a session initialization delay of up to 15 seconds depending on list size.

## Related

To change words after transcription rather than add vocabulary, use word replacement: [formatting.md](formatting.md#word-replacement).
