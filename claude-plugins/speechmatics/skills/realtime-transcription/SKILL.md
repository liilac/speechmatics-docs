---
name: realtime-transcription
description: Covers streaming Speech to Text over the Speechmatics Realtime WebSocket API - endpoints, handshake and authentication, the StartRecognition message, audio_format and AddAudio, every client and server message (AddPartialTranscript, AddTranscript, EndOfUtterance, Info, Warning, Error), close codes, max_delay and latency tuning, realtime diarization, speaker identification, turn detection, session limits, and the Python microphone and FFmpeg guides. Use when writing or debugging code that transcribes live audio, a microphone, or a media stream; when a user mentions wss://*.rt.speechmatics.com, speechmatics-rt, @speechmatics/real-time-client, enable_partials, max_delay_mode, conversation_config, end_of_utterance_silence_trigger, ForceEndOfUtterance, AddChannelAudio, GetSpeakers, language_hints, or a Realtime close code such as 1008 or 4005.
---

# Realtime transcription

Transcribe audio as it is streamed, over one WebSocket connection to the Speechmatics Realtime API. Results arrive continuously as Partial and Final transcripts.

## When to use this skill

Use it for streaming Speech to Text (STT): live captions, dictation, media streams, contact centers, any word-by-word realtime transcript.

Use a sibling skill instead when:

- The audio is a pre-recorded file and results are not needed live: `speechmatics:batch-transcription`.
- The goal is turn-based, speaker-attributed segments for a voice agent's LLM: `speechmatics:agent-stt` (Linden 1, `/v2/agent`).
- The user builds on LiveKit, Pipecat, Twilio, Vapi, or the Voice SDK: `speechmatics:voice-agent-integrations`.
- The question is about API keys, temporary keys, regions, models, or languages: `speechmatics:get-started`.
- The question is about a feature's own options (custom dictionary, translation, audio events, formatting, punctuation): `speechmatics:transcription-features`.

## Prerequisites

