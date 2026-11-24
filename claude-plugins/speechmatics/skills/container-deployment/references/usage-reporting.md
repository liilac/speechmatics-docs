# Usage reporting

Docs:

- Overview: https://docs.speechmatics.com/deployments/usage-reporting
- Automatic: https://docs.speechmatics.com/deployments/usage-reporting/automatic
- Offline: https://docs.speechmatics.com/deployments/usage-reporting/offline

On-prem deployments must report usage for billing. Two modes exist: automatic (online) and offline.

## Contents

- How the mode is configured
- What is recorded
- Automatic reporting
- Offline reporting: cadence and sending data
- Usage container
- Exporting usage data
- Virtual appliance

## How the mode is configured

Two transcriber settings control both modes.

| Variable | Default | Effect |
|---|---|---|
| `SM_EATS_URL` | none | Destination for usage events |
| `SM_ENABLE_USAGE_REPORTING` | `true` | `true`: send the subset of events needed for billing. `false`: send the full activity event stream. `false`, `no` and `0` are equivalent |

| `SM_EATS_URL` | `SM_ENABLE_USAGE_REPORTING` | Result |
|---|---|---|
| unset | `true` (default) | Automatic reporting to `usage.speechmatics.com` |
| unset | `false` | No destination; reporting is disabled entirely |
| set to your usage container | `true` (default) | Offline reporting: the same billing events go to your usage container |
| set | `false` | The full activity event stream, not only the billing subset, goes to that destination |

## What is recorded

Customer audio is never sent over the network. Only metadata about what the transcriber is doing is recorded. No audio files or transcripts are included.

Recorded:

- Audio duration, to calculate billing
- Customer information: contract ID, customer name, license ID
- A summary of the job configuration, excluding potentially sensitive information such as custom dictionary content
- Audio information such as codec and format type
- System information, including certain error events

Events are small JSON objects:

```json
{
  "container_id": "aee112010359",
  "contract_id": "0",
  "customer_id": "Speechmatics",
  "engine_instance_id": "930ab901-c408-457d-9f6d-dee21ecaac7f",
  "event": "TRANSCRIBER_DONE",
  "event_specific_data": {
    "bit_rate": "512000",
    "build_id": "",
    "channels": 2,
    "codec_name": "pcm_s16le",
    "file_metadata": {},
    "format_name": "wav",
    "inference": "cpu",
    "job_config": {
      "transcription_config": {
        "language": "en"
      },
      "type": "transcription"
    },
    "license_id": "b6616911c59c40cbbb32ebf442696a14",
    "rtf": 1.975401759147644,
    "sample_rate": "16000",
    "total_received_bytes": 149562,
    "total_received_duration": 2,
    "total_speech_duration": 2
  },
  "session_id": "a29bd398-5745-43ca-9d16-07cdc6eabdd0",
  "source": "uniasr-batch",
  "time_stamp": "2022-09-14T13:01:13.239Z"
}
```

## Automatic reporting

The transcriber sends usage data to Speechmatics at `usage.speechmatics.com` (HTTPS, port 443, path `/v1/log`).

- Batch transcriber: one `TRANSCRIBER_DONE` event at the end of transcription.
- Realtime transcriber: one `SESSION_ENDED` event at the end of each session, plus `SESSION_STATUS` every few minutes during a session.
- Payloads are several KB.

Version requirements:

- Batch container 10.1.0 onwards
- Realtime container 10.1.0 onwards
- On by default from 10.6.0. It is opt out.

Success shows in the transcriber logs at the end of the session. Verbose debug mode shows the report contents.

```
2024-04-15 13:17:38,799 INFO sentryserver Transcribed 36 seconds of speech
2024-04-15 13:17:38,974	INFO	prod.orchestrator.eats.api	Eats client process finished
```

Turn it off:

```bash
docker run -i -v ~/$AUDIO_FILE:/input.audio \
	-e LICENSE_TOKEN=eyJhbGciOiJ... \
	-e SM_ENABLE_USAGE_REPORTING=false \
	batch-asr-transcriber-en:17.1.0
```

