# Batch API REST reference

Docs: https://docs.speechmatics.com/api-ref/batch/create-a-new-job (API reference section) and https://docs.speechmatics.com/speech-to-text/batch/usage

- Base path: `/v2`. Scheme: `https`. Host used in the docs: `eu1.asr.api.speechmatics.com`. For other regions, see `speechmatics:get-started`.
- Authentication: `Authorization: Bearer $API_KEY`. The bearer value is your API key or a temporary key (JWT).
- Responses are `application/json` unless noted.

| Method | Path | Summary |
|---|---|---|
| POST | `/jobs` | Create a new job |
| GET | `/jobs` | List all jobs |
| GET | `/jobs/{jobid}` | Get job details |
| DELETE | `/jobs/{jobid}` | Delete a job |
| GET | `/jobs/{jobid}/transcript` | Get the transcript for a transcription job |
| GET | `/usage` | Get usage statistics |

## POST `/jobs`: create a new job

Docs: https://docs.speechmatics.com/api-ref/batch/create-a-new-job

Consumes `multipart/form-data`.

| Parameter | In | Type | Required | Notes |
|---|---|---|---|---|
| `config` | form | JSON string | Yes | A `JobConfig`. See [job-config.md](job-config.md) |
| `data_file` | form | file | No | The file to process. Alternatively use `fetch_data` in the config |
| `wait` | query | integer, min 0 | No | SaaS on Cloud only. Block for up to this many seconds. Capped server-side. See [synchronous.md](synchronous.md) |
| `format` | query | string | No | `json-v2` (default), `txt`, `srt`. Embedded transcript format. Only relevant when `wait` is set |
| `sm-app` | query | string | No | App usage tracking. Must be enabled by Support |
| `X-SM-Processing-Data` | header | JSON string | No | On-prem only. For example `{"parallel_engines": 4}` |

Response `201` (`CreateJobResponse`):

| Field | Notes |
|---|---|
| `id` | Required. The unique job ID. Keep it to retrieve the job later |
| `status` | Only present when `wait` was set: `created`, `done`, `rejected`, `deleted` |
| `json-v2` | Object. Best-effort: present when `status` is `done` and `format` was `json-v2` |
| `txt` | String. Best-effort: present when `status` is `done` and `format` was `txt` |
| `srt` | String. Best-effort: present when `status` is `done` and `format` was `srt` |

```json
{ "id": "dlbvi9xpzf" }
```

Errors:

| Code | Example body |
|---|---|
| 400 | `{"code": 400, "error": "Job rejected", "detail": "Job config JSON is invalid"}` |
| 401 | `{"code": 401, "error": "Permission Denied"}` |
| 403 | `{"code": 403, "error": "Invalid or missing license"}` |
| 429 | `{"code": 429, "error": "Max concurrent running jobs exceeded"}` |
| 500 | `{"code": 500, "error": "Internal Server Error"}` |

```bash
API_KEY="YOUR_API_KEY"

curl -L -X POST "https://eu1.asr.api.speechmatics.com/v2/jobs" \
  -H "Authorization: Bearer ${API_KEY}" \
  -F data_file=@example.wav \
  -F config='{"type": "transcription", "transcription_config": {"language": "en", "model": "enhanced"}}'
```

```python
from speechmatics.batch import Client, TranscriptionConfig

with Client(api_key="YOUR_API_KEY") as client:
    job = client.submit_job(
        "example.wav",
        transcription_config=TranscriptionConfig(language="en", model="enhanced"),
    )
    print(job.id)
```

```javascript
import { openAsBlob } from "node:fs";
import { BatchClient } from "@speechmatics/batch-client";

const client = new BatchClient({ apiKey: "YOUR_API_KEY", appId: "my-app" });

// In a browser, pass a File from a file input instead.
const file = new File([await openAsBlob("example.wav")], "example.wav");

const { id } = await client.createTranscriptionJob(file, {
  transcription_config: { language: "en", model: "enhanced" },
});
console.log(id);
```

## GET `/jobs`: list all jobs

Docs: https://docs.speechmatics.com/api-ref/batch/list-all-jobs

| Parameter | In | Type | Notes |
|---|---|---|---|
| `created_before` | query | date-time | UTC timestamp cursor for pagination. Filters on creation time to the nearest millisecond (accepts up to nanosecond precision, truncated). By default the response starts with the most recent job |
| `limit` | query | integer, 1 to 100 | Limit on the number of items returned |
| `include_deleted` | query | boolean | Include deleted jobs. Defaults to `false` |

