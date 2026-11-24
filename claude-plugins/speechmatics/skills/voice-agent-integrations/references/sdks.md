# Integrations and SDK overview

Docs:

- Overview: https://docs.speechmatics.com/integrations-and-sdks/
- SDKs: https://docs.speechmatics.com/integrations-and-sdks/sdks

## Choose a path

Connect through a voice agent platform, or call Speechmatics directly from your code with an SDK. Start with the option that matches your current stack.

### Voice agent orchestrator integrations

| Integration | What it is | Best for | Reference |
|---|---|---|---|
| Vapi | Turnkey voice agent platform. Deploy fast with no code. Rapid prototyping | Non-technical builders | [vapi.md](vapi.md) |
| LiveKit | Open-source framework for building agents with LiveKit's WebRTC infrastructure. Simple setup | Engineers | [livekit.md](livekit.md) |
| Pipecat | Open-source framework with full control of the voice pipeline in code. Complex agents | Power builders | [pipecat.md](pipecat.md) |

### Telephony

| Integration | What it is | Best for | Reference |
|---|---|---|---|
| Twilio | Forkable reference proxy that streams both sides of a Twilio Voice call to the Realtime API. Per-speaker transcripts to your console | Engineers integrating telephony | [twilio.md](twilio.md) |

### No-code

| Integration | What it is | Best for | Reference |
|---|---|---|---|
| Zapier | Transcribe audio inside Zaps. Trigger from any app, send transcripts to any downstream step | No-code automation | [zapier.md](zapier.md) |

## Speech to Text SDKs

| SDK | Purpose | Repository | Docs quickstart path |
|---|---|---|---|
| Agent STT (Python) | Stream audio and receive speaker-labeled, turn-based transcription | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/agent_stt | `/speech-to-text/agent-stt/quickstart` |
| Realtime (Python) | Stream audio and receive a transcription | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/rt | `/rt-stt-sdk` |
| Batch (Python) | Input audio files and output transcription | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/batch | `/python-batch-stt-sdk` |
| Realtime (JavaScript) | Stream audio and receive instant transcripts | https://github.com/speechmatics/speechmatics-js-sdk/tree/main/packages/real-time-client | `/js-rt-stt-sdk` |
| Batch (JavaScript) | Input audio files and output transcription | https://github.com/speechmatics/speechmatics-js-sdk/tree/main/packages/batch-client | `/js-batch-stt-sdk` |
| Realtime (.NET) | Stream audio and receive a transcription | https://github.com/speechmatics/speechmatics-dotnet | `/dotnet-rt-stt-sdk` |
| Realtime and Batch (Rust) | Input audio streams or files and receive transcription | https://github.com/speechmatics/speechmatics-rs | `/rust-stt-sdk` |

Quickstart paths are relative to `https://docs.speechmatics.com` as linked from the SDKs page.

## Text to Speech SDKs

| SDK | Purpose | Repository | Docs quickstart path |
|---|---|---|---|
| TTS (Python) | Convert text to speech | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/tts | `/python-tts-sdk` |

## Voice SDK

The Voice SDK (`speechmatics-voice`, https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/voice) is deprecated and replaced by agent STT. See [voice-sdk.md](voice-sdk.md).

## Where to go for SDK usage

This skill does not document the SDK APIs themselves. Use:

- `speechmatics:agent-stt` for the agent STT Python SDK.
- `speechmatics:realtime-transcription` for the Realtime SDKs.
- `speechmatics:batch-transcription` for the Batch SDKs.
- `speechmatics:get-started` for authentication, regions, and SDK installation.
- `speechmatics:text-to-speech` for the TTS SDK.

Working examples, integrations, and templates: https://github.com/speechmatics/speechmatics-academy
