# Feature discovery

Docs: https://docs.speechmatics.com/speech-to-text/features/feature-discovery

Returns the current capabilities of the service so an application can pick up new languages and features dynamically. Covers Batch and Realtime. The response does not describe agent STT capabilities.

## Request

```
curl "https://eu1.asr.api.speechmatics.com/v1/discovery/features"
```

A plain GET. The docs example sends no authorization header.

## Response

The docs document these properties:

- `metadata`
  - `language_pack_info`: for each supported language, its full name plus any domain language optimizations and output locales.
- `batch`: capabilities of the Batch API.
  - `transcription`
    - `languages`: supported ISO language codes.
    - `locales`: languages with a supported output locale.
    - `domains`: languages with a supported domain language optimization.
  - `translation`: all supported translation pairs.
  - `languageid`: languages supported by language identification.

The docs page details only the `metadata` and `batch` properties. Inspect the live response for anything else.

## What it does not report

Formatting coverage (smart formatting, disfluencies, profanities) is not reported. Use [formatting.md](formatting.md) for language support of those features.

## Related docs

- Languages: https://docs.speechmatics.com/speech-to-text/languages
- Translation pairs: [translation.md](translation.md)
- Language identification: `speechmatics:batch-transcription`