The docs state this returns the 100 most recent jobs submitted in the past 7 days (the spec says no `limit` is applied by default; `limit` itself cannot exceed 100). `created_before` is the pagination cursor: pass a timestamp to get jobs created before it.

Response `200` (`RetrieveJobsResponse`): `{ "jobs": [JobDetails, ...] }`, most recent first.

```json
{
  "jobs": [
    {
      "created_at": "2026-10-28T09:12:44.583Z",
      "data_name": "example.wav",
      "duration": 42,
      "id": "dlbvi9xpzf",
      "status": "done",
      "config": {
        "type": "transcription",
        "transcription_config": { "language": "en", "model": "enhanced" }
      }
    },
    {
      "created_at": "2026-10-27T16:03:10.112Z",
      "data_name": "interview.mp3",
      "duration": 1806,
      "id": "r9fk2m1x7q",
      "status": "running",
      "config": {
        "type": "transcription",
        "transcription_config": { "language": "en", "diarization": "speaker" }
      }
    }
  ]
}
```

On the batch virtual appliance, `config` is not present in the items of this list (it is present for `GET /jobs/{jobid}`).

Errors: 401 (`Permission Denied`), 422 (`{"code": 422, "error": "limit in query must be of type int64"}`), 429, 500.

```bash
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs?limit=10" \
  -H "Authorization: Bearer ${API_KEY}"
```

```python
from speechmatics.batch import Client

with Client(api_key="YOUR_API_KEY") as client:
    for job in client.list_jobs(limit=10):
        print(job.id, job.status)
```

```javascript
import { BatchClient } from "@speechmatics/batch-client";

const client = new BatchClient({ apiKey: "YOUR_API_KEY", appId: "my-app" });

const { jobs } = await client.listJobs({ limit: 10 });
for (const job of jobs) {
  console.log(job.id, job.status);
}
```

## GET `/jobs/{jobid}`: get job details

Docs: https://docs.speechmatics.com/api-ref/batch/get-job-details

Returns job details, including progress and any error reports.

| Parameter | In | Type | Notes |
|---|---|---|---|
| `jobid` | path | string | Required. For example `a1b2c3d4e5` |
| `wait` | query | integer, min 0 | Block for up to this many seconds for a terminal state. Capped server-side. A short default applies when omitted; `wait=0` returns immediately |

Response `200` (`RetrieveJobResponse`): `{ "job": JobDetails }`.

`JobDetails`:

| Field | Type | Notes |
|---|---|---|
| `created_at` | date-time | Required. UTC time the job was created |
| `data_name` | string | Required. Name of the data file submitted |
| `id` | string | Required |
| `status` | string | Required. `running`, `done`, `rejected`, `deleted`, `expired` |
| `duration` | integer | File duration in seconds. May be missing for fetch URL jobs |
| `text_name` | string | Name of the text file submitted to be aligned to audio |
| `config` | object | The `JobConfig` |
| `lang` | string | Backward compatibility with the v1 API |
| `errors` | array | `{ "timestamp", "message" }` items, for example `Audio fetch error, http status 418` |

```json
{
  "job": {
    "created_at": "2026-10-28T09:12:44.583Z",
    "data_name": "example.wav",
    "duration": 42,
    "id": "dlbvi9xpzf",
    "status": "done",
    "config": {
      "type": "transcription",
      "transcription_config": { "language": "en", "model": "enhanced" }
    }
  }
}
```

Errors: 401 (`Permission Denied`), 404 (`Job not found`), 410 (`Job Expired`), 429, 500.

```bash
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

```python
from speechmatics.batch import Client

with Client(api_key="YOUR_API_KEY") as client:
    job = client.get_job_info("JOB_ID")
    print(job.status)
```

```javascript
const { job } = await client.getJob("JOB_ID");
console.log(job.status);
```

## DELETE `/jobs/{jobid}`: delete a job

Docs: https://docs.speechmatics.com/api-ref/batch/delete-a-job

Deletes a job and removes all associated resources.

| Parameter | In | Type | Notes |
|---|---|---|---|
| `jobid` | path | string | Required |
| `force` | query | boolean | When set, a running job is force terminated. When unset (default), a running job is not terminated and the request returns HTTP 423 Locked |

Response `200`: `{ "job": JobDetails }` with `"status": "deleted"`.

Errors: 401 (`Permission Denied`), 404 (`Job not found`), 410 (`Job Expired`), 423 (`{"code": 423, "error": "Resource Locked"}`), 429, 500.

```bash
curl -L -X DELETE "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}" \
  -H "Authorization: Bearer ${API_KEY}"
