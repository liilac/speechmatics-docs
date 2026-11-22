# SDKs, integrations, and the API reference

Sources:

- https://docs.speechmatics.com/integrations-and-sdks/
- https://docs.speechmatics.com/integrations-and-sdks/sdks
- https://docs.speechmatics.com/api-ref/
- https://docs.speechmatics.com/get-started/quickstart

## Official SDKs

### Speech to Text

| SDK | What it does | Repository |
|---|---|---|
| Agent STT (Python) | Stream audio and receive speaker-labeled, turn-based transcription | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/agent_stt |
| Realtime (Python) | Stream audio and receive instant transcripts | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/rt |
| Batch (Python) | Input audio files and receive transcripts | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/batch |
| Realtime (JavaScript) | Stream audio and receive instant transcripts | https://github.com/speechmatics/speechmatics-js-sdk/tree/main/packages/real-time-client |
| Batch (JavaScript) | Input audio files and receive transcripts | https://github.com/speechmatics/speechmatics-js-sdk/tree/main/packages/batch-client |
| Realtime (.NET) | Stream audio and receive a transcription | https://github.com/speechmatics/speechmatics-dotnet |
| Realtime and Batch (Rust) | Input audio streams or files and receive transcription | https://github.com/speechmatics/speechmatics-rs |

### Text to Speech

| SDK | What it does | Repository |
|---|---|---|
| TTS (Python) | Convert text to speech | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/tts |

Top-level repositories:

- Python SDK (agent STT, Realtime, Batch, and TTS): https://github.com/speechmatics/speechmatics-python-sdk
- JavaScript SDK (Realtime and Batch): https://github.com/speechmatics/speechmatics-js-sdk

## Install commands

These are the install commands the docs quickstarts give. For any SDK not listed, read the repository README; do not guess a package name.

| SDK | Command | Docs page |
|---|---|---|
| Realtime (Python), with microphone input | `pip install speechmatics-rt pyaudio` | https://docs.speechmatics.com/speech-to-text/realtime/quickstart |
| Realtime (JavaScript) | `npm install @speechmatics/real-time-client @speechmatics/auth` | https://docs.speechmatics.com/speech-to-text/realtime/quickstart |
| Batch (Python) | `pip install speechmatics-batch` | https://docs.speechmatics.com/speech-to-text/batch/quickstart |
| Batch (JavaScript) | `npm install @speechmatics/batch-client` | https://docs.speechmatics.com/speech-to-text/batch/quickstart |
| Agent STT (Python), with microphone input | `pip install speechmatics-agent-stt pyaudio` | https://docs.speechmatics.com/speech-to-text/agent-stt/quickstart |
| Voice SDK (Python) | `pip install speechmatics-voice` (or `speechmatics-voice[smart]`) | https://docs.speechmatics.com/integrations-and-sdks/voice-sdk |
| WER toolkit and CLI (`sm-metrics`) | `pip install speechmatics-python` | https://docs.speechmatics.com/speech-to-text/accuracy-benchmarking |

`pyaudio` is only needed for microphone capture. The agent STT quickstart reads the key from the environment: `export SPEECHMATICS_API_KEY=<your-api-key>`.

Usage for each SDK lives in the product skill: `speechmatics:realtime-transcription`, `speechmatics:batch-transcription`, `speechmatics:agent-stt`, `speechmatics:text-to-speech`, `speechmatics:voice-agent-integrations`.

## Integrations

Hand off to `speechmatics:voice-agent-integrations` for all of these.

| Integration | Kind | Best for | Docs |
|---|---|---|---|
| Vapi | Voice agent orchestrator | Turnkey platform, no code, rapid prototyping; non-technical builders | https://docs.speechmatics.com/integrations-and-sdks/vapi |
| LiveKit | Voice agent orchestrator | Open-source framework on LiveKit's WebRTC infrastructure; engineers | https://docs.speechmatics.com/integrations-and-sdks/livekit |
| Pipecat | Voice agent orchestrator | Open-source framework with full control of the voice pipeline in code; complex agents | https://docs.speechmatics.com/integrations-and-sdks/pipecat/ |
| Twilio | Telephony | Forkable reference proxy that streams both sides of a Twilio Voice call to Speechmatics Realtime, with per-speaker transcripts | https://docs.speechmatics.com/integrations-and-sdks/twilio |
| Zapier | No-code | Transcribe audio inside Zaps; trigger from any app and send transcripts to any downstream step | https://docs.speechmatics.com/integrations-and-sdks/zapier |

Choose an integration when the stack already uses one of these platforms. Choose an SDK to call Speechmatics directly from your own services.

## Examples and templates

Speechmatics Academy has working examples, integrations, and templates for the SDKs: https://github.com/speechmatics/speechmatics-academy

"Hello World": https://github.com/speechmatics/speechmatics-academy/tree/main/basics/01-hello-world

## Quickstarts

| Goal | Page |
|---|---|
| Transcribe in real time | https://docs.speechmatics.com/speech-to-text/realtime/quickstart |
| Transcribe a file | https://docs.speechmatics.com/speech-to-text/batch/quickstart |
| Transcribe for a voice agent | https://docs.speechmatics.com/speech-to-text/agent-stt/quickstart |
| Generate speech from text | https://docs.speechmatics.com/text-to-speech/quickstart |

## API reference

Index: https://docs.speechmatics.com/api-ref/

Speechmatics offers REST and WebSocket APIs.

| API | Reference |
|---|---|
| Realtime transcription (WebSocket) | https://docs.speechmatics.com/api-ref/realtime-transcription-websocket |
| Agent STT (WebSocket) | https://docs.speechmatics.com/api-ref/agent-stt-websocket |
| Batch: create a transcription job | https://docs.speechmatics.com/api-ref/batch/create-a-new-job |
| Batch: delete a job | https://docs.speechmatics.com/api-ref/batch/delete-a-job |
| Batch: usage statistics | https://docs.speechmatics.com/api-ref/batch/get-usage-statistics |
| Management API: create an API key | https://docs.speechmatics.com/api-ref/management/create-an-api-key |
| Management API: get all API keys | https://docs.speechmatics.com/api-ref/management/get-all-api-keys |
| Management API: delete an API key | https://docs.speechmatics.com/api-ref/management/delete-an-api-key |
| Management API: get all projects | https://docs.speechmatics.com/api-ref/management/get-all-projects |
| Management API: get a project by ID | https://docs.speechmatics.com/api-ref/management/get-a-project-by-id |
| Management API: create a project | https://docs.speechmatics.com/api-ref/management/create-a-project |
| Management API: update a project | https://docs.speechmatics.com/api-ref/management/update-a-project |
| Management API: delete a project | https://docs.speechmatics.com/api-ref/management/delete-a-project |

Download the Batch API OpenAPI spec: https://docs.speechmatics.com/batch.yaml

The reference sidebar groups pages as Transcription API (Realtime, agent STT, Batch) and Management API.

## Other links

- Portal: https://portal.speechmatics.com
- Release notes: https://speechmatics.featurebase.app/en/changelog
- Pricing: https://www.speechmatics.com/pricing
- Support: https://support.speechmatics.com
