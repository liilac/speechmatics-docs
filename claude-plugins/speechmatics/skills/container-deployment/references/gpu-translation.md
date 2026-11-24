# Translation GPU inference container

Docs: https://docs.speechmatics.com/deployments/container/gpu-translation

A GPU inference server that batch and realtime transcribers call to translate transcripts. For `translation_config` options, see `speechmatics:transcription-features`.

## Prerequisites

- Access to the Docker repository ([images-and-licensing.md](images-and-licensing.md)).
- The inference container itself needs no license. Its client, a transcriber container, must have a valid license with translation enabled.
- Transcriber version 10.3.0 or newer.

## System requirements

Same as the transcription GPU inference server except lower RAM and CPU. The translation server and the transcription server cannot use the same GPU.

- Nvidia GPU(s) with at least 16GB of GPU memory. Extra GPU memory may be used if available
- CUDA compute capability 7.5-12.1 inclusive (Turing, Ampere, Lovelace, Hopper, Blackwell). Volta or older is not supported
- 5GB RAM
- 4 vCPUs
- nvidia-container-toolkit
- Docker version > 19.03

Image size is around 10GB.

Nvidia drivers: container 15.0.0 or higher is based on CUDA 13.0.1 and needs driver release 580 or later; 14.13.0 or lower is based on CUDA 12.4.1 and needs 525 or later. Validate with `nvidia-smi`.

## Running the image

Each translation container runs on a single GPU. On a multi-GPU system select the device with `CUDA_VISIBLE_DEVICES` or `--gpus`. The gRPC endpoint is container port 8001; map it to any host port.

```bash
docker run --rm -it \
    --gpus '"device=0"' \
    -e CUDA_VISIBLE_DEVICES \
    -p 8001:8001 \
    speechmaticspublic.azurecr.io/sm-translation-inference-server:17.1.0
```

Startup logs report GPU memory:

```
Total GPU memory: 40960MiB
Approx. size models: 5GB
Available GPU memory after models loaded: 35GB
```

## Sending requests

Transcribers send the requests. Run a batch or realtime transcriber as normal and:

- Set `SM_TRANSLATION_ENDPOINT` in the transcriber to `<server_ip_address>:<port>`, where the port is the host port bound to container port 8001.
- Include `translation_config` in the job config.
- Use a license that allows translation.

### Language pairs

The server is not language specific. All 69 supported translation language pairs run on a single inference container. The source language is the language of the transcriber sending requests.

By default a request can name at most 5 target languages. Change the limit with `SM_TRANSLATION_MAX_TARGET_LANGUAGES` in the transcriber. `0` disables the limit.

### Batch example

Config:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "translation_config": {
    "target_languages": ["es", "de"]
  }
}
```

```bash
cat ~/$AUDIO_FILE | docker run -i \
    -v ~/$CONFIG_FILE:/config.json \
    -e LICENSE_TOKEN=eyJhbGciOiJ... \
    -e SM_TRANSLATION_ENDPOINT=<server>:<port> \
    batch-asr-transcriber-en:17.1.0
```

### Realtime example

Raises the allowed number of target languages to 10:

```bash
docker run -p 9000:9000 -e LICENSE_TOKEN=eyJhbGciOiJ... \
      -e SM_TRANSLATION_ENDPOINT=<server>:<port> \
      -e SM_TRANSLATION_MAX_TARGET_LANGUAGES=10 \
      rt-asr-transcriber-en:17.1.0
```

## Monitoring

The server is based on Nvidia Triton. Use Triton's Prometheus metrics or gRPC/HTTP APIs. Map port 8002 (Prometheus) or 8000 (HTTP) externally.

## Docker Compose

```yaml
---
version: '3.8'

networks:
  transcriber:
    driver: bridge

services:
  triton:
    image: speechmaticspublic.azurecr.io/sm-translation-inference-server:17.1.0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              ### Limit to N GPUs
              # count: 1
              ### Pick specific GPUs by device ID
              # device_ids:
              #   - 0
              #   - 3
              capabilities:
                - gpu
    container_name: triton
    networks:
      - transcriber
    expose:
      - 8000/tcp
      - 8001/tcp
      - 8002/tcp
    environment:
      - NVIDIA_DRIVER_CAPABILITIES=all
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
```

## Error handling

### Unsupported target language (Batch)

If a target language is not supported for the source language, the final JSON includes an error under `metadata.translation_errors`. No translation is returned for that pair.

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-05-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {...},
    "translation_config": {
      "target_languages": [
        "es",
        "zz"
      ]
    },
    "translation_errors": [
      {"type": "unsupported_translation_pair", "message": "Translation from en to zz currently not supported"}
    ],
    ...
  },
  "results": [...]
}
```

This behavior differs from the SaaS deployment.

## Performance

On a 4-core T4, translation has a real-time factor (RTF) of roughly 0.008: up to 125 hours of batch audio per hour, or 125 realtime transcription streams. Each target language counts as a stream, so one realtime stream requesting 5 target languages loads the server as much as 5 streams requesting one each.
