# Helm chart configuration

Docs: https://docs.speechmatics.com/deployments/kubernetes/realtime#configuration

For every option, read the chart README (chart version current at time of writing; check the docs):

```bash
helm show readme oci://speechmaticspublic.azurecr.io/sm-charts/sm-realtime --version 1.5.0
```

Do not guess value keys beyond those shown here; check the README.

## Contents

- Defaults
- All languages on one inference server
- All languages on smaller GPUs
- English Standard and Enhanced
- Language subset
- Autoscaling
- Models
- Version selection
- Hardware

## Defaults

With default values the chart deploys an English transcriber (`rt-transcriber-en`) and an Enhanced inference server (`inference-server-enhanced-recipe1`). The minimum `values.yaml` sets the hostname:

```yaml
proxy:
  ingress:
    hostname: speechmatics.example.com
```

`proxy.ingress.url` is deprecated in favor of `proxy.ingress.hostname`. If `hostname` is not set, the chart still honors `url` as a fallback.

To pull images from your own registry, see [prerequisites.md](prerequisites.md#private-registry). Gateway API values are in [ingress-and-gateway.md](ingress-and-gateway.md).

## All languages on one inference server

Serves every language for both the Standard and Enhanced models from a single inference server. Requires a GPU with a large amount of memory, such as an L40S or H100.

```yaml
global:
  transcriber:
    languages: ["ar", "ba", "be", "bg", "bn", "ca", "cmn", "cmn_en", "cmn_en_ms_ta", "cs", "cy", "da", "de", "el", "en", "en_ms", "en_ta", "eo", "es", "es-bilingual-en", "et", "eu", "fa", "fi", "fr", "ga", "gl", "he", "hi", "hr", "hu", "ia", "id", "it", "ja", "ko", "lt", "lv", "mn", "mr", "ms", "mt", "nl", "no", "pl", "pt", "ro", "ru", "sk", "sl", "sv", "sw", "ta", "th", "tl", "tr", "ug", "uk", "ur", "vi", "yue"]

# Disable the default enhanced inference server recipe
inferenceServerEnhancedRecipe1:
  enabled: false

# Enable the all-language inference server
inferenceServerAll:
  enabled: true

  tritonServer:
    # Raise the GPU memory pool to fit all-language models.
    # Tune to the GPU you are targeting
    memoryPool:
      cudaByteSize: "8000000000"
```

## All languages on smaller GPUs

For GPUs with less memory, such as a T4, serve all languages from separate inference servers for each recipe.

```yaml
global:
  transcriber:
    languages: ["ar", "ba", "be", "bg", "bn", "ca", "cmn", "cmn_en", "cmn_en_ms_ta", "cs", "cy", "da", "de", "el", "en", "en_ms", "en_ta", "eo", "es", "es-bilingual-en", "et", "eu", "fa", "fi", "fr", "ga", "gl", "he", "hi", "hr", "hu", "ia", "id", "it", "ja", "ko", "lt", "lv", "mn", "mr", "ms", "mt", "nl", "no", "pl", "pt", "ro", "ru", "sk", "sl", "sv", "sw", "ta", "th", "tl", "tr", "ug", "uk", "ur", "vi", "yue"]

# Enable all enhanced and standard inference server recipes
inferenceServerEnhancedRecipe1:
  enabled: true

inferenceServerEnhancedRecipe2:
  enabled: true

inferenceServerEnhancedRecipe3:
  enabled: true

inferenceServerEnhancedRecipe4:
  enabled: true

inferenceServerStandardAll:
  enabled: true
```

The languages in each Enhanced recipe (language packs 1 to 4) are listed in `speechmatics:container-deployment`.

## English Standard and Enhanced

A custom inference server deployment using the English-only image, which holds both models:

```yaml
# Disable default enhanced inference server recipes
inferenceServerEnhancedRecipe1:
  enabled: false

# Enable custom inference server deployment with just en models
inferenceServerCustom:
  enabled: true
  fullnameOverride: inference-server-en
 
  tritonServer:
    image:
      # Repository for the en-only inference server triton container
      repository: sm-gpu-inference-server-en
 
  inferenceSidecar:
    enabled: true

    # Configuration for custom model deployments
    registerFeatures:
      capacity: 600
      languages: ["en"]
      model: ["standard", "enhanced"]
```

## Language subset

Deploy transcribers for selected languages and load only those languages from the inference server image, to reduce GPU memory usage and startup time:

```yaml
global:
  transcriber:
    languages: ["en", "tr"]

inferenceServerEnhancedRecipe1:
  tritonServer:
    # Load only these languages from the inference server image,
    # to reduce GPU memory usage and startup time
    languages: ["en", "tr"]
```

## Autoscaling

```yaml
global:
  # Enable scaling for all sessiongroups resources
  sessionGroups:
    scaling:
      enabled: true

inferenceServerEnhancedRecipe1:
  sessionGroups:
    scaling:
      # Scale up inference server pods when there are 300 inference tokens remaining
      scaleOnCapacityLeft: 300

transcribers:
  sessionGroups:
    scaling:
      # Scale up transcriber pods when there is only capacity for 1 more session
      scaleOnCapacityLeft: 1
```

`SessionGroups` scale transcribers and inference servers with demand and protect pods with active sessions from removal. Per the example comments, inference server capacity is counted in inference tokens and transcriber capacity in sessions. `kubectl get sessiongroups` shows the current `CAPACITY` and `USAGE` of each.

## Models

Models (previously called operating points) are configured with `model` keys in the values, for example `registerFeatures.model` on an inference server.

- `model` replaces the older `operatingPoint` keys.
- `operatingPoint` is deprecated but still works as a fallback and accepts the same `standard` and `enhanced` values.
- `operatingPoint` is removed in the next major chart version (2.0.0). Use `model`.
- If both are set, `model` takes precedence, but only when it is not empty. Setting `model: ""` does not clear an inherited `operatingPoint`.

## Version selection

When transcribers and inference servers of different versions run side by side, for example during an upgrade, the resource manager only pairs a transcriber with a compatible inference server. Configure preferred versions with `resourceManager.config.rtWorkersVersionConfig`:

```yaml
resourceManager:
  config:
    rtWorkersVersionConfig:
      legacy:
        "1": { v: "17.0.0", compatibility: major }
        "2": { v: "16.0.0", compatibility: major }
        "3": { v: "15.0.0", compatibility: major }
```

- Entries are tried in order.
- `compatibility` is `exact`, `major` (same major version) or `any`.
- `legacy` covers the `standard` and `enhanced` models.

The default shown routes any 17.x, 16.x or 15.x version, preferring 17.x. If you run a version outside this range, add it to `rtWorkersVersionConfig`.

## Hardware

Recommended Azure node sizes:

| Service | Node size |
|---|---|
| Inference server | Standard_NC4as_T4_v3 |
| Transcriber | Standard_E16s_v5 |
| All other services | Standard_D*s_v5 |