- An API key from the [portal](https://portal.speechmatics.com/settings/api-keys). Store it as a managed secret. Enterprise customers may need to contact [Support](https://support.speechmatics.com).
- No-code trial: the [portal Realtime page](https://portal.speechmatics.com/jobs/create/real-time).

## Endpoints and authentication

| Region | WebSocket URL |
| --- | --- |
| Global (auto-routed to nearest region) | `wss://global.rt.speechmatics.com/v2` |
| EU1 | `wss://eu.rt.speechmatics.com/v2` |
| US1 | `wss://us.rt.speechmatics.com/v2` |
| AU1 | `wss://au.rt.speechmatics.com/v2` |

Pin a regional endpoint for data residency; the global endpoint may route to any region.

- Server side: send `Authorization: Bearer YOUR_API_KEY` on the handshake request.
- Browser: pass a Realtime temporary key as a query parameter, `wss://global.rt.speechmatics.com/v2?jwt=<temporary-key>`. Never ship the long-lived API key to a browser. See `speechmatics:get-started` for creating temporary keys.
- Handshake responses: `101` connected, `400` malformed request, `401` invalid API key or temporary key, `405` method is not `GET`.

## Session flow

1. Open the WebSocket. The server may send `Info` messages (`recognition_quality`, `concurrent_session_usage`) straight after the handshake.
2. Send `StartRecognition` (JSON) with `audio_format` and `transcription_config`.
3. Wait for `RecognitionStarted`.
4. Send audio as binary WebSocket messages (`AddAudio`). The server acknowledges each with `AudioAdded` carrying an incrementing `seq_no`.
5. Receive `AddPartialTranscript` (if enabled) and `AddTranscript` as audio is processed.
6. Send `EndOfStream` with `last_seq_no` set to the number of `AddAudio` messages sent.
7. Receive the remaining `AddTranscript` messages, then `EndOfTranscript`. Close the connection.

After any `Error` message the transcription is terminated and the connection is closed.

Minimal `StartRecognition`:

```json
{
  "message": "StartRecognition",
  "audio_format": { "type": "raw", "encoding": "pcm_s16le", "sample_rate": 16000 },
  "transcription_config": {
    "language": "en",
    "model": "enhanced",
    "max_delay": 2,
    "enable_partials": true
  }
}
```

## Quickstart: Python

```
pip install speechmatics-rt pyaudio
```

`pyaudio` is required for microphone input.

```python
import asyncio
from speechmatics.rt import (
    AudioEncoding, AudioFormat, AuthenticationError,
    Microphone, ServerMessageType, TranscriptResult,
    TranscriptionConfig, AsyncClient,
)

API_KEY = YOUR_API_KEY

# Set up config and format for transcription
audio_format = AudioFormat(
    encoding=AudioEncoding.PCM_S16LE,
    sample_rate=16000,
    chunk_size=4096,
)
config = TranscriptionConfig(
    model="enhanced",
    language="en",
    max_delay=0.7,
)

async def main():

    # Set up microphone
    mic = Microphone(
        sample_rate=audio_format.sample_rate,
        chunk_size=audio_format.chunk_size
    )
    if not mic.start():
        print("Mic not started — please install PyAudio")

    try:
        async with AsyncClient(api_key=API_KEY) as client:
            # Handle ADD_TRANSCRIPT message
            @client.on(ServerMessageType.ADD_TRANSCRIPT)
            def handle_finals(msg):
                if final := TranscriptResult.from_message(msg).metadata.transcript:
                    print(f"[Final]: {final}")

            try:
                # Begin transcribing
                await client.start_session(
                    transcription_config=config,
                    audio_format=audio_format
                )
                while True:
                    await client.send_audio(
                        await mic.read(
                            chunk_size=audio_format.chunk_size
                        )
                    )
            except KeyboardInterrupt:
                pass
            finally:
                mic.stop()

    except AuthenticationError as e:
        print(f"Auth error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

To also receive Partials, set `enable_partials=True` in `TranscriptionConfig` and add:

```python
@client.on(ServerMessageType.ADD_PARTIAL_TRANSCRIPT)
def handle_partials(msg):
    if partial := TranscriptResult.from_message(msg).metadata.transcript:
        print(f"[Partial]: {partial}")
```

## Quickstart: JavaScript

```
npm install @speechmatics/real-time-client @speechmatics/auth
```

Core calls (the full Node.js + `sox` microphone script is in [references/code-examples.md](references/code-examples.md)):

```javascript
import { createSpeechmaticsJWT } from "@speechmatics/auth";
import { RealtimeClient } from "@speechmatics/real-time-client";

const client = new RealtimeClient();

client.addEventListener("receiveMessage", ({ data }) => {
  if (data.message === "AddTranscript") {
    console.log(`[Final]:   ${data.metadata.transcript}`);
  } else if (data.message === "AddPartialTranscript") {
    console.log(`[Partial]: ${data.metadata.transcript}\r`);
  } else if (data.message === "Error") {
    console.error(`Error [${data.type}]: ${data.reason}`);
  }
});

const jwt = await createSpeechmaticsJWT({ type: "rt", apiKey, ttl: 60 });

await client.start(jwt, {
  transcription_config: {
    model: "enhanced",
    max_delay: 0.7,
    language: "en",
    enable_partials: true,
  },
  audio_format: { type: "raw", encoding: "pcm_s16le", sample_rate: 44100 },
});

client.sendAudio(chunk);                      // call for each audio chunk
client.stopRecognition({ noTimeout: true });  // when finished
```

For raw audio capture in the browser, use the `@speechmatics/browser-audio-input` npm package.

## Essential configuration

`audio_format` (required):

| Type | Fields | Notes |
| --- | --- | --- |
| `raw` (recommended) | `encoding`: `pcm_f32le`, `pcm_s16le`, or `mulaw`; `sample_rate`: integer Hz | Both fields are mandatory. |
| `file` | none | Send the whole file including headers, split across `AddAudio` messages. Supported: `wav`, `mp3`, `aac`, `ogg`, `mpeg`, `amr`, `m4a`, `mp4`, `flac`. |

`transcription_config` essentials (full table in [references/configuration.md](references/configuration.md)):

| Field | Values | Default | Notes |
| --- | --- | --- | --- |
| `language` | ISO code, or `multi` | required | Melia 1 and Oak 1 require `multi`. |
| `model` | `standard`, `enhanced`, `melia-1`, `oak-1` | `standard` | `operating_point` is deprecated; use `model`. |
| `max_delay` | 0.7 to 4 seconds | 4 | Delay between end of a spoken word and its Final. |
| `max_delay_mode` | `flexible`, `fixed` | `flexible` | `flexible` lets a Final wait for an entity to finish so smart formatting applies. |
| `enable_partials` | boolean | `false` | Sends `AddPartialTranscript`. |
| `diarization` | `none`, `speaker`, `channel`, `channel_and_speaker` | `none` | See [references/diarization.md](references/diarization.md). |
| `conversation_config.end_of_utterance_silence_trigger` | 0 to 2 seconds | 0 (off) | Enhanced and Standard only. See [references/turn-detection.md](references/turn-detection.md). |
| `language_hints` | array of language codes | none | Melia 1 and Oak 1 only. |

## Finals, Partials, and latency

| Type | Latency | Stability | Best for |
| --- | --- | --- | --- |
| Final (`AddTranscript`) | ~0.7–2 s | Definitive, never revised | Accurate transcripts, subtitles |
| Partial (`AddPartialTranscript`) | <500 ms | May be revised | Live captions, voice interfaces |

`max_delay` guidance:

- 0.7–1.5 s: ultra-fast response; less than 5% accuracy degradation relative to Batch.
- 2.0 s: recommended for most use cases; around 1% degradation.
- 4.0 s: accuracy equivalent to Batch. Add Partials for early feedback.

Read text from `metadata.transcript` for ready-formatted output, or iterate `results` for per-word timing, confidence, speaker, and language.

## Gotchas

- Do not send audio before `RecognitionStarted`.
- Partial accuracy is usually 10–25% lower than Finals, and `confidence` on Partials has no meaning. Partial latency is not affected by `max_delay`.
- With `max_delay_mode: "fixed"`, entities such as numbers can be split across Finals ("I am 30 five.").
- Sending audio faster than real time can fill buffers and drop the connection; watch the WebSocket `bufferedAmount`. A growing backlog ends in a `job_error`.
- Sessions end automatically after 48 hours, after 1 hour with no audio, or after 3 minutes with no audio or ping/pong. The server sends an in-band `Error`, then closes with code `1008`. Reconnect proactively for long-running streams.
- Concurrent sessions: Free 2, Pro 50, Enterprise custom. Exceeding the quota gives `quota_exceeded` (close code `4005`).
- Retry only after close codes `4005`, `4013`, and `1011`, and wait at least 5–10 seconds.
- More than 20,000 `additional_vocab` items gives a `protocol_error` and close code `1003`. A custom dictionary can delay session start by up to 15 seconds.
- Melia 1 and Oak 1: `language` must be `multi`; `end_of_utterance_silence_trigger` is rejected (use `ForceEndOfUtterance`); realtime speaker identification (`GetSpeakers`, `get_speakers`, `speakers`) is not supported; the server sends `LanguageInfo` before each new language appears.
- `SetRecognitionConfig` can change only `max_delay`, `max_delay_mode`, `enable_partials`, `audio_filtering_config`, and `conversation_config` mid-session. `language` may be included but must match the original.
- SaaS channel diarization supports at most 2 channels, and channel audio must be sent as base64 in `AddChannelAudio`, not as binary `AddAudio`.
- The Realtime SaaS service does not store audio, transcripts, or configuration.

## Reference files

| Read | When |
| --- | --- |
| [references/protocol.md](references/protocol.md) | Implementing the WebSocket protocol directly: handshake, every client and server message schema, `Info`/`Warning`/`Error` types, close codes. |
| [references/configuration.md](references/configuration.md) | Building `StartRecognition`: full `audio_format`, `transcription_config`, `translation_config`, `audio_events_config` field tables, language hints, `SetRecognitionConfig`. |
| [references/output-and-latency.md](references/output-and-latency.md) | Tuning `max_delay`/`max_delay_mode`, working with Partials, parsing `results`, `LanguageInfo`, app usage tracking (`sm-app`). |
| [references/diarization.md](references/diarization.md) | Speaker, channel, and channel-and-speaker diarization; `AddChannelAudio`; diarization tuning; realtime speaker identification (enrollment and identification). |
| [references/turn-detection.md](references/turn-detection.md) | End of utterance detection, `ForceEndOfUtterance`, client-side and semantic turn detection, with Python examples. |
| [references/limits-and-errors.md](references/limits-and-errors.md) | Concurrency and session limits, timeout warnings, error types, close codes, retry and reconnect guidance. |
| [references/code-examples.md](references/code-examples.md) | Complete samples: JavaScript microphone and radio stream, Python microphone (`speechmatics-python`), Python URL stream, FFmpeg piping into the `speechmatics` CLI. |

## Docs

- Quickstart: https://docs.speechmatics.com/speech-to-text/realtime/quickstart
- Input: https://docs.speechmatics.com/speech-to-text/realtime/input
- Output: https://docs.speechmatics.com/speech-to-text/realtime/output
- Limits: https://docs.speechmatics.com/speech-to-text/realtime/limits
- Realtime diarization: https://docs.speechmatics.com/speech-to-text/realtime/realtime-diarization
- Speaker identification: https://docs.speechmatics.com/speech-to-text/realtime/speaker-identification
- Turn detection: https://docs.speechmatics.com/speech-to-text/realtime/turn-detection
- API reference: https://docs.speechmatics.com/api-ref/realtime-transcription-websocket
