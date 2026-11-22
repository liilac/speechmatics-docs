# Scaling, GPU, and languages

Docs:

- https://docs.speechmatics.com/deployments/virtual-appliance/administration/scaling
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/using-a-gpu
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/adding-languages
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/language-identification

## Contents

- [Batch scaling mode](#batch-scaling-mode)
- [Realtime sessions and readiness](#realtime-sessions-and-readiness)
- [Enable GPU inference](#enable-gpu-inference)
- [GPU configuration](#gpu-configuration)
- [Query the GPU](#query-the-gpu)
- [Add and remove languages](#add-and-remove-languages)
- [Language Identification](#language-identification)

## Batch scaling mode

`scaling_mode` sets how many threads a job worker gets:

| Value | Behavior |
| --- | --- |
| `simple` | Each transcription job runs in a single thread |
| `adaptive` | Thread count depends on audio length, up to a maximum of 4. Available only if the node has at least 4 cores |

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/host/scaling" \
  -d '{"scaling_mode": "simple"}'
```

Threads per job in `adaptive` mode:

| Audio length in seconds | Threads |
| --- | --- |
| 0 < s <= 300 | 1 |
| 300 < s <= 600 | 2 |
| 600 < s <= 900 | 3 |
| 900 < s <= max | 4 |

Workers reserve CPU and memory according to the scaling mode and the features a job requests (see the tables in [installation.md](installation.md#batch-appliance-requirements)). If enough resources are available at job creation, Kubernetes schedules the job. Otherwise the job is marked pending until resources are freed.

Adaptive jobs use multiple threads, so they put more load on the GPU inference server when it is enabled. `max_jobs` protects the inference server. See [GPU configuration](#gpu-configuration).

## Realtime sessions and readiness

Realtime mode supports multi-threaded workers by default. The worker processes a configurable number of streams (threads) at once, set by `max_streams`. When the maximum is exceeded, the appliance rejects new sessions.

List active sessions:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/realtime/sessions"
```

```json
{
  "request_ids": ["session_1_id", "session_2_id"]
}
```

`request_ids` is a list of strings: the request IDs of active sessions.

Check readiness before starting a new session:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/realtime/ready"
```

```json
{
  "ready": true
}
```

`ready` is `true` if the service has capacity for a new session, and `false` if `max_streams` has been reached.

## Enable GPU inference

GPU mode is disabled by default. The host must be able to pass a GPU through to the VM. VMware Workstation cannot.

Hardware requirements match the GPU inference container: see `speechmatics:container-deployment` and https://docs.speechmatics.com/deployments/container/gpu-speech-to-text#system-requirements. Because the OVA is self-contained, consider only GPU memory, the driver version on the host, and the CUDA capability level.

### Batch mode

Enable:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/host/gpu" \
  -H 'Content-Type: application/json' \
  -d '{"gpu_enabled": true}'
```

Query:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/gpu"
```

```json
{
  "gpu_enabled": true,
  "languages": [
    "en"
  ],
  "primary_operating_point": "standard",
  "max_jobs": 48
}
```

| Field | Meaning |
| --- | --- |
| `gpu_enabled` | `true` or `false`: GPU inference enabled |
| `languages` | Languages available for GPU inference |
| `primary_operating_point` | Primary operating point assumed when controlling GPU load |
| `max_jobs` | Maximum number of jobs of the chosen `primary_operating_point` allowed to run concurrently, before `adaptive` scaling is applied |

### Realtime mode

Enable:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/host/realtime/gpu" \
  -H 'Content-Type: application/json' \
  -d '{"gpu_enabled": true}'
```

Query:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/realtime/gpu"
```

```json
{
  "gpu_enabled": false,
  "max_streams": 9
}
```

| Field | Meaning |
| --- | --- |
| `gpu_enabled` | `true` or `false`: GPU inference enabled |
| `max_streams` | Maximum number of concurrent streams for Realtime inference |

Realtime mode has no concept of GPU-only languages. All installed languages run on GPU when it is enabled, so no language list is returned. Get installed languages from `/v2/management/host/about`.

## GPU configuration

### Batch mode

Get:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/gpu/config"
```

```json
{
  "primary_operating_point": "enhanced",
  "max_jobs": 12
}
```

Update:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/host/gpu/config" \
  -H 'Content-Type: application/json' \
  -d '{
  "primary_operating_point": "standard",
  "max_jobs": 1
}'
```

- `primary_operating_point`: the operating point used for the majority of your jobs, `standard` or `enhanced`. Operating points apply different load, so setting it ahead of time lets the appliance schedule jobs efficiently. It does not stop you running other operating points. One enhanced job is roughly equivalent to six standard jobs.
- `max_jobs`: maximum number of jobs of the chosen `primary_operating_point` allowed to run concurrently, before `adaptive` scaling is applied.

Suggested `max_jobs`, a balance of throughput, cost and stability from benchmarking. Tune for your audio:

| Primary operating point | `max_jobs` |
| --- | --- |
| Standard | 48 |
| Enhanced | 28 |

In `adaptive` scaling mode, one job may be split into 4 or more `simple` (single thread) jobs depending on file length. `max_jobs` counts these `simple` jobs. With `max_jobs` set to 12, you could run up to:

- 3 adaptive jobs with file lengths over 15 minutes, or
- 12 simple jobs, or
- 2 adaptive jobs with file lengths over 15 minutes and 4 simple jobs.

### Realtime mode

The appliance limits the total number of concurrent Realtime streams to protect running sessions from poor performance and crashes. There is no setting to limit sessions by operating point. Do not mix operating points.

Get:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/host/realtime/gpu/config"
```

```json
{
  "max_streams": 9
}
```

Update:

```bash
curl -X 'POST' \
  "https://${APPLIANCE_HOST}/v2/management/host/realtime/gpu/config" \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "max_streams": 30
}'
```

Add `-u admin:<password>` when Management API authentication is enabled.

`max_streams` is the maximum number of concurrent Realtime connections of either operating point.

Recommended starting point:

| Operating point | `max_streams` |
| --- | --- |
| Standard | 64 |
| Enhanced | 16 |

These values come from an 8-core 32GB machine with a T4 GPU running English transcription with a single operating point and transcription config. To tune, raise `max_streams` until the Final Lag becomes unacceptable. See the Loki queries in [monitoring-and-logs.md](monitoring-and-logs.md#useful-loki-queries).

## Query the GPU

Log on to the appliance and run `nvidia-smi` for detailed queries. Basic information is available from the Management API:

```bash
curl -L -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/nodeinfo"
```

The response is the set of labels on the Kubernetes node. If a GPU was detected, labels prefixed `nvidia.com` are present. Excerpt:

```json
{
  "author": "Speechmatics",
  "feature.node.kubernetes.io/cpu-cpuid.AVX": "true",
  "feature.node.kubernetes.io/cpu-cpuid.AVX2": "true",
  "feature.node.kubernetes.io/kernel-version.full": "5.15.0-76-generic",
  "feature.node.kubernetes.io/system-os_release.ID": "ubuntu",
  "feature.node.kubernetes.io/system-os_release.VERSION_ID": "22.04",
  "kubernetes.io/arch": "amd64",
  "kubernetes.io/hostname": "appliance",
  "node.kubernetes.io/instance-type": "k3s",
  "nvidia.com/cuda.driver.major": "525",
  "nvidia.com/cuda.driver.minor": "116",
  "nvidia.com/cuda.driver.rev": "04",
  "nvidia.com/cuda.runtime.major": "12",
  "nvidia.com/cuda.runtime.minor": "0",
  "nvidia.com/gpu.count": "1",
  "nvidia.com/gpu.family": "turing",
  "nvidia.com/gpu.machine": "VMware-Virtual-Platform",
  "nvidia.com/gpu.memory": "15360",
  "nvidia.com/gpu.present": "true",
  "nvidia.com/gpu.product": "Tesla-T4",
  "nvidia.com/gpu.replicas": "1",
  "nvidia.com/mig.capable": "false",
  "nvidia.com/mig.strategy": "single"
}
```

The full response also holds `feature.node.kubernetes.io/cpu-cpuid.*` labels for every CPU feature, `nvidia.com/gpu.deploy.*` labels, and node role labels.

On the appliance itself:

```bash
sudo lshw -C display
nvidia-smi
```

## Add and remove languages

- Supported in `batch` mode only. For extra Realtime languages, contact [Support](https://support.speechmatics.com).
- Installs additional CPU-only languages.
- Requires access to the Speechmatics container repository. As of 08 October 2025 the public containers moved from Artifactory to Azure Container Registry (ACR); contact Support to update your credentials.
- Requires superuser access.
- Language codes are the standard two-letter ISO codes used in transcription config, for example `de`, `fr`.
- You need the image version compatible with your appliance. Ask Support.

Log in over SSH as `smadmin` and run `configure_languages.sh`.

Appliance versions up to and including `6.2.1` pull from the Artifactory repository by default. On those versions, point at ACR:

```bash
export SM_DOCKER_PUBLIC=speechmaticspublic.azurecr.io
```

Set repository credentials in the environment, base64 encoded. If unset, the script prompts for the username and password:

```bash
export CRICTL_AUTH="$(echo -n <username>:<password> | base64)"
```

Add a language:

```bash
sudo CRICTL_AUTH="$(echo -n <username>:<password> | base64)" SM_DOCKER_PUBLIC=speechmaticspublic.azurecr.io BUILD_MODE=batch configure_languages.sh <version> <language-code> [<language-code> ...]
```

Remove a language:

```bash
sudo CRICTL_AUTH="$(echo -n <username>:<password> | base64)" SM_DOCKER_PUBLIC=speechmaticspublic.azurecr.io BUILD_MODE=batch configure_languages.sh -r <language-code> [<language-code> ...]
```

The new language is available once the script completes. Adding a transcription language also makes it available for `auto` Language Identification.

### Revert

If something went wrong after running the script, restore the system configuration:

```bash
sudo kubectl apply -f /root/.siab_deployment/k8s/bjapi.yaml
```

Show the currently configured languages, to assist Support:

```bash
kubectl get -o json deployment/api | \
jq -r '.spec.template.spec.containers[0].env[]|select(.name="SM_FEATURES_VALIDATION").value'
```

The printed configuration has a section under `batch->transcription->languages`:

```json
{
  "batch": {
    "transcription": [
      {
        "version": "latest",
        "languages": [
          "en"
        ]
      }
    ]
  }
}
```

## Language Identification

Disabled by default. Available in `Batch` mode only. `ALID` is the license feature code for language identification (see [licensing.md](licensing.md#license-feature-codes)).

Enable:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/host/langid" \
  -H 'Content-Type: application/json' \
  -d '{"max_thread_count": 1, "memory_per_thread": "3Gi"}'
```

| Field | Optional | Default | Meaning |
| --- | --- | --- | --- |
| `max_thread_count` | Not stated | Not stated | Maximum number of threads Language Identification uses. `0` disables it. Each task uses up to one thread, so set `2` to allow 2 parallel identification tasks |
| `memory_per_thread` | Yes | `3Gi` | Memory reserved for each configured thread. Increase it for large audio files |

Reserved memory is `max_thread_count` x `memory_per_thread`: 2 threads at `3Gi` reserve 6Gi.

For how to request Language Identification in a job, see `speechmatics:batch-transcription` and https://docs.speechmatics.com/speech-to-text/batch/language-identification.
