---
name: container-deployment
description: Deploys Speechmatics Speech to Text on-prem with Docker containers. Covers registry access (speechmaticspublic.azurecr.io), licensing (LICENSE_TOKEN, /license.json), CPU batch and realtime transcriber containers, GPU inference servers for Standard, Enhanced, Melia 1 and Oak 1, GPU translation, the language ID container, speaker identification secrets, the batch persistent worker HTTP API, read-only and non-root hardening, sizing and cost, troubleshooting, and automatic or offline usage reporting. Use when the user mentions on-prem, docker run, batch-asr-transcriber, rt-asr-transcriber, sm-gpu-inference-server, sm-asr-transcriber, SM_INFERENCE_ENDPOINT, SM_MAX_CONCURRENT_CONNECTIONS, SM_TRANSLATION_ENDPOINT, SM_EATS_URL, --run-mode http, --parallel, Triton, or the asr-usage container.
---

# Speechmatics container deployment

Run Speechmatics Speech to Text (STT) on-prem as Docker containers: CPU transcribers, optional GPU inference servers, and supporting containers.

Docs root: https://docs.speechmatics.com/deployments

Versions used below are current at time of writing; check the docs: transcriber and GPU inference server `17.1.0`, Melia 1 and Oak 1 images `1.13.0`, usage container `0.5.3`, language ID image `2.2.1`, JSON output format `2.9`.

## When to use

- Pulling, licensing, running, or tuning Speechmatics containers with Docker or Docker Compose.
- Choosing CPU or GPU, sizing hardware, estimating cost.
- Reporting on-prem usage for billing.

Use a sibling skill instead for:

- Helm chart deployment on Kubernetes: `speechmatics:kubernetes-deployment`.
- The virtual appliance: `speechmatics:virtual-appliance`.
- SaaS accounts, API keys, first requests: `speechmatics:get-started`.
- Job config and Batch API semantics: `speechmatics:batch-transcription`.
- Realtime WebSocket messages (`StartRecognition`, `AddTranscript`): `speechmatics:realtime-transcription`.
- Feature config (diarization, custom dictionary, translation config): `speechmatics:transcription-features`.

## Architecture

| Component | Image | Needs GPU | Purpose |
|---|---|---|---|
| Batch transcriber | `batch-asr-transcriber-<lang>` | No | One file in, one transcript out, then exits. One image per language pack |
| Realtime transcriber | `rt-asr-transcriber-<lang>` | No | WebSocket server on port 9000, health service on 8001 |
| GPU inference server (Standard, Enhanced) | `sm-gpu-inference-server-*` | Yes | Triton server; transcribers offload inference over gRPC port 8001 |
| Melia 1 and Oak 1 transcriber | `sm-asr-transcriber` | No | Single image for Batch and Realtime, selected with `SM_ASR_MODE` |
| Melia 1 and Oak 1 inference server | `sm-asr-inference-server` | Yes | Required; these models are GPU-only |
| Translation inference server | `sm-translation-inference-server` | Yes | All translation pairs; cannot share a GPU with the transcription server |
| Language ID | `langid` | No | Predicts the predominant language of a file |
| Usage container | `asr-usage` | No | Collects usage events for offline reporting |

A CPU transcriber works alone. Add `SM_INFERENCE_ENDPOINT=<server>:<port>` to offload inference to a GPU server. GPU models differ from CPU models, so results are not identical.

## Prerequisites

