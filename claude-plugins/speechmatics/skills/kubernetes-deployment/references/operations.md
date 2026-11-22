# Install, validate, upgrade and uninstall

Docs: https://docs.speechmatics.com/deployments/kubernetes/realtime

Chart version `1.5.0` is current at time of writing; check the docs.

## Install

1. Complete the [prerequisites](prerequisites.md) and set up a [gateway or ingress](ingress-and-gateway.md).
2. Create `values.yaml`. It must at least set the hostname clients connect to. With the default `Ingress`:

```yaml
proxy:
  ingress:
    hostname: speechmatics.example.com
```

With Gateway API, use the `HTTPRoute` values in [ingress-and-gateway.md](ingress-and-gateway.md) instead. More options: [configuration.md](configuration.md).

3. Install the chart:

```bash
# Install the sm-realtime chart
helm upgrade --install speechmatics-realtime \
  oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime \
  --version 1.5.0 \
  -f values.yaml
```

## Validate

### Capacity check

```bash
kubectl get sessiongroups
```

```
NAME                                REPLICAS   CAPACITY   USAGE   VERSION   SPEC HASH
inference-server-enhanced-recipe1   1          480        0       1         b5784af49332f9948481195451eab6ca
rt-transcriber-en                   1          2          0       1         83929f2b9b2448cdc818d0e46e37600b
```

With default values the chart deploys an English transcriber and an Enhanced inference server. `CAPACITY` shows a non-zero value once they have started and registered. Inference servers can take several minutes to load their models, so a `CAPACITY` of 0 shortly after install is expected.

### Run a session

Install the Speechmatics CLI with `pip install speechmatics-python`. Make sure the configured hostname resolves to your ingress or gateway.

```bash
speechmatics rt transcribe \
  --url wss://speechmatics.example.com/v2 \
  --lang en \
  --operating-point enhanced \
  --ssl-mode insecure \
  <audio-file>
```

- `--ssl-mode insecure` skips certificate validation, for example with a self-signed certificate. Remove it once a trusted certificate is in place.
- `--operating-point` is the CLI option for selecting the model.

To build applications against the deployment, use a Speechmatics SDK and set its `url` to the deployment address, for example `wss://speechmatics.example.com/v2`. See `speechmatics:realtime-transcription`.

### Tracing a session

Each session has a request ID in the `proxy-service` logs. Configure `X-Request-Id` and `Request-Id` headers as described in [ingress-and-gateway.md](ingress-and-gateway.md#request-id).

## Upgrade

Helm does not upgrade CustomResourceDefinitions (CRDs). Before upgrading the chart, update the `sessiongroups` CRD:

```bash
helm show crds oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime \
  --version 1.5.0 | kubectl apply --server-side -f -
```

Server-side apply avoids the `metadata.annotations: Too long` error that client-side apply returns for this CRD.

Then upgrade with the same `helm upgrade --install` command and values used to install, with the new `--version`.

During an upgrade, transcribers and inference servers of different versions can run side by side. The resource manager only pairs compatible versions; see version selection in [configuration.md](configuration.md#version-selection).

### Upgrading to 1.5.0

- The default `Ingress` no longer adds a `Request-Id` response header, so `ingress-nginx` no longer needs snippet annotations enabled. To keep the header, see [ingress-and-gateway.md](ingress-and-gateway.md#request-id).
- `operatingPoint` values keep working until chart 2.0.0. Move to `model`; see [configuration.md](configuration.md#models).

## Roll back

```bash
helm rollback speechmatics-realtime
```

Rolls back to the previous chart version. It does not roll back the `sessiongroups` CRD.

## Uninstall

```bash
helm uninstall speechmatics-realtime
```

Depending on the configuration, also remove PVCs created by the Redis deployment:

```bash
# Delete any left-over PVCs with `kubectl delete pvc`
kubectl get pvc | grep redis-data
```