### Network failure

The transcriber retries the usage server several times, for up to 3 seconds:

```
2024-04-15 13:21:15,556	WARNING	prod.orchestrator.eats.api	Exception from EATS API call [TRANSCRIBER_DONE] HTTPSConnectionPool(host='usage.speechmatics.com', port=443): Max retries exceeded with url: /v1/log (Caused by NameResolutionError("<urllib3.connection.HTTPSConnection object at 0x7ff57665e760>: Failed to resolve 'usage.speechmatics.com' ([Errno -3] Temporary failure in name resolution)"))
```

If it still cannot connect, it logs `WARNING` messages and stops trying. The transcriber exits normally with exit code 0.

- Batch: the transcriber exits immediately after.
- Realtime: usage reporting is disabled for a fixed period (currently 60 seconds). The retry slightly slows transcription, so during an outage consider setting `SM_ENABLE_USAGE_REPORTING=false`.

Inform the Speechmatics Finance Team of the duration and timing of any outage.

## Offline reporting

For deployments with no internet access. A usage container collects events locally. You export the data and email it to Speechmatics. No personal customer data, transcripts or media are captured.

You are responsible for assigning storage to the usage container and sending data at regular intervals.

### Cadence

Send all usage data by the last working day of each calendar month, for every usage container and batch appliance. Report more often with very large volumes:

- A usage container storing more than 10,000 batch jobs in a calendar month, or 1250 realtime jobs of more than an hour
- Many long jobs (over 60 minutes), especially a realtime container that persists between sessions

### Sending data

- Email exports to billing-reporting@speechmatics.com.
- Do not modify exported data. Speechmatics requests a new export if data was altered.
- Attachments must have the `.json.gz` extension. The file name does not matter.
- Keep files under 25MB, the default email limit for many providers.
- Multiple attachments per email, or multiple emails, are fine.
- A confirmation email arrives within 15 minutes if the reports are accepted. If `Reply-To` lists several addresses, only the first receives the reply.
- Data is retained in the usage container for 90 days, then purged.
- Overlapping reports with duplicate data are fine. Each transcription is billed once, in the billing cycle of its completion time.

## Usage container

Image: `speechmaticspublic.azurecr.io/asr-usage:0.5.3` (current at time of writing; check the docs). Use the same registry credentials as for the transcriber images, and cache the image in your own registry.

```bash
docker login https://speechmaticspublic.azurecr.io
docker pull speechmaticspublic.azurecr.io/asr-usage:0.5.3
```

The usage container is an early access product available to any customer using the batch or realtime containers. Send feedback and bugs to Support.

### Requirements

- 1 vCPU
- 1 GB memory
- At least 1 GB of persistent storage per usage container. Every 25 MB stores data for up to 13,000 batch jobs or up to 1250 60-minute realtime sessions
- Batch container 8.2.0 onwards; realtime container 1.4.1 onwards
- Tested with Docker version 20; earlier versions are untested
- All transcribers must be able to reach the usage container
- Communication between containers is over HTTPS

`tmpfs` storage is supported but not recommended. If you must use it, report more often to avoid data loss.

### Endpoints and ports

| Endpoint | Use | Port | How to set |
|---|---|---|---|
| `v1/log` | Receives event data from batch and realtime containers | 9090 | Point transcribers at it with `SM_EATS_URL` |
| `v1/export` | Extracts all or time-windowed event data as a compressed file | 8000 | Publish with `docker -p`. To change the port, set `PANDAS_PORT` and publish the matching port |

| Variable (usage container) | Default | Type | Description |
|---|---|---|---|
| `EATS_PORT` | `9090` | int | Listening port for incoming data from transcribers |

Docker exposes no ports by default. Open the ports needed to receive events and to export data.

### Run it

The container always needs a persistent volume mounted at `/data`. Start it before any transcriber so all usage is captured. It is persistent and does not shut down after receiving data.

