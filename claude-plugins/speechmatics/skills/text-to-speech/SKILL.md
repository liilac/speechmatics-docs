---
name: text-to-speech
description: Generates speech audio from text with the Speechmatics Text to Speech (TTS) API. Covers the preview endpoint https://preview.tts.speechmatics.com/generate/<voice_id>, Bearer API key auth, the four English voices (sarah, theo, megan, jack), the output_format query parameter (wav_16000, pcm_16000), streaming playback of the response, cURL and Python requests samples, the speechmatics-tts Python SDK (AsyncClient, Voice, OutputFormat), text preparation best practices, latency, and preview limits. Use when a developer wants to synthesize speech, convert text to audio, pick a Speechmatics voice, save or stream WAV or PCM output, or asks about TTS pricing, languages, rate limits, or deployment.
---

# Speechmatics Text to Speech

Docs: https://docs.speechmatics.com/text-to-speech/quickstart

Text to Speech (TTS) converts text into natural-sounding speech over a single HTTP request. It is in preview and free to use; features and pricing may change.

## When to use another skill

- Creating an account or API key: `speechmatics:get-started`
- TTS inside LiveKit, Pipecat or similar frameworks: `speechmatics:voice-agent-integrations`
- Transcribing audio: `speechmatics:batch-transcription`, `speechmatics:realtime-transcription`

## Prerequisites

- An API key from the portal: https://portal.speechmatics.com/settings/api-keys. Store it as a managed secret.
- For the Python `requests` sample: `pip install requests`. For the SDK sample: `pip install speechmatics-tts`.

## Endpoint

```
POST https://preview.tts.speechmatics.com/generate/<voice_id>
```

| Part | Value |
|---|---|
| Auth header | `Authorization: Bearer YOUR_API_KEY` |
| Content type | `Content-Type: application/json` |
| Body | `{"text": "..."}` |
| Query parameter | `output_format` (optional): `wav_16000` (default) or `pcm_16000` |
| Response body | Audio bytes, streamed. HTTP 200 on success. |

## Voices

| Voice ID | Description |
|---|---|
| `sarah` | English Female (UK) |
| `theo` | English Male (UK) |
| `megan` | English Female (US) |
| `jack` | English Male (US) |

English only. The voice ID is the last path segment of the URL.

## Output formats

| `output_format` | Container | Sample rate | Bit depth | Channels | Byte order |
|---|---|---|---|---|---|
| `wav_16000` (default) | Complete WAV file with headers | 16 kHz | 16-bit signed integer | Mono | |
| `pcm_16000` | Raw PCM, no header | 16 kHz | 16-bit signed integer | Mono | Little-endian |

Usage: append `?output_format=pcm_16000`, or omit the parameter for WAV.

## Minimal examples

### cURL

```bash
curl -X POST "https://preview.tts.speechmatics.com/generate/sarah" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Welcome to the future of speech technology!"}' \
  --output output.wav
```

### Python (requests)

```python
import requests

url = "https://preview.tts.speechmatics.com/generate/sarah"
headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}
data = {
    "text": "Welcome to the future of speech technology!"
}

SAMPLE_RATE = 16000

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    wav_data = response.content

    with open("output.wav", "wb") as wav_file:
        wav_file.write(wav_data)

    # Calculate actual audio duration
    audio_bytes = len(wav_data) - 44  # Remove WAV header
    samples = audio_bytes // 2  # 16-bit = 2 bytes per sample
    duration = samples / SAMPLE_RATE

    print(f"Speech synthesis completed! Saved {len(wav_data)} bytes as output.wav")
    print(f"Audio duration: {duration:.2f} seconds ({samples:,} samples)")
else:
    print(f"Error: {response.status_code}")
    print(f"Response: {response.text}")
```

### Python (SDK)

```python
# pip install speechmatics-tts

import asyncio

from speechmatics.tts import AsyncClient, Voice, OutputFormat

# Generate speech data from text and save to WAV file
async def main():
    async with AsyncClient() as client:
        async with await client.generate(
            text="Welcome to the future of audio generation from text!",
            voice=Voice.SARAH,
            output_format=OutputFormat.WAV_16000
        ) as response:
            audio = b''.join([chunk async for chunk in response.content.iter_chunked(1024)])
            with open("output.wav", "wb") as wav:
                wav.write(audio)


# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
```

The docs sample constructs `AsyncClient()` with no arguments and does not show how the SDK receives the API key. Do not guess a parameter or environment variable name; check the SDK's own documentation.

## Streaming

- Audio is streamed in the response. Start consuming or playing it before the request completes.
- The first audio chunk typically returns in under 200 ms. Later chunks arrive faster than real time.
- Output streaming only. Full bidirectional streaming (sending text incrementally) is not supported.

## Preparing text

- Use proper punctuation: periods, commas and question marks improve speech flow.
- Spell out abbreviations: "Doctor", not "Dr.".
- Spell out numbers: "Twenty-five dollars", not "$25".
- Combine several short texts into one longer request when possible.
- For lowest latency, send smaller amounts of text. Long text is split server-side.
- Cache generated audio to avoid repeat calls for identical text.

## Limits and gotchas

- English only, four voices.
- No control over speed, pitch or emphasis. Prosody is driven by the text.
- No webhooks or callbacks.
- No documented maximum text length. Long paragraphs are accepted.
- On rate limit errors, retry with exponential backoff.
- During the preview, input text and generated audio are stored to improve the service.
- The host is `preview.tts.speechmatics.com`, not the STT hosts.
- The duration math in the `requests` sample assumes a 44-byte WAV header. Do not apply it to `pcm_16000` output; for PCM, duration is `len(bytes) / 2 / 16000` seconds.

## Deployment

Available as the managed service or deployed in your own environment. For on-prem deployment, contact sales: https://www.speechmatics.com/speak-to-sales

## References

- [references/preview-details.md](references/preview-details.md): read for latency, streaming scope, concurrency, data retention, pricing statements, supported use cases, support channels, and known inconsistencies in the docs.
