---
name: virtual-appliance
description: Installs and administers the Speechmatics virtual appliance, the pre-configured on-prem VM (OVA) that runs Batch or Realtime Speech to Text. Covers system requirements, OVA import on VMware ESXi, VMware Workstation, AWS EC2 and Proxmox VE, static IP and netplan, licensing and license feature codes, health checks and smoke tests, and the Management API. Use when the user mentions the virtual appliance, an OVA, `APPLIANCE_HOST`, `/v2/management/...` or `/v2/security/...` endpoints, `smadmin`, `configure_languages.sh`, `scaling_mode`, `max_jobs`, `max_streams`, `gpu_enabled`, `jobtoken`, `sslcertificate`, `insecureports`, `cleanupinterval`, appliance ports 9000/9004/9001/3100, Prometheus or Loki `logcli` on the appliance, or appliance troubleshooting.
---

# Speechmatics virtual appliance

The virtual appliance is a pre-configured virtual machine, distributed as an OVA file, that runs Speechmatics Speech to Text (STT) on your own hardware. It runs Kubernetes (k3s) on a customized Ubuntu machine and is administered through a REST Management API.

Docs: https://docs.speechmatics.com/deployments/virtual-appliance

Version values here (latest appliance version `6.3.0`) are current at time of writing; check the docs.

## When to use

Use this skill for installing, licensing, verifying, securing, scaling, and monitoring a virtual appliance.

Use a sibling skill instead for:

- Running the STT containers directly with Docker: `speechmatics:container-deployment`
- Deploying with the Helm chart on your own cluster: `speechmatics:kubernetes-deployment`
- Job config, features, and output of the jobs API the Batch appliance exposes: `speechmatics:batch-transcription`
- WebSocket messages and session config the Realtime appliance exposes: `speechmatics:realtime-transcription`
- SaaS accounts, API keys, and first requests: `speechmatics:get-started`

## Modes

An appliance runs in one of two modes, fixed by the OVA build you download:

| Mode | Transcription API | Notes |
| --- | --- | --- |
| `batch` | Jobs API at `http(s)://${APPLIANCE_HOST}/v2/jobs/` | CPU or GPU transcription |
| `realtime` | WebSocket at `ws://${APPLIANCE_HOST}:9000/v2/<lang>` or `wss://${APPLIANCE_HOST}:9004/v2/<lang>` | Early access. GPU transcription only; CPU transcription is not supported |

Agent STT is SaaS only.

## Prerequisites

