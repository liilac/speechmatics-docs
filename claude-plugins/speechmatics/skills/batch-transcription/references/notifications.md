# Notifications (webhooks)

Docs: https://docs.speechmatics.com/speech-to-text/batch/notifications

Speechmatics sends an HTTP request to a web service you control when a job finishes, so you do not need to poll. The request can carry the transcript, the media file, and job information.

## Configuration

Add `notification_config` (an array) to the job config:

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en",
    "model": "enhanced"
  },
  "notification_config": [
    {
      "url": "https://collector.example.org/callback",
      "contents": ["transcript", "data"],
      "auth_headers": ["Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhb"]
    }
  ]
}
```

The token in `auth_headers` is the one your service accepts, not the Speechmatics API key.

| Option | Mandatory | Description |
|---|---|---|
| `url` | Yes | Where the notification is sent. Up to 3 URLs are supported in a request |
| `contents` | No | Items to attach. See below |
| `method` | No | `post` (default) or `put` |
| `auth_headers` | No | List of additional headers added to the notification request, for example an OAuth2 bearer token |

`contents` values:

| Value | Content |
|---|---|
| `transcript` | The transcript in `json-v2` format |
| `transcript.json-v2` | The transcript in `json-v2` format |
| `transcript.txt` | The transcript in `txt` format |
| `transcript.srt` | The transcript in `srt` format |
| `data` | The media file provided in the job submission |
| `jobinfo` | The configuration information used to submit the job. Also present in the `json-v2` transcript |
| `text` | The text file submitted with an alignment job |

Notes:

- If no content is requested, the notification is an HTTP message containing only the job ID and status.
- On error, only `jobinfo` is sent back. Output items that are not available because the job was rejected or failed are omitted.
- Set up multiple notifications to different endpoints, for example `jobinfo` to one service and the transcript to another, or audio and transcript uploaded to an object store as distinct objects.
- Callbacks are invoked in parallel and may complete in any order. Some may succeed while others fail. Make downstream logic robust to both.
- Use `auth_headers` for systems that do not support auth tokens in query parameters, or to control the behavior of an object store or other existing endpoint.

## The request you receive

The job ID and status are appended as query parameters:

```
POST /callback?id=r6sr3jlzjj&status=success HTTP/1.1
Host: collector.example.org
```

`status` values (not the same as job status values):

| Value | Meaning |
|---|---|
| `success` | The job was processed successfully |
| `error` | Something went wrong with job processing |
| `fetch_error` | The data file could not be fetched from a URL |
| `trim_error` | The audio file could not be processed prior to transcription |

The user agent is `Speechmatics-API/2.0`.

### Body and MIME type

| Requested `contents` | `Content-Type` | Body |
|---|---|---|
| Exactly one of `transcript`, `transcript.json-v2`, `jobinfo` | `application/json` | The JSON item |
| Exactly one of `transcript.srt`, `transcript.txt` | `text/plain` | The SRT or text transcript |
| `data`, or two or more items | `multipart/form-data` | Items as named file attachments |

A callback with a single attachment sends the item as the request body rather than multipart. This allows writing an individual item directly to an object store such as Amazon S3.

### Responding

- Return a 2xx response. Without one, Speechmatics keeps retrying until it reaches its timeout threshold.
- Make sure the web server's request size limit is large enough for the transcript and, if requested, the original media file. A 413 (Request Entity Too Large) response is treated as a failure and retried.
- Check your web service's error logs when testing to confirm notifications are accepted and processed.

## Egress IP allowlist

To receive notifications, allowlist the egress IP addresses for the relevant environment. This also lets you verify that callbacks come from Speechmatics.

| Region | IP addresses |
|---|---|
| EU1 | `40.74.41.91`, `52.236.157.154`, `40.74.37.0`, `20.73.209.153`, `20.73.142.44` |
| EU2 | `20.105.89.153`, `20.105.89.173`, `20.105.89.184`, `20.105.89.98`, `20.105.88.228` |
| US1 | `52.149.21.32`, `52.149.21.10`, `52.137.102.83`, `40.64.107.92`, `40.64.107.99` |
| US2 | `52.146.58.224`, `52.146.58.159`, `52.146.59.242`, `52.146.59.213`, `52.146.58.64` |
| AU1 | `20.248.249.20`, `20.248.249.47`, `20.248.249.181`, `20.248.249.119`, `20.248.249.164` |

## Notification failure

If a notification cannot be delivered, the transcript is still available through the API. The job `status` stays `done`, and `GET /jobs/{jobid}` returns an `errors` array with each failed attempt:

```json
{
  "job": {
    "config": {
      "fetch_data": {
        "url": "https://example.com/average-files/punctuation1.mp3"
      },
      "notification_config": [
        {
          "contents": ["transcript", "jobinfo"],
          "url": "https://example.com"
        }
      ],
      "transcription_config": {
        "language": "de"
      },
      "type": "transcription"
    },
    "created_at": "2021-07-19T09:02:17.283Z",
    "data_name": "",
    "duration": 4,
    "errors": [
      {
        "message": "Error in sending notification: unable to send notification: HTTPError: Post \"https://example.com/500?id=1uyo82b1bv&status=success\": context deadline exceeded (Client.Timeout exceeded while awaiting headers), retrying",
        "timestamp": "2021-07-19T09:04:11.080Z"
      },
      {
        "message": "Error in sending notification: unable to send notification: Response status: 500, retrying",
        "timestamp": "2021-07-19T09:04:26.619Z"
      },
      {
        "message": "Error in sending notification: unable to send notification: Response status: 500, retrying",
        "timestamp": "2021-07-19T09:04:47.090Z"
      },
      {
        "message": "unable to send notification: unable to send notification: Response status: 500",
        "timestamp": "2021-07-19T09:05:17.347Z"
      },
      {
        "message": "Sending notification failed",
        "timestamp": "2021-07-19T09:05:17.570Z"
      }
    ],
    "id": "1uyo82b1bv",
    "status": "done"
  }
}
```

## Known ambiguity

The docs page says a notification with no `contents` carries only the job ID and status. The API spec says that if `contents` is not specified, the `transcript` item is sent as a file attachment named `data_file` for backward compatibility, and that an empty `contents` gives an empty body. Set `contents` explicitly to avoid depending on either behavior.
