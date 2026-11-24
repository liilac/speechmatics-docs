# Kubernetes prerequisites

Docs: https://docs.speechmatics.com/deployments/kubernetes/prerequisites

Chart version `1.5.0` is current at time of writing; check the docs.

Ingress and gateway setup is in [ingress-and-gateway.md](ingress-and-gateway.md).

## Checklist

| Requirement | Detail |
|---|---|
| Registry access | Credentials for the Speechmatics image and chart registry |
| Private registry | Optional. Recommended for closed environments |
| Speechmatics license | Stored as a secret on the cluster |
| GPU drivers | GPU nodes with the Nvidia device plugin |
| Ingress setup | Gateway API (recommended) or an ingress controller that supports WebSockets |
| Request ID | Optional. Headers for tracing sessions |

If you do not fully control the cluster, or it is shared, create and reference all resources in the same namespace.

## Docker and Helm registry access

Images and the Helm chart come from `speechmaticspublic.azurecr.io`. Get credentials from [Support](https://support.speechmatics.com).

Add a `docker-registry` secret so the cluster can pull images:

```bash
# Add the speechmatics registry credentials for image pulling
kubectl create secret docker-registry speechmatics-registry \
  --docker-server=speechmaticspublic.azurecr.io \
  --docker-username=<username> \
  --docker-password=<password>
```

The chart uses the `speechmatics-registry` secret by default, through the `global.imagePullSecrets` value.

Authenticate Helm with the same credentials:

```bash
# Authenticate to the Speechmatics Helm repository
helm registry login speechmaticspublic.azurecr.io \
  --username <username> \
  --password <password>
```

## Private registry

Mirror the images into a registry you control when the cluster cannot reach external registries, or to control which images are available to the cluster.

1. Mirror images under the same repository names and tags, for example `my-registry.example.com/rt-asr-transcriber-en:<version>`. List the images your configuration uses by rendering the chart:

```bash
helm template oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime \
  --version 1.5.0 -f values.yaml | grep 'image:' | sort -u
```

2. Redis is not published to `speechmaticspublic.azurecr.io`. Mirror the Docker Hub `redis` image under the same name. The command above lists the Redis image and tag.

3. Set `global.imageRegistry`. It replaces the registry of every image in the chart, including Redis, and keeps each image's repository and tag:

```yaml
global:
  imageRegistry: my-registry.example.com
  # Secret for your registry, or [] if nodes can pull without one
  imagePullSecrets:
    - name: my-registry
```

4. Optionally host the chart in your registry too:

```bash
helm pull oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime --version 1.5.0
helm push sm-realtime-1.5.0.tgz oci://my-registry.example.com/sm-charts
```

## Speechmatics license

Contact `support@speechmatics.com` for a license. The chart requires it in a secret named `speechmatics-license`.

Create the secret from your license file:

```bash
kubectl create secret generic speechmatics-license \
  --from-file=license.json=./license.json
```

Or let the chart create it. Set `global.licensing.license` to the base64-encoded contents of the license file, for example the output of `base64 < license.json | tr -d '\n'`:

```yaml
global:
  licensing:
    createSecret: true
    license: <base64-encoded license>
```

License file format and validity rules: `speechmatics:container-deployment`.

## GPU drivers

The inference server runs Nvidia Triton Server, which requires an Nvidia GPU. GPU nodes need the Nvidia device plugin so containers can access the GPUs.

Supported driver releases depend on the container version:

- Container 15.0.0 or higher: Nvidia driver release 580 or later (CUDA 13.0.1)
- Container 14.13.0 or lower: Nvidia driver release 525 or later (CUDA 12.4.1)

Device plugin installation by provider:

- AWS: [Amazon EKS Setup](https://docs.aws.amazon.com/deep-learning-containers/latest/devguide/deep-learning-containers-eks-setup.html#deep-learning-containers-eks-setup-gpu-clusters)
- Azure: [GPU Workloads on AKS](https://learn.microsoft.com/en-us/azure/aks/gpu-cluster?tabs=add-ubuntu-gpu-node-pool#nvidia-device-plugin-installation)
- GCP: [Deploy GPU workloads in GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/gpus#installing_drivers)
- Other: [Nvidia Device Plugin](https://github.com/NVIDIA/k8s-device-plugin#deployment-via-helm)

Check which nodes have allocatable GPU resources:

```bash
kubectl get nodes -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
```

Nodes without GPUs show `<none>`.
