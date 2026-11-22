# Monitoring and logs

Docs:

- https://docs.speechmatics.com/deployments/virtual-appliance/administration/monitoring
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/logcli-help
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/services#access-logs

## Contents

- [Resource endpoints](#resource-endpoints)
- [Prometheus](#prometheus)
- [Useful Prometheus queries](#useful-prometheus-queries)
- [Download logs as a ZIP](#download-logs-as-a-zip)
- [Loki and logcli](#loki-and-logcli)
- [Logs for a specific job](#logs-for-a-specific-job)
- [Useful Loki queries](#useful-loki-queries)
- [logcli manual](#logcli-manual)

## Resource endpoints

Exhausting any resource slows transcription. Monitor at system level:

| Resource ID | Endpoint | Description |
| --- | --- | --- |
| `cpu` | `/v2/management/cpuinfo` | CPU usage across all assigned vCPUs |
| `mem` | `/v2/management/meminfo` | Total RAM usage of the appliance |

```bash
curl -sSL -u admin:admin -X 'GET' \
    "http://${APPLIANCE_HOST}/v2/management/meminfo" \
    | jq
```

```json
{
  "available_kb": 23412128,
  "total_kb": 32862660,
  "usage_percentage": 14.907302,
  "used_kb": 4898936
}
```

The `cpuinfo` response (with `usage_percentage`, `cpus`, and `flags`) is shown in [installation.md](installation.md#host-cpu-info).

## Prometheus

Prometheus is available on port 9001. Credentials are the same as for the Management API: `admin:admin` unless changed.

- Browser UI: `https://${APPLIANCE_HOST}:9001/graph`
- Endpoint for clients such as Grafana: `https://${APPLIANCE_HOST}:9001/`

Query syntax: [Prometheus querying basics](https://prometheus.io/docs/prometheus/latest/querying/basics/).

## Useful Prometheus queries

Disk space left on the transcription jobs partition. Other useful mount points are `/` for the root partition and `/opt/speechmatics/monitoring` for the logs partition:

```
node_filesystem_free_bytes{mountpoint=~"/opt/speechmatics/jobs"}
```

Memory used by individual container images. Autocomplete offers container names:

```
container_memory_rss{image=~"docker-master.artifacts.speechmatics.io/k8s/batch-jobs-api-v2.*"}
```

Memory used by the host in total:

```
node_memory_MemFree_bytes
```

Amount of successfully POSTed data over HTTPS:

```
traefik_entrypoint_requests_bytes_total{code="201", method="POST", entrypoint="websecure"}
```

## Download logs as a ZIP

```bash
curl -sSL -u admin:admin -X 'GET' \
    "http://${APPLIANCE_HOST}/v2/management/logs/zip?limit=1h" \
    -o ./speechmatics.zip
```

Or with an explicit accept header:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/logs/zip?limit=1h" \
  -H 'accept: application/zip'
```

`limit` query parameter:

- The maximum age of logs, as a duration: `8h5m3s`, `8h`, `3h30m`, `300s`.
- The default unit is seconds if none is given.
- If omitted, the last hour of logs is returned.
- It applies to log contents as well as to which logs are returned. Logs that started before the cut-off are truncated, and only the tail is returned.

ZIP contents:

- Logs for all currently running Kubernetes deployments.
- A directory named `extra` with logs collected by the Grafana Loki subsystem, including transcription job logs and logs for completed Kubernetes pods.

Too large a time interval may time out the request. In that case log on to the appliance and use `kubectl` directly, or use `logcli`.

The same download is available in a browser at `http://${APPLIANCE_HOST}/docs/#/Management/ZipLogs`. Click the download link when the ZIP is ready.

## Loki and logcli

`logcli` is the command-line client for Loki log aggregation. Install it from the [Loki documentation](https://grafana.com/docs/loki/latest/query/logcli/getting-started/).

Connection settings:

- Loki endpoint: port 3100.
- Org ID: `fake`, the Loki standard for a single-tenant installation.
- Credentials: `admin:admin` unless changed.

Query logs for a particular Kubernetes deployment:

```bash
export LOKI_ADDR=https://${APPLIANCE_HOST}:3100/
./logcli \
  -o raw \
  --username admin \
  --password admin \
  --tls-skip-verify \
  --org-id=fake query '{instance=~".+:k8sbuffer"}'
```

Use `-o raw` because logs are already in JSON format.

Query limits: results are limited to 1000 entries by default. The `series` and `labels` commands return results within the default period of 1 hour. Extend the period with `--from`.

## Logs for a specific job

For job ID `1o9islfv29`, first find its series:

```bash
export LOKI_ADDR=https://${APPLIANCE_HOST}:3100/
./logcli \
  -o jsonl \
  --username admin \
  --password admin \
  --tls-skip-verify \
  --org-id=fake series \
  --from="2023-12-13T10:00:00Z" '{}' | grep 1o9islfv29

{instance="default/job-1o9islfv29-h8cw7:blobuploader", job="loki.source.kubernetes.pods"}
{instance="default/job-1o9islfv29-h8cw7:transcriber", job="loki.source.kubernetes.pods"}
{instance="default/job-1o9islfv29-h8cw7:preprocessor", job="loki.source.kubernetes.pods"}
```

A transcription job is a Kubernetes job whose pod has three containers, so three series are listed. Request one, or all three with a wildcard: `'{instance=~"default/job-1o9islfv29-h8cw7:.*"}'`. A wildcard merges the logs.

```bash
export LOKI_ADDR=https://${APPLIANCE_HOST}:3100/
./logcli \
  -o raw \
  --username admin \
  --password admin \
  --tls-skip-verify \
  --org-id=fake query --from="2023-12-13T10:00:00Z" '{instance="default/job-1o9islfv29-h8cw7:transcriber"}'

{"jobid": "1o9islfv29", "Request-ID": "477c5bc3ad4027d973b59f2f9ec4276e", "msg": "Shutdown complete", "level": "INFO", "time": "2024-01-05T11:33:19.733285"}
{"msg": "Eats client process finished", "level": "INFO", "time": "2024-01-05T11:33:19.717805"}
{"msg": "Transcribed 4 seconds of speech", "level": "INFO", "time": "2024-01-05T11:33:19.503377"}
{"jobid": "1o9islfv29", "Request-ID": "477c5bc3ad4027d973b59f2f9ec4276e", "msg": "RTF: 3.291123", "level": "INFO", "time": "2024-01-05T11:33:19.502920"}
...
```

Which container log to read:

| Container | Read when |
| --- | --- |
| `transcriber` | Usually the most useful. Also available through the jobs API |
| `blobuploader` | HTTP notifications are not being sent. It is the final stage of the transcription process |
| `preprocessor` | Problems with audio format, or with pulling audio from a remote source |

## Useful Loki queries

### Batch: job RTF (real time factor)

Job processing time relative to audio length. Use it to measure and tune throughput.

```
'{job="loki.source.kubernetes.pods", instance!="monitoring/loki-0:loki"} |= `COMPLETED_JOB` | unpack | __error__=``'
```

Returns JSON log lines containing the field `rtf`, one line per completed job.

### Realtime: final lag and partial lag

Lag between audio sent and audio transcribed (final), or between audio sent and partial transcripts (partial). Use it to measure and tune throughput, including `max_streams`.

```
'{job="loki.source.kubernetes.pods", instance=~"default/sm-proxy-a.*"} |= `connection usage stats` | unpack'
```

Returns JSON log lines, one for each minute of usage of a given session. The field `g.final_lag` holds the final lag and `g.partial_lag` holds the partial lag.

## logcli manual

```
usage: logcli [<flags>] <command> [<args>; ...]

A command-line for loki.
```

### Flags

```
      --help                  Show context-sensitive help (also try --help-long and --help-man).
      --version               Show application version.
  -q, --quiet                 Suppress query metadata
      --stats                 Show query statistics
  -o, --output=default        Specify output mode [default, raw, jsonl]. raw suppresses log labels and timestamp.
  -z, --timezone=Local        Specify the timezone to use when formatting output timestamps [Local, UTC]
      --cpuprofile=""         Specify the location for writing a CPU profile.
      --memprofile=""         Specify the location for writing a memory profile.
      --stdin                 Take input logs from stdin
      --addr="http://localhost:3100"
                              Server address. Can also be set using LOKI_ADDR env var.
      --username=""           Username for HTTP basic auth. Can also be set using LOKI_USERNAME env var.
      --password=""           Password for HTTP basic auth. Can also be set using LOKI_PASSWORD env var.
      --ca-cert=""            Path to the server Certificate Authority. Can also be set using LOKI_CA_CERT_PATH env var.
      --tls-skip-verify       Server certificate TLS skip verify. Can also be set using LOKI_TLS_SKIP_VERIFY env var.
      --cert=""               Path to the client certificate. Can also be set using LOKI_CLIENT_CERT_PATH env var.
      --key=""                Path to the client certificate key. Can also be set using LOKI_CLIENT_KEY_PATH env var.
      --org-id=""             adds X-Scope-OrgID to API requests for representing tenant ID. Useful for requesting tenant data when bypassing
                              an auth gateway. Can also be set using LOKI_ORG_ID env var.
      --query-tags=""         adds X-Query-Tags http header to API requests. This header value will be part of `metrics.go` statistics.
                              Useful for tracking the query. Can also be set using LOKI_QUERY_TAGS env var.
      --bearer-token=""       adds the Authorization header to API requests for authentication purposes. Can also be set using
                              LOKI_BEARER_TOKEN env var.
      --bearer-token-file=""  adds the Authorization header to API requests for authentication purposes. Can also be set using
                              LOKI_BEARER_TOKEN_FILE env var.
      --retries=0             How many times to retry each query when getting an error response from Loki. Can also be set using
                              LOKI_CLIENT_RETRIES env var.
      --min-backoff=0         Minimum backoff time between retries. Can also be set using LOKI_CLIENT_MIN_BACKOFF env var.
      --max-backoff=0         Maximum backoff time between retries. Can also be set using LOKI_CLIENT_MAX_BACKOFF env var.
      --auth-header="Authorization"
                              The authorization header used. Can also be set using LOKI_AUTH_HEADER env var.
      --proxy-url=""          The http or https proxy to use when making requests. Can also be set using LOKI_HTTP_PROXY_URL env var.
```

### Commands

| Command | Purpose |
| --- | --- |
| `help [<command>...]` | Show help |
| `query [<flags>] <query>` | Run a LogQL query |
| `instant-query [<flags>] <query>` | Run an instant LogQL query |
| `labels [<flags>] [<label>]` | Find values for a given label |
| `series [<flags>] <matcher>` | Run a series query |
| `fmt` | Format a LogQL query |
| `stats [<flags>] <query>` | Run a stats query |
| `volume [<flags>] <query>` | Run a volume query |
| `volume_range [<flags>] <query>` | Run a volume query and return timeseries data |

Time range rules shared by `query`, `stats`, `volume` and `volume_range`:

- The default range is the last hour. Change it with `--since`, or give `--from` and `--to`.
- With `--from` and `--to`, use RFC3339Nano time format without a timezone at the end. The local timezone is added automatically, or set it with `--timezone`.

### query

Output modes, chosen with `-o`:

```
      raw: log line
      default: log timestamp + log labels + log line
      jsonl: JSON response from Loki API of log line
```

- `query` prints extra information about the query and results: the API URL, the set of common labels, and the set of excluded labels. Suppress it with `--quiet`.
- Output is limited to 30 entries by default. Raise it with `--limit`. (The appliance docs state results are limited to 1000 entries by default.)
- `query` supports metrics queries, but its output holds multiple data points between the start and end time, as used to build graphs. For only the most recent data point, use `instant-query`.

```bash
logcli query
    --timezone=UTC
    --from="2021-01-19T10:00:00Z"
    --to="2021-01-19T20:00:00Z"
    --output=jsonl
    'my-query'
```

#### Parallelization

Download an unlimited number of logs in parallel with these flags:

```
--parallel-duration
--parallel-max-workers
--part-path-prefix
--overwrite-completed-parts
--merge-parts
--keep-parts
```

```bash
logcli query
    --timezone=UTC
    --from="2021-01-19T10:00:00Z"
    --to="2021-01-19T20:00:00Z"
    --output=jsonl
    --parallel-duration="15m"
    --parallel-max-workers="4"
    --part-path-prefix="/tmp/my_query"
    --merge-parts
    'my-query'
```

- This creates a queue of jobs, each 15 minutes long: forty jobs for the 10-hour range. `--limit` is ignored.
- Four workers each take jobs from the queue until all are complete.
- Each job saves a part file at the `--part-path-prefix` location. Use different prefixes to run multiple queries at once. The file name holds the start and end timestamps of the part.
- While downloading, the file name ends in `.part.tmp`. A completed part ends in `.part`. A completed part is not downloaded again unless you pass `--overwrite-completed-parts`.
- Without `--forward`, parts download in reverse.
- Without `--merge-parts`, logcli downloads the part files and exits. With it, parts are read in order and printed as soon as the next part is complete, then removed. `--keep-parts` keeps them.

Part files mid-download, with `--keep-parts`:

```bash
ls -1 /tmp/my_query*
/tmp/my_query_20210119T183000_20210119T184500.part.tmp
/tmp/my_query_20210119T184500_20210119T190000.part.tmp
/tmp/my_query_20210119T190000_20210119T191500.part.tmp
/tmp/my_query_20210119T191500_20210119T193000.part.tmp
/tmp/my_query_20210119T193000_20210119T194500.part
/tmp/my_query_20210119T194500_20210119T200000.part
```

### instant-query

Evaluates a metric query at a single point in time, equivalent to the Grafana Explore table view. For a metrics query that builds a graph, use `query`. It does not produce useful output for log lines: always use `query` for log queries. LogQL documentation: https://grafana.com/docs/loki/latest/logql/

### labels

Finds values for a given label.

### series

Takes a label matcher and returns all log streams found in the time window.

- Send an empty matcher `'{}'` to return all streams.
- `--analyze-labels` summarizes the labels found in all streams, which helps find high cardinality labels.

### fmt

Formats a LogQL query.

### stats

Returns index statistics on how much data the matching streams contain. Works only against Loki instances using the TSDB index format.

```bash
logcli stats
    --timezone=UTC
    --from="2021-01-19T10:00:00Z"
    --to="2021-01-19T20:00:00Z"
    'my-query'
```

### volume

Takes label selectors and returns aggregate volumes for matching series. Works only against Loki instances using the TSDB index format.

```bash
logcli volume
    --timezone=UTC
    --from="2021-01-19T10:00:00Z"
    --to="2021-01-19T20:00:00Z"
    'my-query'
```

### volume_range

Like `volume`, but returns timeseries data aggregated into buckets by the step value. Works only against Loki instances using the TSDB index format.

```bash
logcli volume_range
    --timezone=UTC
    --from="2021-01-19T10:00:00Z"
    --to="2021-01-19T20:00:00Z"
    --step=1h
    'my-query'
```
