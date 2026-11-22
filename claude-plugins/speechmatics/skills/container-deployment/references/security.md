# Security hardening and speaker identification secrets

Docs:

- https://docs.speechmatics.com/deployments/container/additional-security
- https://docs.speechmatics.com/deployments/container/speaker-identification

Read-only and non-root options for the realtime container are in [cpu-realtime.md](cpu-realtime.md).

## Contents

- Batch container with temporary storage
- Batch container as a non-root user
- Non-root on Kubernetes
- Speaker identification secrets

## Batch container with temporary storage

Run the batch container without writing to disk by using `tmpfs` or `ramfs`. The container supports mounting temporary directories for intermediate files, and mounting the directories for input, output and job config.

Use `--job-config <path>` to give the location of the config inside the container. The argument must come after the image name.

Intermediate files in `tmpfs`, config in a host volume mounted at `/tmp`:

```bash
docker run --rm -i \
    --read-only --tmpfs /home/smuser \
    -v <path/to/dir/in/host/containing/config.json>:/tmp \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0 \
    --job-config /tmp/config.json
```

Alternatively, make `/tmp` a `tmpfs` too and mount the config from a read-only volume. `--job-config` must point at the path where the volume is mounted in the container:

```bash
docker run --rm -i \
    --read-only --tmpfs /home/smuser --tmpfs /tmp \
    -v <path/to/dir/in/host/containing/config.json>:/configs_dir:ro \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0 \
    --job-config /configs_dir/config.json
```

(The docs example passes `--job-config /example_configs_dir/config.json` while mounting `/configs_dir`; the two paths must match.)

On Kubernetes, use an `emptyDir` volume to mount `tmpfs` at `/home/smuser` and `/tmp`. The config can also live in an `emptyDir` if another container in the pod puts it there, for example an initContainer or a sidecar. Call the transcriber with `--job-config` pointing at that path.

Fetch audio from a temporary location with `fetch_data`:

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en"
  },
  "fetch_data": {
    "url": "file:///tmp/$FILENAME.wav"
  }
}
```

## Batch container as a non-root user

Start the container with `--user $USERNUMBER:$GROUPID`. Both are numeric values from 1 to 65535.

```bash
docker run --user 1000:3000 ubuntu echo hello world
```

Transcript output on STDOUT is unchanged for a non-root user:

```bash
docker run -u 1020:4000 \
 -v /Users/$USER/work/pipeline/mydev/config.json:/config.json \
 -v /Users/$USER/work/pipeline/mydev/input.audio:/input.audio \
    ${IMAGE_NAME}
```

To write output to a directory, volume-map a directory the non-root user can access.

## Non-root on Kubernetes

The docs give this as a guideline for when non-root is unavoidable, not as a recommendation.

Set the pod security context. The user and group must match those used when starting the container, and be non-zero values up to 65535:

```yaml
securityContext:
  runAsUser: <user number>
  runAsGroup: <group id>
```

More: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/

If the deployment mandates PodSecurity admission controllers, the docs give this example configuration that allows transcription as a non-root user:

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
  annotations:
    seccomp.security.alpha.kubernetes.io/allowedProfileNames: 'docker/default,runtime/default'
    apparmor.security.beta.kubernetes.io/allowedProfileNames: 'runtime/default'
    seccomp.security.alpha.kubernetes.io/defaultProfileName: 'runtime/default'
    apparmor.security.beta.kubernetes.io/defaultProfileName: 'runtime/default'
spec:
  privileged: false
  # Required to prevent escalations to root.
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  # Allow core volume types.
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    # Assume that persistentVolumes set up by the cluster admin are safe to use.
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    # Require the container to run without root privileges.
    rule: 'MustRunAsNonRoot'
  seLinux:
    # This policy assumes the nodes are using AppArmor rather than SELinux.
    rule: 'RunAsAny'
  supplementalGroups:
    rule: 'MustRunAs'
    ranges:
      # Forbid adding the root group.
      - min: 1
        max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
      # Forbid adding the root group.
      - min: 1
        max: 65535
  readOnlyRootFilesystem: false
```

## Speaker identification secrets

Speaker identification requires the batch or realtime transcriber to access one or more cryptographically strong secrets. They generate and validate speaker identifiers. For the feature itself, see `speechmatics:transcription-features`.

Batch speaker identification requires GPU inference. It is not supported by the CPU container in batch mode; use the GPU inference server. Realtime speaker identification is supported on both CPU and GPU.

### Prepare the secret directory

Store secrets in a dedicated host directory, one secret per file, named `<secret_dir>/s.<integer>`:

```
/speaker_id_secrets/s.1
/speaker_id_secrets/s.2
```

- Files may hold binary data or plain text, for example Base64-encoded values.
- The transcriber reads every file matching `s.<integer>` in the directory.
- Multiple files allow rotation without disrupting workloads. The highest-numbered file is the most recent secret and generates new identifiers. Identifiers encrypted with older secrets are still accepted.
- Most on-prem deployments need a single secret file unless rotation is required.

### Mount the directory

Mount it read-only and set `SM_SPEAKER_ID_SECRETS_DIR` to its location in the container. The transcriber loads all secret files at startup.

```bash
docker run --rm -i \
 -v <path/to/dir/in/host/containing/speaker_id_secrets_dir>:/speaker_id_secrets:ro \
 -e SM_SPEAKER_ID_SECRETS_DIR=/speaker_id_secrets -e LICENSE_TOKEN=$TOKEN_VALUE \
 $IMAGE_NAME
```

With the batch persistent worker, pass `user_id` in the `X-SM-Processing-Data` header for per-customer encrypted identifiers. See [batch-persistent-worker.md](batch-persistent-worker.md).