```bash
# Create volume
docker volume create volume-1

# Mount volume
docker run -it  \
    -v volume-1:/data \
    -e EATS_PORT=9090  \
    -p 8000:8000 \
    speechmaticspublic.azurecr.io/asr-usage:0.5.3
```

Set up backup policies for the volume. The usage container cannot recover a corrupted data file or volume by itself.

The docs example publishes only port 8000. Transcribers must still be able to reach the ingest port (9090): the docs require you to open every port needed to send and extract data.

### Point transcribers at it

Set `SM_EATS_URL` to the usage container's address and listening port, for example `SM_EATS_URL=asr-usage.example.net:9090` or `SM_EATS_URL=10.244.8.32:9090`. Leave `SM_ENABLE_USAGE_REPORTING` at its default of `true`. Transcribers send to the usage container over HTTPS by default.

The docs versions of the two examples below use the image tags `batch-asr-transcriber-en:8.2.0` and `rt-asr-transcriber-en:1.4.0`, while the compatibility list says realtime container 1.4.1 onwards. The tags here are the current release.

Batch:

```bash
docker run -i -v $AUDIO_FILE:/input.audio \
  -v $CONFIG_FILE:/config.json:ro \
  -e LICENSE_TOKEN=$TOKEN_VALUE \
  -e SM_EATS_URL=asr-usage.example.net:9090 \
  batch-asr-transcriber-en:17.1.0
```

Realtime:

```bash
docker run -p 9000:9000 \
  -e LICENSE_TOKEN=$TOKEN_VALUE \
  -e SM_EATS_URL=asr-usage.example.net:9090 \
  rt-asr-transcriber-en:17.1.0
```

### When events are sent

- During transcription
- When transcription finishes. Batch: when the job finishes. Realtime: after the end of transcription message, the container sends `SESSION_ENDED`
- When the container is shut down or terminated, by the user or a system error (for example `SIGTERM`)

### Log messages

Transcriber, success:

```
2021-07-19 11:24:31.314 INFO sentryserver Transcription usage registered with EATS
```

Usage container, event received:

```
[2021-08-25T10:45:37Z INFO  actix_web::middleware::logger] 172.19.0.3:39068 "POST /v1/log HTTP/1.1" 201 0 "-" "Go-http-client/1.1" 0.009459
```

Usage container, export served:

```
[2021-09-03T14:54:00Z INFO  actix_web::middleware::logger] 172.19.0.1:55820 "GET /v1/export HTTP/1.1" 200 12912 "-" "curl/7.64.1" 0.006313
```

Transcriber, cannot reach the usage container:

```
2021-07-19 11:27:43.158 ERROR sentryserver Error 'Post "https://asr-usage.net:9090/v1/log": dial tcp 172.25.0.2:909: connect: connection refused' occurred when logging EATS data: retrying
```

On shutdown, batch and realtime containers retry for up to 1 minute after `SIGTERM`. Unsent data is then lost:

```
2021-07-19 11:28:55.288 WARNING sentryserver Some activity events could not be sent to EATS: count: 4
```

### Multiple usage containers

Run at least one usage container per environment where transcribers run. Add more for redundancy against network or storage failure. With transcribers in several availability zones or clusters, assign usage containers per environment or cluster.

This Docker Compose example runs two usage containers, a Traefik proxy that routes events between them with round robin balancing, and one batch transcriber that sends to the proxy:

```yaml
# Example docker-compose file using multiple telemetry Containers.
#
version: "3.4"

# Common setup for ASR Usage Containers
x-usage-template: &usage-template
  image: asr-usage:x.y.z
  labels:
    - "traefik.enable=true"
    - "traefik.tcp.routers.usage.rule=HostSNI(`*`)"
    - "traefik.tcp.routers.usage.entrypoints=custom"
    - "traefik.tcp.routers.usage.tls=true"
    - "traefik.tcp.routers.usage.tls.passthrough=true"
    - "traefik.tcp.routers.usage.service=telemeter"
    - "traefik.tcp.services.usage.loadbalancer.server.port=9090"
  depends_on:
    - proxy

services:
  # Traefik reverse proxy, to route telemetry events to multiple ASR Usage Container
  # containers
  proxy:
    image: traefik:v2.4
    command: --providers.docker --providers.docker.exposedByDefault=false --entrypoints.custom.address=:9090
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  usagecontainer1:
    <<: *usage-template
    ports:
      - "8001:8000"

  usagecontainer2:
    <<: *usage-template
    ports:
      - "8002:8000"

  transcriber-batch:
    image: batch-asr-transcriber-en:x.y.z
    environment:
      SM_EATS_URL: proxy:9090
    volumes:
      - ./input/10_sec_news.wav:/input.audio
      - ./input/license.json:/license.json
    depends_on:
      - proxy
      - usagecontainer1
      - usagecontainer2
```