- A supported hypervisor: VMware ESXi v7.0+, VMware Workstation v16.0+ (CPU transcription only, no PCI passthrough), AWS EC2, or Proxmox VE v8.0+.
- A Support Portal account (https://support.speechmatics.com) to download the OVA and its sha512 checksum.
- A license file (`license.json`). The appliance uses the same license as the Speechmatics containers.
- A host CPU with AVX (AVX2 recommended), with all AVX instruction sets passed through to the VM.
- No conflict with the k3s subnets `10.42.0.0/16` (pods) and `10.43.0.0/16` (services).

Minimum VM size:

| Appliance | vCPUs | RAM | Disk |
| --- | --- | --- | --- |
| Batch, CPU transcription | 2 | 8GB | Up to 170GB |
| Batch, GPU transcription | 8 | 32GB | Up to 200GB |
| Realtime, GPU transcription | 8 | 16GB | Up to 100GB |

Recommended: 16 vCPUs and 32GB RAM for both modes. See [references/installation.md](references/installation.md) for per-stream resource tables.

## Install workflow

1. Download the `.ova` for the mode you need from the Support Portal knowledge base.
2. Import it into your hypervisor and size the VM. See [references/installation.md](references/installation.md).
3. Map the network adapter before first boot. The appliance acquires an IP address with DHCP by default.
4. Boot. Allow up to 4-5 minutes for the login screen.
5. Change the defaults: SSH `smadmin` / `changeme`, Management API `admin` / `admin`.
6. Apply the license.
7. Check health, then run a smoke test.

Set the host once for every example:

```bash
export APPLIANCE_HOST=<hostname-or-ip>
```

### Apply the license

```bash
curl -L -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/license" -d @license.json
```

### Check health

```bash
curl -sSL -u admin:admin -X 'GET' \
   "http://${APPLIANCE_HOST}/v2/management/health"
```

Each component (`database`, `batch_inference`, `monitoring`, `storage`, `realtime_inference`, `gpu_inference`) reports `healthy`, `disabled`, or `unhealthy`. An unhealthy component includes an `errors` list. Components not needed by the current mode report `disabled`.

### Batch smoke test

```bash
curl -s -L -X 'POST' \
   "http://${APPLIANCE_HOST}/v2/jobs/" \
   -F data_file=@{FILENAME} \
   -F 'config={ "type": "transcription",
         "transcription_config": { "language": "en" }
      }'

curl -s -L -X 'GET' "http://${APPLIANCE_HOST}/v2/jobs/${JOB_ID}/" | jq
curl -s -L -X 'GET' "http://${APPLIANCE_HOST}/v2/jobs/${JOB_ID}/transcript" | jq
```

A job should normally take less than half the duration of the media file. The jobs web UI is at `https://${APPLIANCE_HOST}/v2/ui`.

### Realtime smoke test

Uses the Speechmatics Python client (https://github.com/speechmatics/speechmatics-python):

```bash
speechmatics transcribe --lang en ${PATH_TO_AUDIO_FILE} --url "ws://${APPLIANCE_HOST}:9000/v2/en" --ssl-mode none
```

## Management API

Base URL: `http(s)://${APPLIANCE_HOST}`. HTTP basic authentication with username `admin` (fixed) and default password `admin`. HTTP uses port 80, HTTPS uses port 443 (drop the port and switch the scheme). A Management web UI runs at `http(s)://${APPLIANCE_HOST}/`.

| Method | Path | Purpose | Reference |
| --- | --- | --- | --- |
| GET | `/v2/management/health` | Component health | services-and-security |
| GET | `/v2/management/host/about` | Version, variant, installed languages | services-and-security |
| GET, POST, DELETE | `/v2/management/license` | Check, apply, remove the license | licensing |
| POST | `/v2/management/usagereporting` | Usage reporting mode and proxy | licensing |
| GET | `/v2/management/cpuinfo` | CPU model, cores, flags | installation |
| GET | `/v2/management/meminfo` | RAM usage | monitoring-and-logs |
| GET | `/v2/management/nodeinfo` | Kubernetes node labels, including GPU | scaling-and-gpu |
| GET | `/v2/management/logs/zip?limit=1h` | Download logs as ZIP | monitoring-and-logs |
| DELETE | `/v2/management/reboot` | Reboot (one minute delay) | services-and-security |
| DELETE | `/v2/management/shutdown` | Shut down (one minute delay) | services-and-security |
| POST | `/v2/management/cleanupinterval` | Job artifact cleanup interval | services-and-security |
| POST | `/v2/management/host/scaling` | Batch `scaling_mode` | scaling-and-gpu |
| POST | `/v2/management/host/langid` | Enable Language Identification (Batch) | scaling-and-gpu |
| GET, POST | `/v2/management/host/gpu` | Batch GPU inference on or off | scaling-and-gpu |
| GET, POST | `/v2/management/host/gpu/config` | Batch `primary_operating_point`, `max_jobs` | scaling-and-gpu |
| GET, POST | `/v2/management/host/realtime/gpu` | Realtime GPU inference on or off | scaling-and-gpu |
| GET, POST | `/v2/management/host/realtime/gpu/config` | Realtime `max_streams` | scaling-and-gpu |
| GET | `/v2/management/host/realtime/sessions` | Active Realtime session IDs | scaling-and-gpu |
| GET | `/v2/management/host/realtime/ready` | Capacity for a new Realtime session | scaling-and-gpu |
| POST, DELETE | `/v2/security/adminpassword` | Set the admin password, or disable authentication | services-and-security |
| POST, DELETE | `/v2/security/jobtoken` | Set or remove the transcription token | services-and-security |
| POST | `/v2/security/sslcertificate` | Upload certificate and private key | networking-and-ssl |
| POST | `/v2/security/insecureports` | Disable HTTP access | networking-and-ssl |
| DELETE | `/v2/security/reset` | Reset SSL settings and admin password | networking-and-ssl |

Do not use any Management API endpoint, method, or field that is not in this table or the references.

## Ports

| Port/Protocol | Use |
| --- | --- |
| 22/TCP | SSH access |
| 80/TCP | Management API, and submitting jobs (`batch` mode) |
| 443/TCP | HTTPS for the above |
| 9000/TCP | WebSocket for Realtime transcription (`realtime` mode) |
| 9004/TCP | Secure WebSocket for Realtime transcription (`realtime` mode) |
| 9001/TCP | Prometheus metrics |
| 3100/TCP | Loki logs endpoint |

With HTTPS set up, expose only 443 for `batch` mode, and 443 and 9004 for `realtime` mode.

## Essential settings

| Setting | Endpoint | Values and defaults |
| --- | --- | --- |
| `scaling_mode` | `/v2/management/host/scaling` | `simple` (one thread per job) or `adaptive` (up to 4 threads by audio length; needs at least 4 cores) |
| `gpu_enabled` | `/v2/management/host/gpu`, `/v2/management/host/realtime/gpu` | `true` or `false`. Disabled by default |
| `primary_operating_point` | `/v2/management/host/gpu/config` | `standard` or `enhanced` |
| `max_jobs` | `/v2/management/host/gpu/config` | Suggested: 48 for standard, 28 for enhanced |
| `max_streams` | `/v2/management/host/realtime/gpu/config` | Suggested starting point: 64 for standard, 16 for enhanced |
| `max_thread_count` | `/v2/management/host/langid` | `0` disables Language Identification (default) |
| `memory_per_thread` | `/v2/management/host/langid` | Optional. Default `3Gi` |
| `minutes` | `/v2/management/cleanupinterval` | Default cleanup is every 24 hours |
| `user_token` | `/v2/security/jobtoken` | No transcription authentication by default |
| `enable_insecure_ports` | `/v2/security/insecureports` | `false` redirects HTTP to HTTPS |

## Gotchas

- The transcriber does not start until the appliance is licensed. An unlicensed Realtime appliance reports `realtime_inference` as `unhealthy` with `expected deployment: sm-transcriber-en to have 1 ready replicas have: 0`.
- `GET /v2/management/license` returns 404 when no license is present.
- The default certificate is self-signed. Add `--insecure` to curl, or `--ssl-mode insecure` to the Python client, until you upload your own certificate.
- Upload the certificate and private key over HTTPS only, never HTTP.
- Job artifact cleanup removes all job data, including transcripts. Retrieve transcripts before the cleanup interval elapses.
- Reboot and shutdown through the Management API happen after a one minute delay. Prefer SSH or the hypervisor console.
- Adding languages with `configure_languages.sh` works in `batch` mode only and installs CPU-only languages. For extra Realtime languages, contact Support.
- Appliance versions up to and including `6.2.1` pull from a deprecated registry by default. Set `SM_DOCKER_PUBLIC=speechmaticspublic.azurecr.io` before adding languages.
- Language Identification is disabled by default and is Batch only.
- In `realtime` mode, sessions beyond `max_streams` are rejected. Check `/v2/management/host/realtime/ready` before starting a session. Do not mix operating points.
- `Illegal instruction` errors in job logs mean the host or hypervisor does not expose AVX. Check `flags` from `/v2/management/cpuinfo`.
- A `SoftTimeLimitExceeded` exception means a job ran too long, typically because of slow disk IO. Raise IOPS to 8,000-12,000 if you run more than 10 concurrent workers.
- Low IOPS can make the first few transcription requests on a fresh VM fail.
- `/v2/security/reset` also deletes the configured admin password.

## References

- [references/installation.md](references/installation.md): system requirements, per-stream resources, IOPS, downloading the OVA, importing on ESXi, Workstation, AWS and Proxmox, first boot, health checks, and smoke tests. Read when sizing or importing an appliance.
- [references/licensing.md](references/licensing.md): applying, checking, and removing a license, license feature codes, usage reporting, and proxies. Read for any license question.
- [references/networking-and-ssl.md](references/networking-and-ssl.md): interface mapping, static IP with netplan, cloud-init, DHCP reservation, subnets, firewall ports, HTTPS, certificate upload, disabling HTTP, resets, and TLS versions and cipher suites. Read when configuring the network or TLS.
- [references/services-and-security.md](references/services-and-security.md): about and health endpoints, restart and shutdown, cleanup interval, admin password, transcription token, SSH access, at-rest encryption, and troubleshooting. Read for day-to-day administration and failures.
- [references/scaling-and-gpu.md](references/scaling-and-gpu.md): `scaling_mode`, Realtime sessions and readiness, GPU enablement and configuration, `nodeinfo`, adding and removing languages, and Language Identification. Read when tuning throughput or changing languages.
- [references/monitoring-and-logs.md](references/monitoring-and-logs.md): `meminfo`, Prometheus queries, log ZIP download, Loki queries, and the full `logcli` manual. Read when monitoring resources or collecting logs.