```

Terminate a running job:

```bash
curl -L -X DELETE "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}?force=true" \
  -H "Authorization: Bearer ${API_KEY}"
```

```python
from speechmatics.batch import Client

with Client(api_key="YOUR_API_KEY") as client:
    client.delete_job("JOB_ID")
```

```javascript
const { job } = await client.deleteJob("JOB_ID");
console.log(job.status);
```

Deleting a completed job has no effect on reported usage.

## GET `/jobs/{jobid}/transcript`: get the transcript

Docs: https://docs.speechmatics.com/api-ref/batch/get-the-transcript-for-a-transcription-job

Produces `application/json`, `application/vnd.speechmatics.v2`, `application/vnd.speechmatics.v2+json`, or `text/plain`.

| Parameter | In | Type | Notes |
|---|---|---|---|
| `jobid` | path | string | Required |
| `format` | query | string | `json-v2` (default), `txt`, `srt` |
| `wait` | query | integer, min 0 | Block for up to this many seconds for the transcript. Capped server-side. A short default applies when omitted |

Response `200`: a `RetrieveTranscriptResponse` JSON object for `json-v2` (see [output.md](output.md)), or a string for `txt` and `srt`.

Errors:

| Code | Example body |
|---|---|
| 401 | `{"code": 401, "error": "Permission Denied"}` |
| 404 | `{"code": 404, "error": "Job not found"}`. Also returned while the transcript is not ready (`Transcription not ready`) |
| 410 | `{"code": 410, "error": "File Expired", "detail": "File deleted from the storage"}` |
| 429 | Rate limited |
| 500 | `{"code": 500, "error": "Internal Server Error"}` |

```bash
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/transcript?format=txt" \
  -H "Authorization: Bearer ${API_KEY}"
```

```python
from speechmatics.batch import Client

with Client(api_key="YOUR_API_KEY") as client:
    transcript = client.get_transcript("JOB_ID")
    print(transcript.transcript_text)
```

```javascript
const transcript = await client.getJobResult("JOB_ID", "text");
console.log(transcript);
```

## GET `/usage`: get usage statistics

Docs: https://docs.speechmatics.com/speech-to-text/batch/usage and https://docs.speechmatics.com/api-ref/batch/get-usage-statistics

Usage is the number of jobs successfully processed in a period and the total duration of their audio, for the account associated with the API key.

- Reported per Coordinated Universal Time (UTC) calendar day.
- Usage for the current UTC day is not included.
- Deleting a completed job has no effect on reported usage.

| Parameter | In | Type | Notes |
|---|---|---|---|
| `since` | query | date, `YYYY-MM-DD` | Include usage from this date (inclusive). If omitted, usage is reported from the day the first job was successfully processed for the account |
| `until` | query | date, `YYYY-MM-DD` | Include usage up to this date (inclusive). If omitted, usage is reported until the end of the previous UTC day |

```bash
curl -L -X GET "https://eu1.asr.api.speechmatics.com/v2/usage?since=2023-01-01&until=2023-12-31" \
    -H "Authorization: Bearer $API_KEY"
