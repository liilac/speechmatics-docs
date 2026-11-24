# Limits and troubleshooting

Docs: https://docs.speechmatics.com/speech-to-text/batch/limits and https://docs.speechmatics.com/speech-to-text/batch/troubleshooting

These pages cover the Batch SaaS. For on-prem troubleshooting, see https://docs.speechmatics.com/deployments/container/cpu-speech-to-text.

## Rate limiting and fair usage

Speechmatics Batch SaaS applies rate limiting and fair queueing. A burst of requests may fail with `HTTP 429 - Rate Limited`. Stay under these recommended rates:

| Request | Recommended maximum |
|---|---|
| New jobs (POST) | 10 per second |
| Job status requests (GET) | 50 per second |

- Use notifications for job status updates in production rather than polling.
- With many concurrent jobs, the most recently submitted jobs may take longer to complete.
- There is generally no limit on the number of jobs you can submit, with one backstop: 20,000 concurrent jobs. Beyond that, POST returns `HTTP 429 - Max concurrent running jobs exceeded`. This is unlikely in normal operation but can happen if very slow audio fetching from your servers builds up a backlog.

## File size

A media file uploaded in the body of `POST /jobs` must be less than 1 GB or the job is rejected. For larger files, provide a URL with `fetch_data`.

## Custom dictionary

A job whose `additional_vocab` has more than 20,000 items is rejected with `HTTP 400 Bad Request` and error `Job rejected`.

## Data retention

Audio files, transcripts, and configuration data are stored for 7 days. A request for a transcript or file more than 7 days after processing fails, and the job status is `expired`. The limits page describes this as an HTTP 404; the API spec defines `410` (`Job Expired`, `File Expired`) for expired jobs and files. Handle both.

Delete audio or transcripts earlier with `DELETE /jobs/{jobid}`.

## First checks

Before raising a ticket, check:

1. API endpoint
2. Language code
3. API key expiration

## Errors by status code

| Code | Meaning | Action |
|---|---|---|
| 400 | Bad request, for example `Job rejected` with `detail` `Job config JSON is invalid` | Read `detail`. Fix the config |
| 401 | No API key provided, or the wrong API endpoint for the key's region | Send `Authorization: Bearer $API_KEY`. Use the endpoint for the key's region |
| 403 | `Entitlement check failed`: the key has expired or does not have a feature requested in the config | Check key expiry and the features in the config |
| 404 | `Job not found`, or the transcript is not ready yet | Check the job ID. Retry the transcript request, or use `wait` |
| 410 | `Job Expired` or `File Expired` | The data passed the retention period or was deleted |
| 422 | Invalid query parameter, for example `limit in query must be of type int64` | Fix the parameter |
| 423 | `Resource Locked`: deleting a running job without `force` | Pass `force=true` |
| 429 | Rate limited, or `Max concurrent running jobs exceeded` | Add a 1-second delay between requests of the same type, for example between `GET /v2/jobs/{job_id}` requests |
| 500 | Internal server error | The docs give no specific action. See [Raise an incident](#raise-an-incident) |
| 503 | Service unavailable (rare) | Retry immediately. If it persists, raise an incident |

### 401 response format

The 401 response may be returned as HTML:

```html
<html>
  <head>
    <title>401 Authorization Required</title>
  </head>

  <body>
    <center>
      <h1>401 Authorization Required</h1>
    </center>
    <hr />
    <center>nginx</center>
  </body>
</html>
```

HTTP 401 and 429 responses are moving to `application/json`:

```json
{"code": 401, "error": "Unauthorized"}
```

Do not assume a JSON body on 401 or 429. Check the status code first, then `Content-Type`.

### 403 response

```json
{
  "code": 403,
  "detail": "Entitlement check failed",
  "error": "Forbidden"
}
```

## Rejected jobs

A job can be accepted (HTTP 201) and later move to `status` `rejected`. Read `job.errors[]` from `GET /jobs/{jobid}`. Common causes in the docs:

| Cause | Where to look |
|---|---|
| Audio could not be fetched from `fetch_data.url` | [job-config.md](job-config.md) |
| Language identification failed or the language was unexpected | [language-identification.md](language-identification.md) |
| Uploaded file of 1 GB or more | [job-config.md](job-config.md) |
| Output locale combined with `"language": "auto"` | [language-identification.md](language-identification.md) |

A notification delivery failure also writes to `job.errors[]`, but the job stays `done`. See [notifications.md](notifications.md).

## Terminate a job

To stop a job that seems stuck, runs too long, or is no longer needed, delete it with the `force` parameter:

```bash
curl -L -X DELETE "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}?force=true" \
  -H "Authorization: Bearer ${API_KEY}"
```

## Raise an incident

Contact Support at https://support.speechmatics.com. Provide:

- A thorough description of the error
- Any relevant job or session IDs
- The configuration used to submit the job

A successful submission returns the job ID in the body and a `Request-Id` header:

```
HTTP/1.1 201 Created
Content-Length: 20
Content-Type: application/json
Request-Id: df6ec500191bf2c02ee42d519fbea34f
Strict-Transport-Security: max-age=15724800; includeSubDomains
X-Azure-Ref: 01mDmXAAAAABUtz6ZgS7QRI2F3f5B+19wTE9OMjFFREdFMDMxMgBhN2JjOWQ4MC02YjBiLTQ1NWEtYjE3MS01NGJkZmNiYWE0YTk=
Date: Thu, 23 May 2019 08:59:08 GMT

{"id":"z2jfp1jwu1"}
```

If no job ID was returned, provide the `Request-Id` and `X-Azure-Ref` response headers. Log both headers on every failed request so they are available for a ticket.

## Status page

Check service health at https://status.speechmatics.com/.
