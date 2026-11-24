# Synchronous transcription with `wait`

Docs: https://docs.speechmatics.com/speech-to-text/batch/synchronous

The `wait` query parameter blocks a request until the job reaches a terminal state (`done`, `rejected`, or `deleted`), so you can get a transcript in one call instead of polling. It applies to job creation, job status, and transcript retrieval.

- `wait` is available on SaaS on Cloud only. On-prem deployments do not support it.
- `wait` is an integer number of seconds, minimum 0, capped server-side. The docs and spec do not state the cap.
- If the job has not finished when `wait` elapses, the request returns the current state. Retry to keep waiting.

| Endpoint | Default when `wait` is omitted | On success within `wait` | When `wait` elapses |
|---|---|---|---|
| `POST /jobs` | No wait. Returns `{ "id" }` as soon as the job is created | HTTP 201, `status: "done"`, transcript embedded | HTTP 201, `status: "created"`, no transcript |
| `GET /jobs/{jobid}` | Short default wait | HTTP 200, job in terminal state | HTTP 200, job in current non-terminal state |
| `GET /jobs/{jobid}/transcript` | Short default wait | HTTP 200, transcript | HTTP 404 (transcription not ready) |

## Create a job and wait for the transcript

Add `format` to choose the embedded transcript format: `json-v2` (default), `txt`, or `srt`. `format` on `POST /jobs` is only relevant when `wait` is set.

```bash
API_KEY="YOUR_API_KEY"
PATH_TO_FILE="example.wav"

# Create a job and block for up to 60 seconds for a plain-text transcript
curl -L -X POST "https://eu1.asr.api.speechmatics.com/v2/jobs/?wait=60&format=txt" \
-H "Authorization: Bearer ${API_KEY}" \
-F data_file=@${PATH_TO_FILE} \
-F config='{"type": "transcription","transcription_config": { "model": "enhanced", "language": "en" }}'
```

The response is always HTTP 201. When `wait` is set, it includes a `status` field. On `done`, the transcript is embedded under a key named after the requested format.

For `format=txt` and `format=srt`, the value is a string:

```json
{
  "id": "a1b2c3d4e5",
  "status": "done",
  "txt": "Welcome to Speechmatics..."
}
```

For the default `format=json-v2`, the value is a nested object with the same shape as the transcript endpoint response, not a string (`results` abbreviated):

```json
{
  "id": "uwcl3jevp3",
  "status": "done",
  "json-v2": {
    "format": "2.9",
    "job": {
      "created_at": "2026-06-23T13:33:24.230Z",
      "data_name": "example.wav",
      "duration": 10,
      "id": "uwcl3jevp3"
    },
    "metadata": {
      "created_at": "2026-06-23T13:33:24.879071Z",
      "transcription_config": { "language": "en", "model": "enhanced" },
      "type": "transcription"
    },
    "results": [
      {
        "alternatives": [
          { "confidence": 1.0, "content": "I", "language": "en", "speaker": "UU" }
        ],
        "start_time": 1.5,
        "end_time": 1.79,
        "type": "word"
      }
    ]
  }
}
```

If the job is still running when `wait` elapses:

```json
{
  "id": "a1b2c3d4e5",
  "status": "created"
}
```

| `status` | Meaning |
|---|---|
| `created` | Created and still running, or `wait` elapsed before it finished. Retry to get the result |
| `done` | Finished. The transcript is embedded under the requested format key when available |
| `rejected` | The job could not be processed |
| `deleted` | The job was deleted before it could finish |

This `status` reports the outcome of the wait. It is distinct from the job lifecycle status returned by `GET /jobs/{jobid}` (`running`, `done`, `rejected`, `deleted`, `expired`).

The embedded transcript is best-effort. If `status` is `done` but no transcript key (`json-v2`, `txt`, or `srt`) is present, fetch it from `GET /jobs/{jobid}/transcript`.

After `status: "created"`, keep waiting with `GET /jobs/{jobid}?wait=N` or `GET /jobs/{jobid}/transcript?wait=N`. Do not resubmit the job.

## Wait when checking job status

```bash
# Wait up to 30 seconds for the job to reach a terminal state
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}?wait=30" \
-H "Authorization: Bearer ${API_KEY}"
```

The response is always HTTP 200 with the job in its current state. If the job is still running when `wait` elapses, retry.

## Wait for the transcript

```bash
# Wait up to 30 seconds for the transcript, then return it as plain text
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/transcript?wait=30&format=txt" \
-H "Authorization: Bearer ${API_KEY}"
```

If the transcript becomes ready within `wait`, the response is HTTP 200 with the transcript. Otherwise it returns the usual HTTP 404, and you retry.

## Default wait on the GET endpoints

`GET /jobs/{jobid}` and `GET /jobs/{jobid}/transcript` apply a default wait when `wait` is omitted. Existing polling code benefits without changes: each request returns as soon as the job reaches a terminal state.

The default is currently 5 seconds and will increase. Treat it as an unspecified short interval and do not build logic around a specific duration. To control the duration, pass `wait` explicitly. An explicit value overrides the default.

```bash
# Return the current job state without waiting
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}?wait=0" \
-H "Authorization: Bearer ${API_KEY}"
```

Set HTTP client timeouts longer than the `wait` you request.
