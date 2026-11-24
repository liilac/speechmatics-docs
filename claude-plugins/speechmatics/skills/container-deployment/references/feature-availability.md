# Feature availability by deployment

Docs: https://docs.speechmatics.com/deployments

## Deployment options

Cloud (SaaS): create an account in the portal (https://portal.speechmatics.com/) and use the Realtime API, Batch API or agent STT. See `speechmatics:get-started`.

On-prem:

| Option | Docs |
|---|---|
| CPU Speech to Text container | https://docs.speechmatics.com/deployments/container/cpu-speech-to-text |
| GPU Speech to Text container | https://docs.speechmatics.com/deployments/container/gpu-speech-to-text |
| Kubernetes (Helm chart) | https://docs.speechmatics.com/deployments/kubernetes |
| Language ID container | https://docs.speechmatics.com/deployments/container/language-id |
| Translation container | https://docs.speechmatics.com/deployments/container/gpu-translation |

## Speech to Text features

Agent STT is available on SaaS only. Where a row lists agent STT as a mode, on-prem applies to the Batch and Realtime modes only.

| Feature | Modes | Deployments |
|---|---|---|
| Multilingual Speech to Text | Batch, Realtime | SaaS, on-prem |
| Alignment | Batch | SaaS |
| Audio events | Batch, Realtime | SaaS, on-prem |
| Audio filtering | Batch, Realtime | SaaS, on-prem |
| Auto chapters | Batch | SaaS |
| Custom dictionary | Batch, Realtime, agent STT | SaaS, on-prem |
| Diarization | Batch, Realtime, agent STT (speaker diarization only, not channel diarization) | SaaS, on-prem |
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
| Tracking | Batch, Realtime | SaaS, on-prem |
| Translation | Batch, Realtime | SaaS, on-prem |
| Turn detection | Realtime | SaaS, on-prem |

Notes:

- Speaker identification on-prem: batch requires the GPU Speech to Text container. Realtime is supported on CPU and GPU containers. Both need secrets; see [security.md](security.md#speaker-identification-secrets).
- Language identification as a Batch API job feature is SaaS only. On-prem, run the separate language ID container ([language-id.md](language-id.md)) and pass the predicted code to a transcriber.
- Translation on-prem needs the translation GPU inference server ([gpu-translation.md](gpu-translation.md)).
- Melia 1 and Oak 1 on-prem are GPU-only ([gpu-inference.md](gpu-inference.md)).

For feature configuration, see `speechmatics:transcription-features`.
