---
name: get-started
description: Routes a Speechmatics integration to the right product, model, endpoint, and sibling skill. Covers choosing between the Realtime API, Batch API, agent STT, and Text to Speech; model selection (`standard`, `enhanced`, `melia-1`, `oak-1`, `linden-1`, `domain` `medical`); SaaS versus on-prem; authentication with API keys and temporary keys (JWTs from `mp.speechmatics.com/v1/jwts`, `ttl`, `client_ref`, `region`) including browser use; regions and endpoint hostnames; supported languages and language codes; official SDKs and install commands; and where the API reference lives. Use when starting a Speechmatics integration, when asked which Speechmatics API or model to use, or on a 401 Unauthorized, wrong-region, or unsupported-language error.
---

# Get started with Speechmatics

Speechmatics provides APIs for Speech to Text (STT) and Text to Speech (TTS). Use this skill to pick the product, model, endpoint, and auth method, then hand off to the skill that owns the detail.

Docs: https://docs.speechmatics.com/ · Quickstart: https://docs.speechmatics.com/get-started/quickstart

## Route to the right skill

| Task | Skill |
|---|---|
| Transcribe a pre-recorded file (jobs, polling, notifications, output formats) | `speechmatics:batch-transcription` |
| Summarization, sentiment analysis, topic detection, auto chapters on a batch job | `speechmatics:speech-intelligence` |
| Transcribe live audio over a WebSocket | `speechmatics:realtime-transcription` |
| Turn-based, speaker-labeled transcription to feed an LLM in a voice agent | `speechmatics:agent-stt` |
| Diarization, custom dictionary, translation, Entity Detection, PII Redaction, audio events, formatting | `speechmatics:transcription-features` |
| Generate speech from text | `speechmatics:text-to-speech` |
| LiveKit, Pipecat, Twilio, Vapi, Voice SDK, Zapier | `speechmatics:voice-agent-integrations` |
| Run containers on-prem (CPU, GPU, language ID, translation, usage reporting) | `speechmatics:container-deployment` |
| Deploy on Kubernetes with the Helm chart | `speechmatics:kubernetes-deployment` |
| Install or administer the virtual appliance | `speechmatics:virtual-appliance` |
| Workspaces, projects, members, SSO, management tokens, Management API, billing, usage | `speechmatics:account-administration` |
| Measure Word Error Rate (WER), benchmark accuracy, app analytics (`sm-app`) | `speechmatics:accuracy-benchmarking` |

## Choose a product

| Need | Product | Transport |
|---|---|---|
| Transcripts as the audio plays: live captions, broadcasts, meetings, call monitoring | Realtime API | WebSocket `wss://<rt-host>/v2` |
| Complete transcript of a recorded file; highest accuracy; range of output formats | Batch API | REST `https://<batch-host>/v2/jobs/` |
| Punctuated, speaker-attributed segments plus turn start and end, ready to pass to an LLM | agent STT | WebSocket `wss://<rt-host>/v2/agent` |
| Speech from text | TTS API | See `speechmatics:text-to-speech` |

- Batch is asynchronous by default: submit a job, monitor it, retrieve the transcript. A job holds the audio or video file, the config, metadata and status, and the transcripts. Create jobs by direct upload or by referencing a URL. A synchronous mode is also documented (`speechmatics:batch-transcription`).
- agent STT is the STT layer for building voice agents. It is SaaS only.
- The quickest way to try a product without code is the portal: https://portal.speechmatics.com/

## Choose a model

Set `model` in `transcription_config`. Default when omitted: `standard`.

| `model` | Use for | API |
|---|---|---|
| `enhanced` | Highest accuracy on single-language audio (medical, legal, subtitling) | Batch, Realtime |
| `standard` | Throughput or latency over maximum accuracy (archival, indexing, large-scale captioning) | Batch, Realtime |
| `melia-1` | Audio with more than one language, including mid-conversation switching. Requires `"language": "multi"` | Batch, Realtime |
| `oak-1` | Multilingual healthcare audio. Requires `"language": "multi"` | Batch, Realtime |
| `linden-1` | agent STT only, on the `/v2/agent` path | agent STT |