Each usage container needs its own persistent volume. Export from every usage container; there are as many reports as usage containers.

## Exporting usage data

Use the usage container's REST API on port 8000:

```bash
# To export all data
curl 'asr-usage.net:8000/v1/export' > ExportExampleFile.json.gz

# To export data within a date window, e.g. 1-Jan-2020 to 1-Feb-2020
curl 'asr-usage.net:8000/v1/export?since=2020-01-01T00:00:00.000000Z&until=2020-02-01T00:00:00Z' > ExportExampleFile-01-01_2020-02-01.json.gz
```

| Query parameter | Description |
|---|---|
| `since` | Start of the window, ISO-8601 timestamp |
| `until` | End of the window, ISO-8601 timestamp |

- Output is compressed `json.gz`. Send it in that format.
- If the export is too large, a 4XX response may be returned. In testing this happened at around 25,000 batch jobs or 5,000 hour-long realtime jobs. Use a smaller window.
- To stay under 25MB per file, chunk by time: usually around 10,000 batch jobs or 1250 one-hour realtime sessions per file. (The storage requirement in the same docs page says 25 MB holds up to 13,000 batch jobs; the docs give both figures.)

Weekly export script for a month:

```bash
#!/bin/bash

# Use ISO-8601 format
START="2021-11-01T00:00:00Z"
END="2021-12-01T00:00:00Z"
CHUNK="7 day"

d=$(date -d "$START" -I)
while [ $(date -d "$d" +%s) -le $(date -d "$END" +"%s") ]; do
    SINCE=$(date -d "$d" +"%Y-%m-%dT%H:%M:%SZ")
    d=$(date -I -d "$d + $CHUNK")
    UNTIL=$(date -d "$d" +"%Y-%m-%dT%H:%M:%SZ")
    
    curl "asr-usage.net:8000/v1/export?since=${SINCE}&until=${UNTIL}" > exported_$(date -d "${SINCE}" -I)_$(date -d "${UNTIL}" -I).json.gz
done
```

Inspect an export with `jq` (do not send a modified file):

```
$ cat exported_2020-01-01_2020-02-01.json.gz | gunzip | jq .
{
  "header": {
    "alg": "HS512"
  },
  "payload": {
    "events": [
      {
        ...
```

## Virtual appliance

Usage reporting on the virtual appliance is on by default and opt out. Set the mode with the Management API. `mode` is `offline` or `online`:

```bash
curl -L -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/usagereporting" \
  -d '{"mode": "offline"}'
```

In `offline` mode a container inside the appliance collects usage. Recommended workflow:

1. Run one or more virtual appliances.
2. Before running any jobs, set the usage mode to `offline`.
3. At intervals of no more than a calendar month, export usage from each appliance.
4. Email the exports to billing-reporting@speechmatics.com.

Export a compressed archive:

```bash
curl -X 'GET' \
  "http://${APPLIANCE_HOST}/v1/export?since={start_time}&until={end_time}" \
  -H 'accept: application/gzip'
```

`start_time` and `end_time` are inclusive ISO-8601 timestamps (`YYYY-MM-DDTHH:MM:SSZ`). Data is retained in the appliance for 90 days.

In `realtime` mode, usage for contract ID `-77777777777777` is a prewarming job run at the transcriber's first startup. It is not billed.

For appliance administration, see `speechmatics:virtual-appliance`.
