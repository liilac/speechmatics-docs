# Authentication, temporary keys, and endpoints

Source: https://docs.speechmatics.com/get-started/authentication

## API keys

- Every request to the Speechmatics API needs an API key. Without it the response is `HTTP 401 - Unauthorized`.
- Create a key in the portal: sign in at https://portal.speechmatics.com, then go to **Settings > API Keys** (https://portal.speechmatics.com/settings/api-keys/). Enter a name, generate, and store the value. It cannot be shown again.
- An API key is scoped to one project. It can access only the transcripts produced in that project.
- Store and grant access to keys on the principle of least privilege. If a key is compromised, contact support at https://support.speechmatics.com.
- To create or revoke keys programmatically, use the Management API with a management token. See `speechmatics:account-administration`.

## Authenticate by product

### Batch

Include the key in the header of every request to the jobs API:

```bash
curl -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/" \
  -H "Authorization: Bearer $API_KEY"
```

### Realtime

Server-side: send the key in the header of the WebSocket connection request.

```http
GET /v2/ HTTP/1.1
Host: eu.rt.speechmatics.com
Upgrade: websocket
Connection: Upgrade
Authorization: Bearer YOUR_API_KEY
User-Agent: Python/3.8 websockets/8.1
```

Client-side: use a temporary key as a query parameter.

```text
wss://eu.rt.speechmatics.com/v2?jwt=$TEMP_KEY
```

### Agent STT

Server-side: send the key in the header of the WebSocket connection request to the `/v2/agent` path.

```http
GET /v2/agent HTTP/1.1
Host: eu.rt.speechmatics.com
Upgrade: websocket
Connection: Upgrade
Authorization: Bearer YOUR_API_KEY
User-Agent: Python/3.12 websockets/15.0
```

Client-side: agent STT uses Realtime (`type=rt`) temporary keys as a query parameter.

```text
wss://global.rt.speechmatics.com/v2/agent?jwt=$TEMP_KEY
```

## Supported endpoints

All production endpoints are active and highly available. Use more than one region to balance requests or to fail over.

Enterprise customers who want a region other than the one in their contract must contact their account manager or support.

### Batch SaaS

| Customer type | Region | Endpoint |
|---|---|---|
| All | EU1 (Europe) | `eu1.asr.api.speechmatics.com` |
| Enterprise | EU2 (Europe) | `eu2.asr.api.speechmatics.com` |
| All | US1 (USA) | `us1.asr.api.speechmatics.com` |
| Enterprise | US2 (USA) | `us2.asr.api.speechmatics.com` |
| All | AU1 (Australia) | `au1.asr.api.speechmatics.com` |

- Jobs are created in the region of the endpoint used. Use the same endpoint for all requests relating to a job.
- Melia 1 and Oak 1 are available on the EU1, US1, and AU1 endpoints only.
- EU2 and US2 exist for enterprise high availability and failover only. Jobs created there are not visible in the portal.

### Realtime SaaS

| Region | Endpoint |
|---|---|
| Global (auto-routed) | `global.rt.speechmatics.com` |
| EU1 (Europe) | `eu.rt.speechmatics.com` |
| US1 (USA) | `us.rt.speechmatics.com` |
| AU1 (Australia) | `au.rt.speechmatics.com` |

Path: `/v2`. `global.rt.speechmatics.com` routes each connection to the nearest region for lowest latency. It may route to any region; with data residency or compliance requirements, pin to a regional endpoint.

### Agent STT

Same hosts as Realtime, with the `/v2/agent` path, for example `wss://eu.rt.speechmatics.com/v2/agent`. The same `global.rt.speechmatics.com` routing and data residency warning applies.

## Temporary keys

A temporary key is a short-lived JWT that replaces the long-lived API key. It lets end users talk to Speechmatics directly, which reduces latency and development effort, without exposing the API key.

Enterprise customers must contact support or their account manager to use temporary keys.

### Endpoint

```text
POST https://mp.speechmatics.com/v1/jwts?type=<batch|rt>
Authorization: Bearer <API key>
Content-Type: application/json
```

| URL query parameter | Required | Description |
|---|---|---|
| `type` | No | String: `batch` (default) or `rt`. Whether the token can use the Batch API, or the Realtime and agent STT APIs. |

| Request body parameter | Required | Description |
|---|---|---|
| `ttl` | Yes | Integer, 60-86400. Time to live in seconds. Use the shortest TTL possible to minimize security risk. |
| `client_ref` | No | String. With it, `batch` tokens can create and retrieve only jobs with that reference; without it they can access any job. Must be set when temporary keys are exposed to end users. Ignored for `rt` tokens. |
| `region` | No | String: `eu` (default), `usa`, or `au`. Set for `batch` temporary keys used outside Europe. A `batch` temporary key is valid only in this region, so it must match the Batch endpoint called. Not needed for `rt` keys, which work in every region and ignore it. |

Response:

```json
{
  "key_value": "eyJhbG..."
}
```

The key is always issued for the project that owns the API key used to authenticate.

`POST /v1/jwts` replaces the deprecated `POST /v1/api_keys` endpoint. Migrate any `/v1/api_keys` usage to `/v1/jwts`; `type`, `ttl`, `client_ref`, and `region` work the same way, and the response contains only `key_value`.