- Single-language healthcare audio needing full features: `"model": "enhanced"` plus `"domain": "medical"` (Enhanced Medical).
- Melia 1 and Oak 1 reject `"language": "auto"` and support a reduced feature set (no custom dictionary, confidence scores, speaker identification, or speech intelligence yet).
- `operating_point` is deprecated on SaaS; it maps to `model`. Use `model`.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  }
}
```

Full comparison, Realtime gaps for Melia 1 and Oak 1, and configs: [references/models.md](references/models.md).

## Authenticate

1. Sign in at https://portal.speechmatics.com and create an API key at **Settings > API Keys** (https://portal.speechmatics.com/settings/api-keys/). The value is shown once; store it securely.
2. Send it as a bearer token. Requests without a valid key get `HTTP 401 - Unauthorized`.

Batch:

```bash
curl -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/" \
  -H "Authorization: Bearer $API_KEY"
```

Realtime (server-side), in the WebSocket handshake:

```http
GET /v2/ HTTP/1.1
Host: eu.rt.speechmatics.com
Upgrade: websocket
Connection: Upgrade
Authorization: Bearer YOUR_API_KEY
```

agent STT (server-side): same header, path `/v2/agent`.

### Browser and client-side use: temporary keys

Never ship a long-lived API key to a browser. Mint a temporary key (JWT) on your server and pass it to the client.

```bash
curl -L -X POST "https://mp.speechmatics.com/v1/jwts?type=rt" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $API_KEY" \
     -d '{"ttl": 60 }'
```

Response: `{"key_value": "eyJhbG..."}`.

| Parameter | Where | Values |
|---|---|---|
| `type` | Query | `batch` (default) or `rt`. `rt` covers both Realtime and agent STT |
| `ttl` | Body, required | Integer 60-86400 seconds. Use the shortest possible |
| `client_ref` | Body | `batch` only. Restricts the key to jobs with that reference. Required when the key is exposed to end users. Ignored for `rt` |
| `region` | Body | `batch` only: `eu` (default), `usa`, `au`. Must match the Batch endpoint called. Ignored for `rt` |

- Realtime and agent STT in the browser: pass the key as a query parameter, `wss://eu.rt.speechmatics.com/v2?jwt=$TEMP_KEY` or `wss://global.rt.speechmatics.com/v2/agent?jwt=$TEMP_KEY`.
- Batch: use the temporary key in place of the API key in the `Authorization` header.
- Enterprise customers must ask support or their account manager to enable temporary keys.

Details, gotchas, handshake responses, and close codes: [references/authentication.md](references/authentication.md).

## Regions and endpoints

Batch SaaS (the endpoint sets the region; use the same endpoint for every request about a job):

| Customer type | Region | Endpoint |
|---|---|---|
| All | EU1 (Europe) | `eu1.asr.api.speechmatics.com` |
| Enterprise | EU2 (Europe) | `eu2.asr.api.speechmatics.com` |
| All | US1 (USA) | `us1.asr.api.speechmatics.com` |
| Enterprise | US2 (USA) | `us2.asr.api.speechmatics.com` |
| All | AU1 (Australia) | `au1.asr.api.speechmatics.com` |

Realtime SaaS and agent STT (agent STT uses the `/v2/agent` path):

| Region | Endpoint |
|---|---|
| Global (auto-routed to nearest region) | `global.rt.speechmatics.com` |
| EU1 (Europe) | `eu.rt.speechmatics.com` |
| US1 (USA) | `us.rt.speechmatics.com` |
| AU1 (Australia) | `au.rt.speechmatics.com` |

- `global.rt.speechmatics.com` may route to any region. For data residency or compliance, use a regional endpoint.
- EU2 and US2 are for enterprise high availability and failover only. Jobs created there are not visible in the portal.
- Melia 1 and Oak 1 on Batch: use EU1, US1, or AU1 only.

## Languages

Set `language` in `transcription_config` to an ISO 639-1 or ISO 639-3 code, for example `en`, `es`, `de`, `fr`, `ja`, `cmn`, `yue`.

