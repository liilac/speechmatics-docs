---
name: kubernetes-deployment
description: Deploys Speechmatics Realtime Speech to Text on Kubernetes with the sm-realtime Helm chart. Covers prerequisites (registry and Helm login, speechmatics-registry and speechmatics-license secrets, private registry mirroring, Nvidia device plugin), exposing proxy-service through Gateway API (HTTPRoute, ListenerSet, NGINX Gateway Fabric) or an Ingress, request IDs, install, validation with kubectl get sessiongroups, values for languages, inference server recipes, models and autoscaling, version selection, upgrade, rollback and uninstall. Use when the user mentions Kubernetes, k8s, Helm, helm upgrade --install, values.yaml, sm-charts/sm-realtime, SessionGroups, ingress-nginx, proxy.ingress.hostname, proxy.httproute, global.imageRegistry, inferenceServerEnhancedRecipe1, scaleOnCapacityLeft, or rtWorkersVersionConfig.
---

# Speechmatics on Kubernetes

Deploy Speechmatics Realtime Speech to Text (STT) on Kubernetes with the `sm-realtime` Helm chart.

Docs: https://docs.speechmatics.com/deployments/kubernetes

Chart version `1.5.0` is current at time of writing; check the docs.

## When to use

- Installing, configuring, scaling, upgrading or removing the Realtime Helm chart.
- Setting up registry access, the license secret, GPU nodes, and a gateway or ingress for the chart.

The Kubernetes deployment supports Realtime only. Use a sibling skill instead for:

- Single Docker containers, batch on-prem, GPU inference server details, usage reporting, container environment variables, container health probe endpoints, and non-root or `emptyDir` settings for your own pod specs: `speechmatics:container-deployment`.
- The virtual appliance: `speechmatics:virtual-appliance`.
- Realtime WebSocket messages and client code: `speechmatics:realtime-transcription`.
- Feature config: `speechmatics:transcription-features`.
- SaaS setup: `speechmatics:get-started`.

## What the chart deploys

| Component | Role |
|---|---|
| Proxy service (`proxy-service`) | Accepts client WebSocket connections from your gateway or ingress controller |
| Resource manager | Tracks capacity and assigns each session to a transcriber and an inference server |
| Transcribers | Run the speech recognition pipeline for a session. One deployment per language |
| Inference servers | Run the models on GPUs, shared by many transcribers |
| Redis | Stores the capacity and session state used by the resource manager |

Transcribers and inference servers are managed as `SessionGroups`, a custom resource that scales them with demand and protects pods with active sessions from removal.

## Prerequisites

