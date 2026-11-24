# CPU realtime transcriber container

Docs: https://docs.speechmatics.com/deployments/container/cpu-speech-to-text#realtime-transcription

The realtime container transcribes a live stream or recorded file in a predefined language over a WebSocket. Multiple instances can run on one Docker host, for one or several languages. All data is transitory; nothing is persisted.

## Contents

- Starting the container
- Multi-session containers
- Prewarming
- Input and output
- Speech duration log
- Read-only mode
- Non-root user
- Health service

## Starting the container

```bash
docker run \
    -p 9000:9000 \
    -p 8001:8001 \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    rt-asr-transcriber-en:17.1.0
```

- Port 9000: WebSocket. Clients connect to `ws://<host>:9000/v2`.
- Port 8001: health service.

System requirements match the batch container: 1 vCPU, 2-5GB RAM, AVX-capable CPU. See [cpu-batch.md](cpu-batch.md). Session resource use is in [performance-and-cost.md](performance-and-cost.md).

To build an application against the container, use a Speechmatics SDK and set its URL to the container address. See `speechmatics:realtime-transcription`.

## Multi-session containers

By default the container accepts one WebSocket connection at a time. Set `SM_MAX_CONCURRENT_CONNECTIONS` to the maximum number of sessions. The `/ready` endpoint then returns true while a connection is free.

CPU usage scales with active sessions. Most memory is shared between connections, and more is shared when the transcriber is linked to a GPU inference server.

## Prewarming

Reduce first-session loading time to several hundred milliseconds by prewarming engines with `SM_PREWARM_ENGINE_MODES`, a semicolon-separated list:

```
SM_PREWARM_ENGINE_MODES='en_general_gpu_standard:1;en_general_gpu_enhanced:2'
```

Format: `{language}_{domain}_{processor}_{model}:{prewarm_connections}`

| Part | Values |
|---|---|
| `language` | A supported language code |
| `domain` | `general`, or a domain used for some multilingual packs, for example `SM_PREWARM_ENGINE_MODES='es_bilingual-en_gpu_standard:1'` |
| `processor` | `cpu` or `gpu`. `gpu` requires a GPU inference server |
| `model` | `standard` or `enhanced` |
| `prewarm_connections` | Integer. Number of engine instances of that mode to prewarm |

The total of `prewarm_connections` cannot exceed `SM_MAX_CONCURRENT_CONNECTIONS`. After prewarming completes, the setting does not limit which connection types the engine can start.

## Input and output

Pass audio over a WebSocket: send a `StartRecognition` message with the configuration, then binary audio chunks. Transcripts return in `AddTranscript` messages. Each carries result segments for audio delimited by pauses and other latency measurements.

Results are sorted by increasing `start_time`, then by decreasing `end_time`:

```json
{
    "message": "AddTranscript",
    "format": "2.9",
    "metadata": {
      "transcript": "full tell radar",
      "start_time": 0.11,
      "end_time": 1.07
    },
    "results": [
      {
        "type": "word",
        "start_time": 0.11,
        "end_time": 0.4,
        "alternatives": [{ "content": "full", "confidence": 0.7 }]
      },
      {
        "type": "word",
        "start_time": 0.41,
        "end_time": 0.62,
        "alternatives": [{ "content": "tell", "confidence": 0.6 }]
      },
      {
        "type": "word",
        "start_time": 0.65,
        "end_time": 1.07,
        "alternatives": [{ "content": "radar", "confidence": 1.0 }]
      }
    ]
}
```

Ensure the config JSON in `StartRecognition` is correctly formatted; malformed JSON is the common realtime problem the docs call out. Message reference: `speechmatics:realtime-transcription`.

## Speech duration log

After every session the container logs the duration of speech transcribed, excluding silence and background noise. Use it for your own records or usage reporting.

```
2020-04-13 22:48:05.312 INFO sentryserver Transcribed 52 seconds of speech
```

Regular expression to extract the seconds:

```
^.+ .+ INFO sentryserver Transcribed (\d+) seconds of speech$
```

## Read-only mode

```bash
docker run -it --read-only \
    -p 9000:9000 \
    --tmpfs /tmp \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    rt-asr-transcriber-en:17.1.0
```

The container still needs a writable temporary directory. `--tmpfs /tmp` provides one held in host memory and removed when the container stops.

With the shared custom dictionary cache, also mount the cache location:

```bash
docker run -it --read-only \
    -p 9000:9000 \
    --tmpfs /tmp \
    -v /cachelocation:/cache \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    -e SM_CUSTOM_DICTIONARY_CACHE_TYPE=shared \
    rt-asr-transcriber-en:17.1.0
```

Cache details: [cpu-batch.md](cpu-batch.md#shared-custom-dictionary-cache).

## Non-root user

The realtime container can run as a non-root user with no loss of functionality. Pass `--user $USERNUMBER:$GROUPID`, both numeric values from 1 to 65535:

```bash
docker run -it --user 100:100 \
    -p 9000:9000 \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    rt-asr-transcriber-en:17.1.0
```

## Health service

An HTTP health service runs by default on port 8001 as a subprocess of the container entrypoint. Query each endpoint with HTTP GET. Use these as Kubernetes startup, liveness and readiness probes.

| Endpoint | Probe | 200 when | Otherwise | Body |
|---|---|---|---|---|
| `/started` | Startup | All services in the container have started. Never reverts once successful | 503 | `{"started": true}` |
| `/live` | Liveness | All services have started and sent an update to the health service recently. A service silent for more than 10 seconds is marked dead | 503 | `{"alive": true}` |
| `/ready` | Readiness | The container has a free connection slot | 503 | `{"ready": true}` |
| `/session_status` | Session listing (from 13.0.0) | Sessions listed successfully | 503 | See below |

```
$ curl -i address.of.container:8001/started
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.8.5
Date: Mon, 08 Feb 2021 12:46:21 GMT
Content-Type: application/json
{
    "started": true
}
```

```
$ curl -i address.of.container:8001/live
HTTP/1.0 200 OK
Content-Type: application/json
{
    "alive": true
}
```

```
$ curl -i address.of.container:8001/ready
HTTP/1.0 200 OK
Content-Type: application/json
{
    "ready": true
}
```

`/ready` is accurate to a 2 second resolution. If used for load balancing, a burst of traffic within that window can all be allocated to one container because its readiness state has not yet changed.

### `/session_status`

Lists sessions served by the container, which can be tied to log entries and client connections.

- `session_id` is created by the transcriber, returned to the client on first connection, and always present.
- `request_id` is only populated if the `x-request-id` header was set in the initial WebSocket handshake. This supports deployments where a proxy or load balancer adds an ID to each connection.

```
$ curl -i address.of.container:8001/session_status
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.10.13
Date: Wed, 05 Mar 2025 11:41:51 GMT
Content-Type: application/json
{
  "max_sessions": 4,
  "active_sessions": [
    {"session_id": "499e3f17-b9e4-4c72-b9aa-66cbbdafea53", "request_id": "499e3f17-b9e4-4c72-b9aa-66cbbdafea53"},
    {"session_id": "fffc5412-d4b5-4e72-a912-663107349968", "request_id": "802da03c-77f5-4b9a-b0df-441734a3b2b0"},
  ]
}
```

## Verbose logging

```bash
docker run -e DEBUG=true rt-asr-transcriber-en:17.1.0
```

Startup logs and license errors: [troubleshooting.md](troubleshooting.md).