Docs versus spec: the authentication page documents temporary keys only through `POST /v1/jwts` with `type` `batch` or `rt`. The Management API spec (`spec/mp.yaml`) separately documents `POST /v1/api-keys` (hyphen), which also issues a temporary key when `ttl` (60-86400) is set, accepts `type` `batch`, `rt`, or `tts`, returns `apikey_id` and `key_value`, and marks `region` as deprecated with no effect. Use `/v1/jwts` for temporary keys as the authentication page directs; see `speechmatics:account-administration` for `/v1/api-keys`.

### Batch temporary keys

Use them so end users upload audio to Speechmatics directly. This can cut development effort, storage, and bandwidth cost.

- `client_ref` should be a string that uniquely identifies an end user. A key minted with a `client_ref` can create and retrieve only jobs associated with that `client_ref`.
- If the key is exposed to end users (for example in the browser), `client_ref` is mandatory. It stops one user viewing or deleting another user's jobs.
- A Batch temporary key is valid in one region only. Set `region` to the region of the Batch endpoint you call or the key is rejected. Omitted means `eu`.
- Keys minted with a `client_ref` cannot access the Batch usage endpoint (https://docs.speechmatics.com/api-ref/batch/get-usage-statistics) and receive `HTTP 403 - Forbidden`.

Create a key valid for 60 seconds, tied to the reference `USER123`:

```bash
curl -L -X POST "https://mp.speechmatics.com/v1/jwts?type=batch" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $API_KEY" \
     -d '{"ttl": 60, "client_ref": "USER123"}'
```

Use it in place of the API key:

```bash
curl -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/" \
  -H "Authorization: Bearer $TEMP_KEY"
```

### Realtime temporary keys

- Not tied to a region. The same key works with any Realtime endpoint, including `global.rt.speechmatics.com`.
- Valid for starting any number of Realtime sessions until it expires.
- In the browser, pass the key as the `jwt` query parameter.

```bash
curl -L -X POST "https://mp.speechmatics.com/v1/jwts?type=rt" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $API_KEY" \
     -d '{"ttl": 60 }'
```

### Agent STT temporary keys

- There is no separate agent STT key type. Request `type=rt` (same request as above) and use the key on the `/v2/agent` path.
- Not tied to a region. Works with any agent STT endpoint, including `global.rt.speechmatics.com`.
- In the browser, pass the key as the `jwt` query parameter.

### Recommended browser pattern

1. The browser asks your backend for a key.
2. The backend calls `POST /v1/jwts` with the long-lived API key and a short `ttl` (and `client_ref` plus `region` for Batch).
3. The backend returns `key_value` to the browser.
4. The browser opens `wss://<rt-host>/v2?jwt=<key_value>` (or `/v2/agent?jwt=...`), or sends Batch requests with `Authorization: Bearer <key_value>`.

## WebSocket handshake responses

Applies to both the Realtime (`/v2`) and agent STT (`/v2/agent`) handshakes.

| Status | Meaning |
|---|---|
| 101 | Switching Protocols. Connected: send `StartRecognition` to begin. |
| 400 | Bad Request. The handshake request is malformed. |
| 401 | Unauthorized. The API key or temporary key is not valid. |
| 405 | Method Not Allowed. The request method is not `GET`. |

A successful Realtime handshake request:

```http
GET /v2/ HTTP/1.1
Host: global.rt.speechmatics.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: ujRTbIaQsXO/0uCbjjkSZQ==
Sec-WebSocket-Version: 13
Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
Authorization: Bearer YOUR_API_KEY
User-Agent: Python/3.8 websockets/8.1
```

And its response:

```http
HTTP/1.1 101 Switching Protocols
Connection: upgrade
Upgrade: WebSocket
Sec-WebSocket-Accept: 87kiC/LI5WgXG52nSylnfXdz260=
```

## WebSocket close codes

An `Error` message can be followed by a WebSocket close frame. Same table for Realtime and agent STT.

| Close code | Reason |
|---|---|
| 1003 | `protocol_error` |
| 1008 | `policy_violation` |
| 1011 | `internal_error` |
| 4001 | `not_authorised` |
| 4003 | `not_allowed` |
| 4004 | `invalid_model` |
| 4005 | `quota_exceeded` |
| 4006 | `timelimit_exceeded` |
| 4013 | `job_error` |

For `4005`, `4013`, and `1011` only, retry after at least 5-10 seconds.

Realtime sessions also close when they idle or run too long. For those limits see `speechmatics:realtime-transcription`. For the full message protocol see `speechmatics:realtime-transcription` and `speechmatics:agent-stt`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `401` on every request | Missing or invalid `Authorization: Bearer` header; revoked key; expired temporary key |
| Batch temporary key rejected outside Europe | `region` omitted or not matching the endpoint (`eu`, `usa`, `au`) |
| `403` on the Batch usage endpoint | Temporary key was created with a `client_ref` |
| Cannot retrieve a job | Request sent to a different regional endpoint than the one that created the job, or the key belongs to another project |
| Jobs missing in the portal | Created on EU2 or US2 |
| Browser WebSocket cannot set headers | Use `?jwt=<temporary key>` |
| Close code `4004` (`invalid_model`) | Check `model` against the models the endpoint supports. See [models.md](models.md) |

## Next step

Try the "Hello World" example in the Speechmatics Academy: https://github.com/speechmatics/speechmatics-academy/tree/main/basics/01-hello-world
