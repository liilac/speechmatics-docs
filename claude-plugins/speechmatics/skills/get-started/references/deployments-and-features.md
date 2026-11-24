# Deployments, feature availability, and preview mode

Sources:

- https://docs.speechmatics.com/deployments/
- https://docs.speechmatics.com/speech-to-text/
- https://docs.speechmatics.com/private/preview-mode

## Deployment options

### SaaS (cloud)

Fully managed. No infrastructure to deploy or maintain.

1. Create an account in the portal: https://portal.speechmatics.com/
2. Follow a quickstart: Realtime (`speechmatics:realtime-transcription`), Batch (`speechmatics:batch-transcription`), or agent STT (`speechmatics:agent-stt`).

### On-prem

Run Speechmatics in your own environment for control over deployment and data. On-prem and on-device deployment are available only on the Enterprise plan; contact sales at https://www.speechmatics.com/speak-to-sales.

| Option | Use | Docs | Skill |
|---|---|---|---|
| CPU Speech to Text container | STT engine as a CPU-based container on your hardware | https://docs.speechmatics.com/deployments/container/cpu-speech-to-text | `speechmatics:container-deployment` |
| GPU Speech to Text container | STT engine on GPU for maximum throughput and lowest latency; high-volume and real-time workloads | https://docs.speechmatics.com/deployments/container/gpu-speech-to-text | `speechmatics:container-deployment` |
| Language ID container | Identify the language spoken in audio | https://docs.speechmatics.com/deployments/container/language-id | `speechmatics:container-deployment` |
| Translation container | Translate audio from one language to another | https://docs.speechmatics.com/deployments/container/gpu-translation | `speechmatics:container-deployment` |
| Kubernetes | Elastic scaling and orchestration on your own hardware or chosen cloud vendor | https://docs.speechmatics.com/deployments/kubernetes | `speechmatics:kubernetes-deployment` |
| Virtual appliance | Packaged appliance deployment | https://docs.speechmatics.com/deployments/virtual-appliance | `speechmatics:virtual-appliance` |

A hybrid of managed service and self-hosting is possible.

On-prem deployments report usage differently from the portal. See `speechmatics:container-deployment`.

## Feature availability

Availability varies by deployment and processing mode. Agent STT is SaaS only: where a row lists agent STT as a mode, the on-prem deployment applies to Batch and Realtime only.

| Feature | Modes | Deployments |
|---|---|---|
| Multilingual Speech to Text | Batch, Realtime | SaaS, on-prem |
| Alignment | Batch | SaaS |
| Audio events | Batch, Realtime | SaaS, on-prem |
| Audio filtering | Batch, Realtime | SaaS, on-prem |
| Auto chapters | Batch | SaaS |
| Custom dictionary | Batch, Realtime, agent STT | SaaS, on-prem |
| Diarization | Batch, Realtime, agent STT (speaker diarization only, not channel) | SaaS, on-prem |
| Disfluencies and word replacement | Batch, Realtime, agent STT | SaaS, on-prem |
| Entity Detection | Batch | SaaS |
| Feature discovery | Batch, Realtime | SaaS |
| Fetch URL | Batch | SaaS, on-prem |
| Language identification | Batch | SaaS |
| Notifications | Batch | SaaS, on-prem |
| PII Redaction | Batch | SaaS |
| Punctuation settings | Batch, Realtime | SaaS, on-prem |
| Sentiment analysis | Batch | SaaS, on-prem |
| Smart formatting | Batch, Realtime | SaaS, on-prem |
| Speaker identification | Batch, Realtime, agent STT | SaaS, on-prem (see note) |
| Summarization | Batch | SaaS |
| Topic detection | Batch | SaaS |
| Tracking metadata | Batch, Realtime | SaaS, on-prem |
| Translation | Batch, Realtime | SaaS, on-prem |
| Turn detection | Realtime | SaaS, on-prem |

Notes:

- On-prem Batch speaker identification requires the GPU Speech to Text container. Realtime speaker identification works on both CPU and GPU containers.
- Speaker diarization with Melia 1 and Oak 1 is SaaS only.
- A separate Language ID container exists for on-prem.
- Feature support also varies by model. See [models.md](models.md).

Skills that own each feature: `speechmatics:transcription-features` (diarization, custom dictionary, translation, Entity Detection, PII Redaction, audio events, audio filtering, formatting, feature discovery, speaker identification), `speechmatics:speech-intelligence` (summarization, sentiment analysis, topic detection, auto chapters), `speechmatics:batch-transcription` (alignment, fetch URL, notifications, language identification, tracking), `speechmatics:realtime-transcription` (turn detection).

## When to use each processing mode

Realtime:

- Speed matters
- Live broadcasts or events
- Captions for webinars, meetings, or podcasts in real time
- Live input for voice assistants or AI agents
- Monitoring contact center calls as they happen
- Accessibility features such as live captions

Batch:

- Recorded meetings or interviews
- Captions for on-demand video and podcasts
- Searchable transcripts for media archives
- Customer service recordings for compliance or insights
- Subtitles across large video libraries

Agent STT:

- A voice agent or live conversational assistant
- Responding as soon as a caller stops speaking
- Feeding clean, speaker-labeled turns to an LLM
- Multi-speaker calls without stitching words together

Agent STT groups the transcript into segments (punctuated, attributed to a speaker) and marks where each speaker's turn starts and ends.

## Data handling by mode

- Realtime: audio is streamed over a WebSocket and never recorded or stored. Transcripts are streamed back and then discarded. Processing is in memory.
- Batch: audio files, transcripts, and job configuration are stored for 7 days, then deleted automatically. Delete sooner with the API.

More in `speechmatics:account-administration`.

## Preview mode

Preview mode gives early access to features before production. It is available for Realtime transcription only.

- Do not use for live production traffic. Features may be limited and the system is less stable than production.
- No uptime or performance SLAs.
- No data residency guarantees. Preview traffic is not served from a hosted region; data may be processed in either the US or the EU.
- Preview features may be cancelled at any time or never released.

Portal: enable the **Preview Mode** toggle in system settings (https://portal.speechmatics.com/settings/system).

API: use a portal API key to start a Realtime session at:

```text
wss://preview.rt.speechmatics.com/v2
```
