---
name: batch-transcription
description: Transcribes pre-recorded audio and video files with the Speechmatics Batch API (REST, https://eu1.asr.api.speechmatics.com/v2). Use when creating a transcription job (POST /jobs with data_file upload or fetch_data URL), writing a job config (transcription_config, model, language, language_hints), polling job status, retrieving transcripts in json-v2, txt, or srt, blocking with the wait query parameter (synchronous transcription), configuring notification_config webhooks, batch speaker or channel diarization, batch speaker identification (get_speakers, speakers), language identification (language auto, language_identification_config), alignment jobs, the /usage endpoint, rate and file size limits, or debugging 401, 403, 429, and rejected jobs. Also covers the speechmatics-batch Python package and @speechmatics/batch-client JavaScript client.
---

# Batch transcription

Transcribe pre-recorded files with the Speechmatics Batch API: submit a job, wait for it to finish, fetch the transcript.

## When to use this skill

Use it for anything file-based and asynchronous: job creation, job config, status, transcripts, webhooks, limits, and Batch API errors.

Use a sibling skill instead for:

- API keys, temporary keys, regions and endpoints, model and language selection: `speechmatics:get-started`
- Custom dictionary, generic diarization concepts, translation, Entity Detection, PII Redaction, audio events, punctuation and formatting: `speechmatics:transcription-features`
- Summarization, sentiment analysis, topic detection, auto chapters: `speechmatics:speech-intelligence`
- Live audio over WebSocket: `speechmatics:realtime-transcription`
- Account, billing, and key management: `speechmatics:account-administration`

## Prerequisites

- An API key from the portal (`https://portal.speechmatics.com/settings/api-keys`). Store it as a managed secret. Enterprise customers may need to contact Support for keys.
- Send it on every request as `Authorization: Bearer $API_KEY`. A temporary key (JWT) is also accepted.
- An API key is linked to a specific region. Using it against the wrong regional endpoint returns 401.
- Optional client library: `pip install speechmatics-batch` (Python) or `npm install @speechmatics/batch-client` (JavaScript).

## Endpoints

Base URL used throughout the docs: `https://eu1.asr.api.speechmatics.com/v2`. For other regions, see `speechmatics:get-started`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs` | Create a job (multipart form: `config`, optional `data_file`) |
| GET | `/jobs` | List jobs (`limit`, `created_before`, `include_deleted`) |
| GET | `/jobs/{jobid}` | Job details and status (`wait`) |
| DELETE | `/jobs/{jobid}` | Delete a job (`force` to terminate a running job) |
| GET | `/jobs/{jobid}/transcript` | Transcript (`format`, `wait`) |
| GET | `/usage` | Usage statistics (`since`, `until`) |

Full parameters, response schemas, and error codes: [references/api-reference.md](references/api-reference.md).

## Minimal working examples

### curl

```bash
API_KEY="YOUR_API_KEY"
PATH_TO_FILE="example.wav"

curl -L -X POST "https://eu1.asr.api.speechmatics.com/v2/jobs/" \
-H "Authorization: Bearer ${API_KEY}" \
-F data_file=@${PATH_TO_FILE} \
-F config='{"type": "transcription","transcription_config": { "model":"enhanced", "language": "en" }}'
```

The response is HTTP 201 with `{"id":"z2jfp1jwu1"}`. Then:

```bash
# Status: running | done | rejected | deleted | expired
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/$JOB_ID" \
-H "Authorization: Bearer $API_KEY"

# Transcript as plain text (default is json-v2; srt also available)
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/transcript?format=txt" \
  -H "Authorization: Bearer ${API_KEY}"
```

### One call (SaaS on Cloud only)

```bash
# Create a job and block for up to 60 seconds for a plain-text transcript
curl -L -X POST "https://eu1.asr.api.speechmatics.com/v2/jobs/?wait=60&format=txt" \
-H "Authorization: Bearer ${API_KEY}" \
-F data_file=@${PATH_TO_FILE} \
-F config='{"type": "transcription","transcription_config": { "model": "enhanced", "language": "en" }}'
```

Returns `{"id": "...", "status": "done", "txt": "..."}`, or `"status": "created"` if `wait` elapsed first. Details: [references/synchronous.md](references/synchronous.md).

### Python (`speechmatics-batch`)

```python
import asyncio
from speechmatics.batch import AsyncClient, TranscriptionConfig

API_KEY = "YOUR_API_KEY"
AUDIO_FILE= "example.wav"

config = TranscriptionConfig(
    diarization="speaker",
    language="en",
    model="enhanced"
)

async def main():
    client = AsyncClient(api_key=API_KEY)
    result = await client.transcribe(
        audio_file=AUDIO_FILE,
        transcription_config=config
    )
    print(result.transcript_text)
    await client.close()

asyncio.run(main())
```

### JavaScript (`@speechmatics/batch-client`, Node.js)

```javascript
import { openAsBlob } from "node:fs";
import { BatchClient } from "@speechmatics/batch-client";

const client = new BatchClient({
  apiKey: "YOUR_API_KEY",
  appId: "nodeJS-example",
});

async function transcribeFile() {
  const blob = await openAsBlob("./example.wav");
  const file = new File([blob], "example.wav");

  const response = await client.transcribe(
    file,
    {
      transcription_config: {
        language: "en",
        model: "enhanced",
      },
    },
    "json-v2",
  );

  console.log(
    // Transcripts can be strings when the 'txt' format is chosen
    typeof response === "string"
      ? response
      : response.results.map((r) => r.alternatives?.[0].content).join(" "),
  );
}

transcribeFile();
```

Per-endpoint SDK calls (`submit_job`, `list_jobs`, `get_job_info`, `get_transcript`, `delete_job`; `createTranscriptionJob`, `listJobs`, `getJob`, `getJobResult`, `deleteJob`): [references/api-reference.md](references/api-reference.md).

## Job config essentials

`config` is a JSON string in the multipart form. `type` is required; `transcription_config.language` is required for transcription.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "diarization": "speaker"
  },
  "fetch_data": { "url": "https://example.com/audio.mp3" },
  "notification_config": [
    { "url": "https://collector.example.org/callback", "contents": ["transcript"] }
  ],
  "tracking": { "title": "My job", "reference": "ref-1", "tags": ["a"] },
  "output_config": { "srt_overrides": { "max_line_length": 37, "max_lines": 2 } }
}
```

| Field | Values and notes |
|---|---|
| `type` | `transcription` |
| `transcription_config.model` | `standard`, `enhanced`, `melia-1`, `oak-1`. `operating_point` is the deprecated alias |
| `transcription_config.language` | A language code for Standard and Enhanced; `multi` for Melia 1 and Oak 1; `auto` for language identification (not Melia 1) |
| `transcription_config.language_hints` | Melia 1 and Oak 1 only. Restricts language labels to the hinted languages and biases transcription toward them |
| `transcription_config.diarization` | `none` (default), `speaker`, `channel` |
| `transcription_config.speaker_diarization_config` | `speaker_sensitivity` (0 to 1, default 0.5), `prefer_current_speaker` (default `false`), `get_speakers`, `speakers` |
| `transcription_config.channel_diarization_labels` | One label per channel; pattern `^[A-Za-z0-9._]+$` |
| `fetch_data` | `url` (required), `auth_headers`. Use instead of `data_file` |
| `notification_config` | Array of callbacks: `url` (required), `contents`, `method` (`post` default, `put`), `auth_headers` |
| `tracking` | `title`, `reference`, `tags`, `details`; echoed in job details and transcript |
| `output_config.srt_overrides` | `max_line_length` (default 37), `max_lines` (default 2) |
| `language_identification_config` | `expected_languages`, `low_confidence_action`, `default_language` |

Complete schema, including the fields owned by sibling skills: [references/job-config.md](references/job-config.md).

## Input

- Supported file types (exhaustive): `wav`, `mp3`, `aac`, `ogg`, `mpeg`, `amr`, `m4a`, `mp4`, `flac`.
- The type must be detectable by data inspection. Raw audio without an embedded codec (for example `.raw`, `.g729`) cannot be processed.
- Fastest format: 16-bit 16 kHz mono WAV (no preprocessing).
- Uploaded files must be under 1 GB. For larger files, use `fetch_data`.

## Output

- Job `status`: `running`, `done`, `rejected`, `deleted`, `expired`.
- Transcript `format`: `json-v2` (default), `txt`, `srt`. Word timestamps, speakers, translations, and speech intelligence results are in `json-v2` only.
- `results[]` items have `type` (`word`, `punctuation`, `entity`), `start_time`, `end_time`, and `alternatives[]` with `content`, `confidence`, `language`, and optional `speaker`. Ignore unrecognized item types.
- JSON transcript format version is `2.9` (current at time of writing; check the docs).

Schema and examples: [references/output.md](references/output.md).

## Limits

| Limit | Value |
|---|---|
| New jobs (POST) | 10 per second recommended |
| Status requests (GET) | 50 per second recommended |
| Concurrent jobs backstop | 20,000 (`HTTP 429 - Max concurrent running jobs exceeded`) |
| Uploaded file size | Under 1 GB; use `fetch_data` above that |
| Custom dictionary | 20,000 items (`additional_vocab`); more returns `HTTP 400`, `Job rejected` |
| Data retention | 7 days for audio, transcripts, and config |
| List jobs | 100 most recent jobs from the past 7 days |
| Notification URLs | Up to 3 per request |
| Channel diarization | Up to 100 separate input files |
| Speaker identifiers | 50 across all `speakers` |

## Gotchas

- `GET /jobs/{jobid}` and `GET /jobs/{jobid}/transcript` apply a short default wait (currently 5 seconds, subject to change). Pass `wait=0` to return immediately. Do not build logic around the default duration.
- `wait` is SaaS on Cloud only; on-prem deployments do not support it. `POST /jobs` has no default wait.
- With `wait` on `POST /jobs`, the response is always HTTP 201. Check the `status` field: `created` means still running. If `status` is `done` but no transcript key is present, fetch the transcript endpoint.
- The `status` on the `POST /jobs?wait=` response (`created`, `done`, `rejected`, `deleted`) is not the job lifecycle status from `GET /jobs/{jobid}`. Notification `status` query values (`success`, `error`, `fetch_error`, `trim_error`) are a third, separate set.
- `GET /jobs/{jobid}/transcript` returns HTTP 404 while the transcript is not ready.
- `DELETE /jobs/{jobid}` on a running job returns HTTP 423 unless `force=true`.
- A failed `fetch_data` download sets `status` to `rejected`; read `job.errors[]` from `GET /jobs/{jobid}`.
- A failed notification does not fail the job: `status` stays `done` and the failures appear in `job.errors[]`.
- Melia 1 does not support `"language": "auto"`; use `"language": "multi"`.
- Batch speaker identification (`get_speakers`, `speakers`) is not supported by Melia 1 and Oak 1.
- `speaker_change` and `channel_and_speaker_change` were removed in July 2024. Use `"diarization": "speaker"`.
- In production, use notifications or `wait` rather than tight polling. On 429, add a 1-second delay between requests of the same type.
- Some docs samples use the older `speechmatics.batch_client.BatchClient` Python client with `ConnectionSettings`. Prefer `speechmatics.batch` (`speechmatics-batch`) for new code.

## References

- [references/job-config.md](references/job-config.md): read when writing or validating a job config, using `fetch_data`, `language_hints`, `tracking`, or the `sm-app` parameter.
- [references/output.md](references/output.md): read when parsing job status or the `json-v2` transcript, handling multilingual output, or producing SRT subtitles.
- [references/synchronous.md](references/synchronous.md): read when using the `wait` query parameter on any endpoint.
- [references/notifications.md](references/notifications.md): read when configuring webhooks, building the receiving endpoint, or allowlisting egress IPs.
- [references/diarization-and-speaker-identification.md](references/diarization-and-speaker-identification.md): read when separating speakers or channels, tuning diarization, or enrolling and identifying known speakers.
- [references/language-identification.md](references/language-identification.md): read when using `"language": "auto"` and `language_identification_config`.
- [references/alignment.md](references/alignment.md): read when asked to align an existing text to audio.
- [references/api-reference.md](references/api-reference.md): read for every endpoint's parameters, response schemas, error bodies, SDK calls, and the `/usage` endpoint.
- [references/limits-and-troubleshooting.md](references/limits-and-troubleshooting.md): read when hitting rate limits, 4xx or 5xx errors, stuck jobs, or raising a Support ticket.