1. Registry credentials and a license from [Support](https://support.speechmatics.com).
2. Log in and pull. Speechmatics requires you to re-host images in your own private registry after the first pull.

```bash
docker login https://speechmaticspublic.azurecr.io
docker pull speechmaticspublic.azurecr.io/batch-asr-transcriber-en:17.1.0
docker pull speechmaticspublic.azurecr.io/rt-asr-transcriber-en:17.1.0
```

3. License every transcriber one of two ways. Licensing needs no network access.

```bash
# File: map to /license.json
docker run -v ./my_license.json:/license.json batch-asr-transcriber-en:17.1.0
# Token: the signedclaimstoken value from the license file
docker run -e LICENSE_TOKEN=exampleClaimsToken batch-asr-transcriber-en:17.1.0
```

If both are given, the file is ignored. After `notValidAfter` the container still runs but does not transcribe.

Full image list and license structure: [references/images-and-licensing.md](references/images-and-licensing.md).

## Minimal examples

### Batch on CPU

```bash
# Audio via STDIN
cat ~/example.wav | docker run -i \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0

# Audio mapped to /input.audio
docker run \
    -v ~/example.wav:/input.audio \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0
```

JSON transcript goes to stdout, logs to stderr. Exit code 0 means success. Map a job config to `/config.json` (or pass `--job-config <path>` after the image name). Input limit: 2 hours or 4GB.

### Realtime on CPU

```bash
docker run \
    -p 9000:9000 \
    -p 8001:8001 \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    rt-asr-transcriber-en:17.1.0
```

Connect a WebSocket client to `ws://localhost:9000/v2`, send `StartRecognition`, then binary audio. The docs example with the CLI:

```bash
speechmatics transcribe --additional-vocab gnocchi --url ws://localhost:9000/v2 --ssl-mode=none test.mp3
```

### GPU inference server plus transcriber

```bash
docker run --rm -it \
    -v $PWD/license.json:/license.json \
    --gpus '"device=0"' \
    -e CUDA_VISIBLE_DEVICES \
    -p 8001:8001 \
    speechmaticspublic.azurecr.io/sm-gpu-inference-server-en:17.1.0

docker run --rm -it \
  -e SM_INFERENCE_ENDPOINT=<server>:<port> \
  -v $PWD/license.json:/license.json \
  -v $PWD/example.wav:/input.audio \
  <speech_container_image_name>
```

The server defaults to batch mode. For realtime transcribers, start it with `-e SM_BATCH_MODE=false`. One server supports one mode at a time and one GPU.

### Melia 1 or Oak 1

```bash
docker run --rm -it \
    -v $PWD/license.json:/license.json \
    --gpus '"device=0"' \
    -e CUDA_VISIBLE_DEVICES \
    -p 8001:8001 \
    speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0

docker run --rm -it \
  -e SM_INFERENCE_ENDPOINT=<server>:<port> \
  -e SM_ASR_MODE=batch \
  -v $PWD/license.json:/license.json \
  -v $PWD/example.wav:/input.audio \
  speechmaticspublic.azurecr.io/sm-asr-transcriber:1.13.0
```

Set `"model": "melia-1"` or `"oak-1"` and `"language": "multi"` in `transcription_config`. For Realtime, start the server with `SM_STREAMING=true` and the transcriber with `SM_ASR_MODE=rt` and `-p 9000:9000` (requires `1.13.0` or later).

## Essential environment variables

| Variable | Container | Effect |
|---|---|---|
| `LICENSE_TOKEN` | Transcribers, language ID | License token. Overrides `/license.json` |
| `SM_INFERENCE_ENDPOINT` | Transcribers | gRPC endpoint `<server>:<port>` of the GPU inference server |
| `SM_BATCH_MODE` | Standard/Enhanced inference server | `false` selects realtime mode. Default is batch |
| `SM_MODEL` | Standard/Enhanced inference server | `standard` or `enhanced`: load one model only. Must be `standard` on the `standard-all` image. Replaces deprecated `SM_OPERATING_POINT` |
| `SM_LANGUAGES` | Standard/Enhanced inference server | Comma-separated codes to load, for example `en,de,fr`. From 15.18.0. Unknown code fails startup |
| `SM_STREAMING` | Melia 1/Oak 1 inference server | `true` selects Realtime mode |
| `SM_ASR_MODE` | `sm-asr-transcriber` | `batch` or `rt` |
| `SM_MAX_CONCURRENT_CONNECTIONS` | Realtime transcribers | Max concurrent WebSocket sessions. Default accepts one |
| `SM_PREWARM_ENGINE_MODES` | Realtime transcriber | `{language}_{domain}_{processor}_{model}:{n}` list separated by `;` |
| `SM_SPLIT_RETRY_TIMEOUT` | Batch transcriber with GPU | Seconds to retry the inference connection. Default 60 |
| `SM_CUSTOM_DICTIONARY_CACHE_TYPE` | Transcribers | `shared` enables the cache mounted at `/cache` |
| `SM_CUSTOM_DICTIONARY_CACHE_ENTRY_MAX_SIZE` | Transcribers | Max cached entry size in bytes. Default `-1` (no limit) |
| `SM_TRANSLATION_ENDPOINT` | Transcribers | gRPC endpoint of the translation inference server |
| `SM_TRANSLATION_MAX_TARGET_LANGUAGES` | Transcribers | Max target languages per request. Default 5; `0` disables the limit |
| `SM_SPEAKER_ID_SECRETS_DIR` | Transcribers | Directory in the container holding `s.<integer>` secret files |
| `SM_ENABLE_USAGE_REPORTING` | Transcribers | `false`, `no` or `0` turns off automatic usage reporting |
| `SM_EATS_URL` | Transcribers | Usage event destination, for example `asr-usage.example.net:9090` |
| `SM_JOB_ID`, `SM_LOG_DIR` | Batch transcriber | Write logs to `<SM_LOG_DIR>/<SM_JOB_ID>/` |
| `DEBUG` | Realtime transcriber | `true` enables verbose logging |
| `SM_BATCH_WORKER_LISTEN_PORT`, `SM_BATCH_WORKER_MAX_JOB_HISTORY` | Batch persistent worker | Internal port (default `18000`); completed job records kept in memory |

## Batch transcriber arguments

Arguments go after the image name.

| Argument | Effect |
|---|---|
| `--parallel=N` | Use N cores. Files are split into 5 minute chunks; optimum is audio minutes / 5. Must be at least 1 |
| `--all-formats <dir>` (or `--allformats`) | Write JSON, TXT and SRT to a mounted directory |
| `--job-config <path>` | Path in the container to the job config |
| `--run-mode http` | Run as a batch persistent worker (from 15.7.0) |
| `-stderr` | Send logs to stderr |

## Ports

| Port | Container | Use |
|---|---|---|
| 9000 | Realtime transcriber | WebSocket, path `/v2` |
| 8001 | Realtime transcriber | Health service: `/started`, `/live`, `/ready`, `/session_status` |
| 8001 | Inference servers | gRPC inference |
| 8000 / 8002 | Inference servers | Triton HTTP / Prometheus metrics |
| 18000 | Batch persistent worker | HTTP job API and `/live`, `/ready` |
| 9090 / 8000 | Usage container | `v1/log` ingest / `v1/export` |

Port 8001 is used by both the realtime health service and the inference server gRPC endpoint; remap one when they share a host.

## Gotchas

- CPU images are one per language pack. Repeat pulls per language.
- Hosts need a CPU with AVX. `err: signal: illegal instruction` means AVX is missing; pass AVX through any hypervisor.
- With `--parallel=N`, budget `N` times the per-container RAM (up to 5GB each).
- GPU: Nvidia GPU with at least 16GB memory, CUDA compute capability 7.5-12.1, 24 GB RAM, nvidia-container-toolkit, Docker > 19.03. Container 15.0.0+ needs Nvidia driver 580 or later; 14.13.0 and lower need 525 or later.
- Batch speaker identification requires GPU inference. Realtime speaker identification works on CPU and GPU.
- Spanish and English bilingual (`es-bilingual-en` images) is GPU-only.
- Translation needs transcriber 10.3.0 or newer and a license with translation enabled.
- A realtime `/ready` probe has a 2 second resolution; bursts inside that window can land on one container.
- Automatic usage reporting is on by default from 10.6.0. Air-gapped deployments must run a usage container and email exports monthly.
- Speechmatics Support expects issues to be reproduced on the unmodified image.

## Feature availability on-prem

Not available on-prem (SaaS only): alignment, auto chapters, Entity Detection, feature discovery, the Batch API language identification feature, PII Redaction, summarization, topic detection. Agent STT is SaaS only. Full table: [references/feature-availability.md](references/feature-availability.md).

## References

| Read | When |
|---|---|
| [references/images-and-licensing.md](references/images-and-licensing.md) | Finding the right image name or language pack, license file fields, license errors |
| [references/cpu-batch.md](references/cpu-batch.md) | Batch input methods, output, custom images, `--parallel`, multiple formats, shared custom dictionary cache |
| [references/cpu-realtime.md](references/cpu-realtime.md) | Realtime sessions, prewarming, read-only and non-root, health service endpoints |
| [references/gpu-inference.md](references/gpu-inference.md) | GPU requirements, Standard and Enhanced server, Melia 1 and Oak 1, Docker Compose files, monitoring |
| [references/gpu-translation.md](references/gpu-translation.md) | Translation inference server setup and errors |
| [references/language-id.md](references/language-id.md) | Language ID container usage, output and errors |
| [references/batch-persistent-worker.md](references/batch-persistent-worker.md) | Long-lived HTTP batch worker: job API, capacity, health |
| [references/security.md](references/security.md) | tmpfs, read-only, non-root, Kubernetes security context, speaker identification secrets |
| [references/performance-and-cost.md](references/performance-and-cost.md) | Benchmarks, throughput, session density, sizing |
| [references/troubleshooting.md](references/troubleshooting.md) | Exit codes, logging, license error messages |
| [references/usage-reporting.md](references/usage-reporting.md) | Automatic and offline usage reporting, usage container, exports |
| [references/feature-availability.md](references/feature-availability.md) | Checking whether a feature works on-prem |
