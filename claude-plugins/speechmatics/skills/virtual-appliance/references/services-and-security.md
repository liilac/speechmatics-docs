# Services and security

Docs:

- https://docs.speechmatics.com/deployments/virtual-appliance/administration/services
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/security
- https://docs.speechmatics.com/deployments/virtual-appliance/administration/remote-access

## Contents

- [About](#about)
- [Health](#health)
- [Restart and shutdown](#restart-and-shutdown)
- [Job artifact cleanup](#job-artifact-cleanup)
- [Security overview](#security-overview)
- [Remote access](#remote-access)
- [Management API authentication](#management-api-authentication)
- [Transcription token](#transcription-token)
- [Troubleshooting](#troubleshooting)

## About

```bash
curl -sSL -u admin:admin -X 'GET' \
   "http://${APPLIANCE_HOST}/v2/management/host/about"
```

```json
{
  "appliance_version": "6.3.0",
  "appliance_variant": "sm-realtime-appliance-6.3.0-xxxxxxx",
  "languages": [
    "en"
  ]
}
```

| Field | Meaning |
| --- | --- |
| `appliance_version` | Appliance version |
| `appliance_variant` | Specific build and mode of the appliance |
| `languages` | Languages installed in the appliance |

`6.3.0` is the latest appliance version at time of writing; check the docs.

## Health

```bash
curl -sSL -u admin:admin -X 'GET' \
   "http://${APPLIANCE_HOST}/v2/management/health"
```

Each component status is one of `healthy`, `disabled`, or `unhealthy`. An unhealthy component includes related errors:

```json
{
  "status": "healthy",
  "database": { "status": "healthy" },
  "batch_inference": { "status": "healthy" },
  "monitoring": { "status": "healthy" },
  "storage": { "status": "healthy" },
  "realtime_inference": { "status": "disabled" },
  "gpu_inference": {
    "status": "unhealthy",
    "errors": ["expected deployment: sm-gpu to have 1 ready replicas have: 0"]
  }
}
```

Field meanings and common health issues are in [installation.md](installation.md#verify-the-appliance).

## Restart and shutdown

If the appliance becomes unresponsive, restart it through an SSH session or the hypervisor console. The legacy Management API commands remain available:

```bash
# reboot
curl -sSL -u admin:admin -X 'DELETE' "http://${APPLIANCE_HOST}/v2/management/reboot"
# shutdown
curl -sSL -u admin:admin -X 'DELETE' "http://${APPLIANCE_HOST}/v2/management/shutdown"
```

The action occurs one minute after the request.

## Job artifact cleanup

Job execution saves artifacts to disk, such as the job config and audio file. They are cleared automatically every 24 hours. Change the interval:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/cleanupinterval" \
  -H 'Content-Type: application/json' \
  -d '{
  "minutes": 1
}'
```

Also available in the Management interface at `http://${APPLIANCE_HOST}/#/Management/Management_SetCleanupInterval`. (The docs give this path without `/docs`, but give the log download page as `http://${APPLIANCE_HOST}/docs/#/Management/ZipLogs`.)

Cleanup removes all job data, including processed transcripts. Retrieve and store transcripts externally before they are deleted.

## Security overview

- Install the appliance inside your own security perimeter.
- The appliance runs a Kubernetes architecture on a customized Ubuntu machine. AppArmor default security policies protect the OS and running applications.
- Its own firewall allows ingress only to the ports required for the Management, Monitoring and Speech APIs. See [networking-and-ssl.md](networking-and-ssl.md#firewall-ports).
- Data on the appliance (submitted audio and video, logs, and output transcripts) is encrypted on disk only if the hypervisor is configured to manage at-rest encryption. The OVA is not encrypted by default. For at-rest encryption, follow your hypervisor's instructions.

## Remote access

The appliance accepts SSH with username `smadmin` and password `changeme`. Disable password access and set up access with an SSH key: [Key-based SSH access (Ubuntu)](https://help.ubuntu.com/community/SSH/OpenSSH/Keys). Alternatively, block access to port 22.

## Management API authentication

All Management API requests need HTTP basic authentication unless it is explicitly turned off. The username is always `admin` and cannot be changed. The default password is `admin`.

Set your own password (advised):

```bash
curl -sSL -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/security/adminpassword" \
  -H 'Content-Type: application/json' \
  -d '{
  "password": "yourpassword"
}'
```

Over HTTPS with the default self-signed certificate:

```bash
curl --insecure -L -u admin:admin -X 'POST' \
  "https://${APPLIANCE_HOST}/v2/security/adminpassword" \
  -H 'Content-Type: application/json' \
  -d '{ "password": "example" }'
```

A successful request returns HTTP 200 with a success message. The web server takes around five seconds to restart. Unauthenticated requests then fail:

```
$ curl -X 'GET' "http://${APPLIANCE_HOST}/v2/management/host/about"
401 Unauthorized
```

Authenticate with curl's `--user` flag:

```bash
curl -L --user "admin:$PWD" -X GET "http://${APPLIANCE_HOST}/v2/management/host/about"
```

In a browser, the Management interface prompts for the username and password.

Disable authentication against the Management API:

```bash
curl -sSL -u admin:admin -X 'DELETE' \
  "http://${APPLIANCE_HOST}/v2/security/adminpassword"
```

These operations are also available in the Management web UI at `http(s)://${APPLIANCE_HOST}/`.

To recover a forgotten password, see [networking-and-ssl.md](networking-and-ssl.md#reset-a-forgotten-admin-password).

## Transcription token

Appliance versions before 6.0.0 required no authentication for the ASR API. Later versions require none by default, but you can configure a token of your choice. Depending on the appliance mode, it protects the jobs endpoint or the Realtime WebSocket.

Set the token:

```bash
curl -sSL -u admin:admin -X 'POST' \
  "https://${APPLIANCE_HOST}/v2/security/jobtoken" \
  -H 'Content-Type: application/json' \
  -d '{"user_token": "$AUTH_TOKEN"}'
```

The single quotes stop the shell expanding `$AUTH_TOKEN`. Substitute your token value in the body.

Remove the token:

```bash
curl -sSL -u admin:admin -X 'DELETE' \
  "https://${APPLIANCE_HOST}/v2/security/jobtoken"
```

With a token set, transcription requests need an authentication header identical to the kind used with Speechmatics SaaS.

### Batch mode

The jobs API requires `Authorization: Bearer $AUTH_TOKEN`:

```bash
curl -s -L -X 'POST' "https://${APPLIANCE_HOST}/v2/jobs/" \
   -H "Authorization: Bearer $AUTH_TOKEN" \
   -F data_file=@sample.wav \
   -F 'config={ "type": "transcription",
         "transcription_config": { "language": "en" }
      }'
```

The docs page passes `config` with `-d` in this example; curl cannot combine `-F` and `-d`, so `-F` is used here, as in the docs' smoke test.

### Realtime mode

The WebSocket requires the token. With the Speechmatics Python client:

```bash
speechmatics config set --auth-token $AUTH_TOKEN
speechmatics transcribe --lang en ${PATH_TO_AUDIO_FILE} --url "ws://${APPLIANCE_HOST}:9000/v2/en" --ssl-mode none
```

## Troubleshooting

When the appliance behaves unexpectedly:

1. Check appliance health.
2. Check the license is valid. See [licensing.md](licensing.md).
3. Check the worker services are running.
4. Check CPU, memory and disk are not exhausted. See [monitoring-and-logs.md](monitoring-and-logs.md).
5. Restart the appliance.
6. Collect logs and contact [Support](https://support.speechmatics.com). See [monitoring-and-logs.md](monitoring-and-logs.md#download-logs-as-a-zip).

### Transcription job failure

If a job fails with an `error` job status, search the logs of the `api` container for the job ID.

A `SoftTimeLimitExceeded` exception means the job took longer than expected and was terminated. The typical cause is poor VM performance, in particular slow disk IO (IOPS). Improve disk IO on the host, or add RAM to the VM so memory caches help. Check you are not over-committing compute resources. See [installation.md](installation.md#iops).

### Illegal instruction errors

If jobs fail repeatedly with `Illegal instruction` in their logs, the host hardware probably does not support AVX. The machine learning algorithms used by Speechmatics ASR require AVX. Check with:

```bash
curl -sSL -u admin:admin -X 'GET' \
  "http://${APPLIANCE_HOST}/v2/management/cpuinfo"
```

If `avx` is missing from `flags`, the host CPU does not support AVX or the hypervisor does not pass it through.

### AVX2 warning

The appliance is optimized for hardware with the AVX2 flag. This message means the hardware is not optimized and jobs may run slower:

```
WARNING ([5.5.675~1-0c22]:SetupMathLibrary():asrengine/asrengine.cc:356) Unable to set CNR mode to 10 (AVX2); falling back to 9. The transcription might be slower and/or use more CPU resource.
```

### Pending jobs

Jobs enter a pending state in Kubernetes when the machine lacks resources to schedule them. Check the number of running jobs. Pending jobs start once running jobs complete and free enough resources.

### Jobs storage full

Job artifacts are stored for 24 hours after job completion by default. With a high volume of jobs, local storage can fill and jobs begin to fail. Monitor job storage with Prometheus (see [monitoring-and-logs.md](monitoring-and-logs.md#useful-prometheus-queries)) and reduce the cleanup interval if it fills too quickly.

Delete individual jobs through the jobs API:

```bash
curl -sSL -u admin:admin -X 'DELETE' \
  "https://${APPLIANCE_HOST}/v2/jobs/${job_id}"
```

### First requests fail on a fresh VM

Low IOPS lengthens appliance startup. If IOPS is too low, the first few transcription requests on a fresh VM may fail. See [installation.md](installation.md#iops).

### Deeper diagnosis

Log on to the appliance and use `kubectl` and `journald` commands directly.
