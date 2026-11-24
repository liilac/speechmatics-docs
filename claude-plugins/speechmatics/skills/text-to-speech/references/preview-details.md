# Text to Speech preview details

Docs: https://docs.speechmatics.com/text-to-speech/quickstart

The docs for Text to Speech (TTS) consist of one quickstart page with an FAQ. Everything below comes from that page. Where the page is silent, say so rather than guess.

## Status

- In preview and free to use. Features and pricing may change.
- Feedback is requested through GitHub discussions: https://github.com/orgs/speechmatics/discussions

## Intended use cases

- Voice AI: voice assistants, chatbots, IVR systems.
- Translation: realtime translation of live events or media.
- Accessibility: screen readers and assistive technologies.
- Content creation: podcasts, dubbing, audiobooks, voice-overs.
- Media production: news broadcasts and automated announcements.

## API surface

| Item | Value |
|---|---|
| Method and URL | `POST https://preview.tts.speechmatics.com/generate/<voice_id>` |
| Auth | `Authorization: Bearer YOUR_API_KEY` |
| Request body | JSON with a `text` string |
| `output_format` query parameter | `wav_16000` (default), `pcm_16000` |
| Voice IDs | `sarah`, `theo`, `megan`, `jack` |
| Success | HTTP 200, audio bytes in the body |

The page documents no other request fields, no other endpoints, and no error code table. The `requests` sample treats any non-200 status as an error and prints `response.status_code` and `response.text`.

### Audio format details

`wav_16000`:

- Complete WAV file with headers
- 16 kHz sample rate
- 16-bit signed integer
- Mono

`pcm_16000`:

- Raw PCM data
- 16 kHz sample rate
- 16-bit signed integer
- Mono
- Little-endian

### SDK names used in the docs sample

| Name | Use |
|---|---|
| Package | `speechmatics-tts` (`pip install speechmatics-tts`) |
| Import | `from speechmatics.tts import AsyncClient, Voice, OutputFormat` |
| Client | `async with AsyncClient() as client` |
| Call | `await client.generate(text=..., voice=Voice.SARAH, output_format=OutputFormat.WAV_16000)`, used as an async context manager |
| Reading audio | `response.content.iter_chunked(1024)` |

Only `Voice.SARAH` and `OutputFormat.WAV_16000` appear in the docs. Other enum member names are not documented there.

## FAQ answers

### Core functionality

| Question | Answer |
|---|---|
| Languages | English. More languages are planned. Request one on GitHub discussions. |
| Voices | Four at present. More will be added during the preview. |
| Speed, pitch, emphasis control | Not yet. Prosody is driven by the text content. |

### Technical

| Question | Answer |
|---|---|
| Latency | First audio chunk typically in under 200 ms; subsequent chunks faster than real time. |
| Streaming | Streaming audio output is supported (play audio as it arrives). Full bidirectional streaming is not; it is planned. |
| Concurrency and rate limits | High concurrency is expected at release. No numeric limits are published. On rate limit errors, retry with exponential backoff. |
| Maximum text size | No stated maximum. Text is split server-side and long paragraphs are handled. Smaller inputs give the lowest latency. |
| Webhooks or callbacks | Not available. |
| Official SDKs | The FAQ says official SDKs are not available yet and to use standard HTTP requests. The same page shows a Python SDK sample using `speechmatics-tts`. See "Inconsistencies" below. |

### Commercial

| Question | Answer |
|---|---|
| Price | Free during the preview. The page says pricing would be announced in September 2025 with billing starting 1 October, at least 2 weeks after the announcement, with a generous free tier. Those dates have passed; check the Speechmatics pricing page for the current position. |
| Commercial use | For commercial use and enterprise pricing, contact sales: https://www.speechmatics.com/speak-to-sales |
| Data handling | During the preview, input text and generated audio are stored to help improve the service. In production, both non-retentive and data-retentive options are planned; customers allowing retention may be eligible for discounted pricing. |

### Deployment

Consumable as the managed service or deployed in your own environment. For on-prem options, contact sales.

### Support

Feedback, bug reports and feature requests: https://github.com/orgs/speechmatics/discussions

## Inconsistencies in the docs

- SDK availability. The FAQ states no official SDKs exist; the quickstart tab "Python (SDK)" uses `speechmatics-tts`. Treat the SDK sample as usable, and fall back to plain HTTP if the package behaves differently.
- SDK authentication. The SDK sample never passes an API key. The mechanism is undocumented on this page.
- Dates. Language expansion "in 2025" and the September/October 2025 pricing timeline are stale. Do not quote them as upcoming.

## More

- Examples: https://github.com/speechmatics/speechmatics-academy/tree/main/basics/03-text-to-speech
- Community: https://www.reddit.com/r/Speechmatics
- Framework plugins (LiveKit, Pipecat): `speechmatics:voice-agent-integrations`
