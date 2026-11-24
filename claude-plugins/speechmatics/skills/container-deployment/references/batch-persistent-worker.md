# Batch persistent worker

Docs: https://docs.speechmatics.com/deployments/container/batch-persistent-worker

Available from container version 15.7.0.

A batch persistent worker (also called the HTTP batch worker) is a long-running batch transcriber. It loads the models once at startup, then accepts jobs over an HTTP API for the lifetime of the container. A standard batch container starts, processes one job, and exits.

## When to use

| | Standard batch | Persistent worker |
|---|---|---|
| Startup cost | Per job | Once |
| Memory usage | One container per job | Multiple jobs share one container |
| CPU/GPU utilization | Interrupted between jobs | Continuous |
| Best for | Large, infrequent files | High throughput or smaller files |

- Model loading, especially onto GPU, takes several seconds. For a ten second clip, startup can exceed transcription time. For a five minute file it is negligible.
- A standard batch container leaves the GPU idle between jobs; a persistent worker keeps it warm.
- For long audio, the real-time factor (RTF) is similar to a standard batch job.

## Deploying

```bash
docker run -it \
  -e LICENSE_TOKEN=$TOKEN_VALUE \
  -e SM_INFERENCE_ENDPOINT=<server>:<port> \
  -p PORT:18000 \
  batch-asr-transcriber-en:17.1.0 \
  --run-mode http \
  --parallel=4 \
  --all-formats /output_dir_name
```

| Parameter | Description |
|---|---|
| `--run-mode http` | Run as a persistent worker |
| `--parallel` | Number of parallel engines. Each engine maps to one GPU connection when used with a GPU inference server |
| `--all-formats` | Directory where all job outputs and logs are saved. Defaults to `/tmp/jobs` if omitted |
| `PORT` | Local port forwarded to the container's internal port `18000` |

| Environment variable | Description |
|---|---|
| `SM_BATCH_WORKER_LISTEN_PORT` | Override the default internal port (`18000`) |
| `SM_BATCH_WORKER_MAX_JOB_HISTORY` | Maximum number of completed job records to retain in memory |

"Engines" are the worker's processing units. The worker handles up to `--parallel` engines at once, and a single job can be assigned several engines to cut its own turnaround time.

For Melia 1 and Oak 1, run `sm-asr-transcriber` with `SM_ASR_MODE=batch` and `command: --run-mode http --parallel=10`. See the Docker Compose file in [gpu-inference.md](gpu-inference.md#melia-1-and-oak-1-batch-persistent-worker).

## Submitting a job

`POST /v2/jobs` with an audio file and transcription config. The worker queues the job and returns a `job_id` immediately. Poll `GET /v2/jobs/{job_id}` and fetch the transcript when the status is `DONE`.

```bash
curl -X POST address.of.container:PORT/v2/jobs \
  -H 'X-SM-Processing-Data: {"parallel_engines": 2, "user_id": "MY_USER_ID"}' \
  -F 'config={
    "type": "transcription",
    "transcription_config": {
      "language": "en",
      "diarization": "speaker",
      "model": "enhanced"
    }
  }' \
  -F 'data_file=@~/audio_file.mp3'
```

Python SDK:

```python
import asyncio
import os
from dotenv import load_dotenv
from speechmatics.batch import AsyncClient

load_dotenv()

async def main():
    client = AsyncClient(
        api_key=os.getenv("SPEECHMATICS_API_KEY"),
        url="address.of.container:PORT/v2"
    )
    result = await client.transcribe(
        "audio.wav",
        parallel_engines=2,
        user_id="MY_USER_ID"
    )
    print(result.transcript_text)
    await client.close()

asyncio.run(main())
```

### Fetching audio from a URL

Add `fetch_data` to the job config instead of uploading a file. Full options: https://docs.speechmatics.com/speech-to-text/batch/input#fetch-url

```bash
curl -X POST address.of.container:PORT/v2/jobs \
  -F 'config={
    "type": "transcription",
    "transcription_config": {
      "language": "en"
    },
    "fetch_data": {
      "url": "https://example.com/audio_file.mp3"
    }
  }'
```

## `X-SM-Processing-Data` header

A JSON object sent as a request header on `POST /v2/jobs`.

| Field | Description |
|---|---|
| `parallel_engines` | Number of engines to assign to this job. More engines means faster turnaround for the job and less concurrency for others |
| `user_id` | Enables per-customer encrypted speaker identifiers, as used in the SaaS offering |

## Managing capacity

### `GET /jobs`

Returns current engine usage and active jobs. Use `unused_engines` to decide how many engines to request for the next job. The docs write this capacity endpoint as `/jobs`, without the `/v2` prefix used by the job endpoints (`/v2/jobs`).

```json
{
  "active_jobs": [
    { "job_id": "f8a564954b334eecb823", "parallel_engines": 1 },
    { "job_id": "29351ae8cf2c4e8694f0", "parallel_engines": 1 }
  ],
  "max_engines": 8,
  "unused_engines": 6
}
```

### Requesting parallel engines

```bash
curl -X POST address.of.container:PORT/v2/jobs \
  -H 'X-SM-Processing-Data: {"parallel_engines": 2}' \
  -F 'config={"type": "transcription", "transcription_config": {"language": "en"}}' \
  -F 'data_file=@~/audio_file.mp3'
```

A job that requests more engines than are available is rejected:

```
HTTP 503: {"detail": "Server busy: 8 engines not available (2 engines in use, 5 parallel allowed)"}
```

## Speaker identification

Use the same job config as the one-shot batch container. Batch speaker identification requires the GPU inference server; it is not supported in batch mode on CPU. Pass `user_id` in `X-SM-Processing-Data` for per-customer encrypted identifiers:

```bash
curl -X POST address.of.container:PORT/v2/jobs \
  -H 'X-SM-Processing-Data: {"user_id": "MY_USER_ID"}' \
  -F 'config={
    "type": "transcription",
    "transcription_config": {
      "language": "en",
      "diarization": "speaker",
      "model": "enhanced"
    }
  }' \
  -F 'data_file=@~/audio_file.mp3'
```

Secrets setup: [security.md](security.md#speaker-identification-secrets).

## Job API reference

The worker API mirrors the SaaS Batch API v2 (https://docs.speechmatics.com/api-ref/batch/create-a-new-job), so SaaS and on-prem are interchangeable. See `speechmatics:batch-transcription` for the endpoints. Differences:

Not supported:

- The `include_deleted` parameter on `GET /v2/jobs`
- `GET /v2/usage`
- Deleting a job (`DELETE /v2/jobs/{job_id}`)

Added: `GET /v2/jobs/{job_id}` also returns `request_id`.

## Health endpoints

On the same port as job submission. Designed as Kubernetes liveness and readiness probes.

### `GET /live`

Returns `200` when all container services are running and healthy.

```json
{ "live": true }
```

### `GET /ready`

Returns `200` when at least one engine slot is free, `503` when all engines are occupied. Includes the number of engines in use.

```json
{
  "ready": true,
  "engines_used": 0
}
```