- One global pack per language covers all accents. There are no per-accent codes; use `output_locale` to standardize spelling (see `speechmatics:transcription-features`).
- `auto` (language identification) is Batch only, and not for Melia 1 or Oak 1.
- Bilingual packs for Enhanced and Standard: `ar_en`, `en_ms`, `cmn_en`, `cmn_en_ms_ta`, `en_ta`, `tl`, and Spanish and English as `"language": "es"` with `"domain": "bilingual-en"`.
- Melia 1 and Oak 1 use `"language": "multi"`.
- agent STT (Linden 1) supports the same languages as Realtime; translation is not available.

Full code table, medical languages, translation pairs: [references/languages.md](references/languages.md).

## SDKs

| SDK | Install | Source |
|---|---|---|
| Realtime (Python) | `pip install speechmatics-rt` | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/rt |
| Batch (Python) | `pip install speechmatics-batch` | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/batch |
| agent STT (Python) | `pip install speechmatics-agent-stt` | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/agent_stt |
| TTS (Python) | See repository | https://github.com/speechmatics/speechmatics-python-sdk/tree/main/sdk/tts |
| Realtime (JavaScript) | `npm install @speechmatics/real-time-client @speechmatics/auth` | https://github.com/speechmatics/speechmatics-js-sdk/tree/main/packages/real-time-client |
| Batch (JavaScript) | `npm install @speechmatics/batch-client` | https://github.com/speechmatics/speechmatics-js-sdk/tree/main/packages/batch-client |
| Realtime (.NET) | See repository | https://github.com/speechmatics/speechmatics-dotnet |
| Realtime and Batch (Rust) | See repository | https://github.com/speechmatics/speechmatics-rs |

The docs give install commands only for the rows shown; for the others read the repository README. Do not guess package names. Integrations, examples, and the API reference map: [references/sdks-and-api-reference.md](references/sdks-and-api-reference.md).

## SaaS or on-prem

- SaaS: fully managed, no infrastructure. Start in the portal.
- On-prem: containers (CPU, GPU, language ID, translation), Kubernetes, or the virtual appliance in your own environment. On-prem deployment is available only on the Enterprise plan; contact sales at https://www.speechmatics.com/speak-to-sales.
- Some features are SaaS only (for example alignment, auto chapters, Entity Detection, PII Redaction, summarization, topic detection, Batch language identification, feature discovery, agent STT). Check [references/deployments-and-features.md](references/deployments-and-features.md) before promising a feature on-prem.

## Gotchas

- A Batch temporary key works in one region only. A key minted without `region` is for `eu` and is rejected by `us1` or `au1` endpoints.
- Temporary keys with a `client_ref` get `HTTP 403 - Forbidden` from the Batch usage endpoint.
- There is no agent STT key type. Request `type=rt` and connect to `/v2/agent`.
- An API key belongs to one project and determines the project a request applies to. You never pass a project ID to the transcription APIs.
- Language availability depends on the languages you are contracted to use.
- Preview features run on a separate non-production endpoint. See [references/deployments-and-features.md](references/deployments-and-features.md).

## References

- [references/authentication.md](references/authentication.md): API keys, temporary key parameters, per-product examples, endpoint tables, WebSocket handshake responses, and close codes. Read when writing auth code or debugging 401, 403, or a closed WebSocket.
- [references/models.md](references/models.md): model comparison, feature gaps for Melia 1 and Oak 1 on Batch and Realtime, Enhanced Medical, Linden 1, `operating_point`. Read before recommending or configuring a model.
- [references/languages.md](references/languages.md): every language code, bilingual packs, medical languages, translation pairs. Read when setting `language`, `domain`, or translation targets.
- [references/sdks-and-api-reference.md](references/sdks-and-api-reference.md): SDK and integration list, Speechmatics Academy, API reference URLs. Read when choosing a client library or linking to reference pages.
- [references/deployments-and-features.md](references/deployments-and-features.md): SaaS versus on-prem, feature availability by mode and deployment, preview mode. Read when a feature must run on-prem or in a specific mode.