```

This returns usage for all jobs completed from the start of 1 January 2023 to the end of 31 December 2023. (The usage page then restates the range as "at or after 2023-01-01T00:00Z and before 2023-01-01T00:00Z", which contradicts this; the spec defines both `since` and `until` as inclusive dates.)

Response `200` (`UsageResponse`):

| Field | Type | Notes |
|---|---|---|
| `since` | date-time | Required |
| `until` | date-time | Required |
| `summary` | array of `UsageDetails` | Required. Totals by mode and type |
| `details` | array of `UsageDetails` | Required. Breakdown by language and model |

`UsageDetails`:

| Field | Type | Notes |
|---|---|---|
| `mode` | string | Required. `batch` |
| `type` | string | Required. `transcription` |
| `count` | integer | Required. Total number of billable jobs |
| `duration_hrs` | number | Required. Total duration of billable jobs in hours |
| `language` | string | For example `en` |
| `model` | string | `standard`, `enhanced`, `melia-1`, `oak-1` |
| `operating_point` | string | Deprecated alias of `model`; same values |

```json
{
  "since": "2026-10-01T00:00:00Z",
  "until": "2026-10-31T23:59:59Z",
  "summary": [
    { "mode": "batch", "type": "transcription", "count": 5, "duration_hrs": 1.53 }
  ],
  "details": [
    { "mode": "batch", "type": "transcription", "language": "en", "operating_point": "enhanced", "count": 4, "duration_hrs": 1.33 },
    { "mode": "batch", "type": "transcription", "language": "de", "operating_point": "standard", "count": 1, "duration_hrs": 0.2 }
  ]
}
```

Read both `model` and `operating_point` when parsing `details`; the spec's examples use either.

Errors: 401, 403, 429, 500.

## `ErrorResponse`

| Field | Type | Notes |
|---|---|---|
| `code` | integer | Required. The HTTP status code |
| `error` | string | Required. The error message |
| `detail` | string | The details of the error |

`error` values:

`Bad Request`, `File Expired`, `Forbidden`, `Resource Locked`, `Format Not Supported`, `Internal Server Error`, `Job error`, `Job Expired`, `Job In Progress`, `Job is not of type transcription`, `Job not found`, `Job rejected`, `Job rejected due to invalid audio`, `Job rejected due to invalid text`, `Malformed request`, `Missing callback`, `Missing data_file`, `No language selected`, `Not Implemented`, `Permission Denied`, `Requested product not available`, `Transcription not ready`, `Log file not available`, `Unprocessable Entity`, `Max concurrent running jobs exceeded`

## Client libraries

| Language | Package | Install | Entry points shown in the docs |
|---|---|---|---|
| Python | `speechmatics-batch` (https://github.com/speechmatics/speechmatics-python-sdk) | `pip install speechmatics-batch` | `from speechmatics.batch import Client, AsyncClient, TranscriptionConfig` |
| JavaScript | `@speechmatics/batch-client` (https://www.npmjs.com/package/@speechmatics/batch-client) | `npm install @speechmatics/batch-client` | `import { BatchClient } from "@speechmatics/batch-client"` |

Python calls shown in the docs:

| Call | Purpose |
|---|---|
| `Client(api_key=...)` as a context manager | Synchronous client |
| `AsyncClient(api_key=...)`, `await client.close()` | Async client |
| `await client.transcribe(audio_file=..., transcription_config=...)` | Submit, wait, and return a result with `.transcript_text` (shown on `AsyncClient`) |
| `client.submit_job("example.wav", transcription_config=TranscriptionConfig(...))` | Create a job; returns an object with `.id` |
| `client.list_jobs(limit=10)` | Iterate jobs with `.id`, `.status` |
| `client.get_job_info("JOB_ID")` | Job details with `.status` |
| `client.get_transcript("JOB_ID")` | Transcript with `.transcript_text` |
| `client.delete_job("JOB_ID")` | Delete a job |
| `TranscriptionConfig(language=..., model=..., diarization=...)` | Transcription config |

JavaScript calls shown in the docs:

| Call | Purpose |
|---|---|
| `new BatchClient({ apiKey, appId })` | Client |
| `client.transcribe(file, config, "json-v2")` | Submit, wait, and return the transcript (a string when a text format is chosen) |
| `client.createTranscriptionJob(file, config)` | Create a job; returns `{ id }` |
| `client.listJobs({ limit: 10 })` | Returns `{ jobs }` |
| `client.getJob("JOB_ID")` | Returns `{ job }` |
| `client.getJobResult("JOB_ID", "text")` | Transcript |
| `client.deleteJob("JOB_ID")` | Returns `{ job }` |

`file` is a `File`. In Node.js, build it with `new File([await openAsBlob("example.wav")], "example.wav")`. In a browser, pass a `File` from a file input.

Do not assume other methods or arguments exist; check the package's own documentation.

### Older Python client

Some docs samples (including the speech intelligence samples) use an older client:

```python
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"

settings = ConnectionSettings(
    url="https://eu1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {"type": "transcription", "transcription_config": {"language": LANGUAGE, "model": "enhanced"}}

# Open the client using a context manager
with BatchClient(settings) as client:
    try:
        job_id = client.submit_job(
            audio=PATH_TO_FILE,
            transcription_config=conf,
        )
        print(f"job {job_id} submitted successfully, waiting for transcript")

        # Note that in production, you should set up notifications instead of polling.
        # Notifications are described here: https://docs.speechmatics.com/speech-to-text/batch/notifications
        transcript = client.wait_for_completion(job_id, transcription_format="txt")
        # To see the full output, try setting transcription_format='json-v2'.
        print(transcript)
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key - Check your API_KEY at the top of the code!")
        elif e.response.status_code == 400:
            print(e.response.json()["detail"])
        else:
            raise e
```

Here `conf` is the full job config as a dict, so any config field (for example `notification_config` or `summarization_config`) can be added directly.