| Requirement | Detail |
|---|---|
| Registry access | Credentials for `speechmaticspublic.azurecr.io` (images and chart), from [Support](https://support.speechmatics.com) |
| Private registry | Optional. Recommended for closed environments |
| License | A Speechmatics license in a secret named `speechmatics-license` |
| GPU drivers | GPU nodes with the Nvidia device plugin |
| Ingress | Gateway API (recommended) or an ingress controller that supports WebSockets |
| Request ID | Optional headers for tracing sessions |

On a shared cluster, create and reference all resources in the same namespace.

```bash
# Registry credentials for image pulling (default global.imagePullSecrets name)
kubectl create secret docker-registry speechmatics-registry \
  --docker-server=speechmaticspublic.azurecr.io \
  --docker-username=<username> \
  --docker-password=<password>

# Authenticate Helm
helm registry login speechmaticspublic.azurecr.io \
  --username <username> \
  --password <password>

# License secret
kubectl create secret generic speechmatics-license \
  --from-file=license.json=./license.json

# Check which nodes have allocatable GPUs (<none> means no GPU)
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
```

Details, private registry mirroring and chart-created license secret: [references/prerequisites.md](references/prerequisites.md).

## Install

Create `values.yaml`. It must at least set the hostname clients connect to.

With the default `Ingress` (written for `ingress-nginx`, `ingressClassName: nginx`):

```yaml
proxy:
  ingress:
    hostname: speechmatics.example.com
```

With Gateway API (recommended for new deployments; the chart creates an `HTTPRoute`, you manage the `Gateway`):

```yaml
proxy:
  ingress:
    # Disable the default Ingress
    enabled: false

  httproute:
    enabled: true

    # Hostname to match
    hostname: speechmatics.example.com

    # Gateway that accepts traffic for this route
    parentRefs:
      - name: my-gateway
        namespace: nginx-gateway
        sectionName: https
```

Install:

```bash
helm upgrade --install speechmatics-realtime \
  oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime \
  --version 1.5.0 \
  -f values.yaml
```

Gateway and ingress controller setup: [references/ingress-and-gateway.md](references/ingress-and-gateway.md).

## Validate

With default values the chart deploys an English transcriber and an Enhanced inference server.

```bash
kubectl get sessiongroups
```

```
NAME                                REPLICAS   CAPACITY   USAGE   VERSION   SPEC HASH
inference-server-enhanced-recipe1   1          480        0       1         b5784af49332f9948481195451eab6ca
rt-transcriber-en                   1          2          0       1         83929f2b9b2448cdc818d0e46e37600b
```

`CAPACITY` is non-zero once transcribers and inference servers have started and registered. Inference servers can take several minutes to load models.

Run a session. Install the CLI with `pip install speechmatics-python`, and make sure the hostname resolves to your ingress or gateway:

```bash
speechmatics rt transcribe \
  --url wss://speechmatics.example.com/v2 \
  --lang en \
  --operating-point enhanced \
  --ssl-mode insecure \
  <audio-file>
```

`--ssl-mode insecure` skips certificate validation (for example a self-signed certificate); remove it once a trusted certificate is in place. `--operating-point` is the CLI option that selects the model.

Client endpoint: `wss://<hostname>/v2`. For applications, set the `url` of a Speechmatics SDK to that address.

## Essential values

| Value | Purpose |
|---|---|
| `proxy.ingress.hostname` | Hostname for the default `Ingress`. Replaces deprecated `proxy.ingress.url`, still honored as a fallback |
| `proxy.ingress.enabled` | `false` disables the default `Ingress` |
| `proxy.ingress.ingressClassName` | Ingress class. Default `nginx` |
| `proxy.ingress.annotations`, `proxy.ingress.path` | Defaults are specific to `ingress-nginx`; the default path is a regular expression |
| `proxy.httproute.enabled`, `.hostname`, `.parentRefs`, `.filters` | Gateway API `HTTPRoute` |
| `proxy.listenerset.*` | Chart-created `ListenerSet` attached to your `Gateway` |
| `global.imageRegistry` | Replaces the registry of every image in the chart, including Redis |
| `global.imagePullSecrets` | Pull secrets. Default uses `speechmatics-registry` |
| `global.licensing.createSecret`, `global.licensing.license` | Let the chart create the license secret from a base64-encoded license |
| `global.transcriber.languages` | Languages to deploy transcribers for |
| `inferenceServerEnhancedRecipe1` to `4`, `inferenceServerStandardAll`, `inferenceServerAll`, `inferenceServerCustom` | Inference server deployments, each with `enabled` |
| `<inferenceServer>.tritonServer.languages` | Load only these languages from the image |
| `<inferenceServer>.tritonServer.memoryPool.cudaByteSize` | GPU memory pool size |
| `<inferenceServer>.inferenceSidecar.registerFeatures` | `capacity`, `languages`, `model` for custom model deployments |
| `global.sessionGroups.scaling.enabled` | Enable scaling for all `sessiongroups` |
| `<component>.sessionGroups.scaling.scaleOnCapacityLeft` | Scale up when this much capacity remains |
| `resourceManager.config.rtWorkersVersionConfig` | Which transcriber and inference server versions are paired |

Full option list is in the chart README:

```bash
helm show readme oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime --version 1.5.0
```

Complete values files for each scenario: [references/configuration.md](references/configuration.md).

## Hardware

Recommended Azure node sizes:

| Service | Node size |
|---|---|
| Inference server | Standard_NC4as_T4_v3 |
| Transcriber | Standard_E16s_v5 |
| All other services | Standard_D*s_v5 |

Serving every language from one inference server (`inferenceServerAll`) needs a GPU with a large amount of memory, such as an L40S or H100. On smaller GPUs such as a T4, use the per-recipe inference servers.

## Upgrade and uninstall

Helm does not upgrade CRDs. Update the `sessiongroups` CRD first, then rerun the install command with the new `--version`:

```bash
helm show crds oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime \
  --version 1.5.0 | kubectl apply --server-side -f -
```

```bash
helm rollback speechmatics-realtime     # does not roll back the CRD
helm uninstall speechmatics-realtime
kubectl get pvc | grep redis-data       # delete leftovers with kubectl delete pvc
```

Details: [references/operations.md](references/operations.md).

## Gotchas

- The chart does not create the `Gateway`. Create and manage it yourself; the TLS secret must be in the `Gateway`'s namespace.
- `ingress-nginx` is retired (maintenance ended March 2026). Existing installs work; use Gateway API for new deployments.
- Gateway or ingress pods that restart or reload end active WebSocket sessions unless configured for graceful shutdown (the docs use 24h timeouts).
- Redis is not in the Speechmatics registry. When mirroring, also mirror the Docker Hub `redis` image under the same name.
- Use `model` keys in values. `operatingPoint` is deprecated and removed in chart 2.0.0. `model: ""` does not clear an inherited `operatingPoint`.
- Client-side `kubectl apply` of the CRD fails with `metadata.annotations: Too long`; use `--server-side`.
- From chart 1.5.0 the default `Ingress` no longer adds a `Request-Id` response header.
- Nvidia driver requirements follow the container version: see `speechmatics:container-deployment`.

## References

| Read | When |
|---|---|
| [references/prerequisites.md](references/prerequisites.md) | Registry and Helm login, private registry mirroring, license secret, GPU device plugin |
| [references/ingress-and-gateway.md](references/ingress-and-gateway.md) | NGINX Gateway Fabric, `Gateway`, `HTTPRoute`, `ListenerSet`, `ingress-nginx`, other controllers, request ID headers, graceful shutdown |
| [references/configuration.md](references/configuration.md) | Values files for all languages, smaller GPUs, English only, language subset, autoscaling; models; version selection |
| [references/operations.md](references/operations.md) | Install, validate, upgrade, 1.5.0 upgrade notes, rollback, uninstall |
