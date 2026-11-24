# GPU inference servers

Docs:

- Standard and Enhanced: https://docs.speechmatics.com/deployments/container/gpu-speech-to-text
- Melia 1 and Oak 1: https://docs.speechmatics.com/deployments/container/gpu-speech-to-text-multilingual

A GPU inference server lets multiple transcriber containers offload inference to a GPU, where it is batched and parallelized. Transcribers stay on CPU and point at the server with `SM_INFERENCE_ENDPOINT`.

## Contents

- System requirements and drivers
- Standard and Enhanced server
- Melia 1 and Oak 1 server
- Monitoring
- Docker Compose files

## System requirements

Both server families require:

- Nvidia GPU(s) with at least 16GB of GPU memory
- Nvidia drivers (versions below)
- CUDA compute capability 7.5-12.1 inclusive: Turing, Ampere, Lovelace, Hopper, Blackwell architectures. Volta or older cannot run the models
- 24 GB RAM
- The [nvidia-container-toolkit](https://github.com/NVIDIA/nvidia-docker)
- Docker version > 19.03

The Standard/Enhanced server image is around 15GB.

### Nvidia drivers

| Server | Container version | CUDA base | Nvidia driver release |
|---|---|---|---|
| Standard/Enhanced | 15.0.0 or higher | 13.0.1 | 580 or later |
| Standard/Enhanced | 14.13.0 or lower | 12.4.1 | 525 or later |
| Melia 1/Oak 1 | All | 13.0.1 | 580 or later |

Validate the driver with `nvidia-smi`. It returns the driver version and GPU details. GPU nodes can be provisioned in the cloud.

### GPU selection

Each inference server container runs on a single GPU. On a multi-GPU system, specify the device with `CUDA_VISIBLE_DEVICES` or the `--gpus` argument.

No GPU-specific license exists. The server runs with an existing Batch or Realtime container license. (The Melia 1 and Oak 1 page names only the Batch container license, although it also documents Realtime.)

## Standard and Enhanced server

```bash
docker run --rm -it \
    -v $PWD/license.json:/license.json \
    --gpus '"device=0"' \
    -e CUDA_VISIBLE_DEVICES \
    -p 8001:8001 \
    speechmaticspublic.azurecr.io/sm-gpu-inference-server-en:17.1.0
```

Ready when the model table shows `READY` and the services start:

```
I1215 11:43:57.300390 1 server.cc:633]
+----------------------+---------+--------+
| Model                | Version | Status |
+----------------------+---------+--------+
| am_en_enhanced       | 1       | READY  |
| am_en_standard       | 1       | READY  |
| body_enhanced        | 1       | READY  |
| body_standard        | 1       | READY  |
| diar_enhanced        | 1       | READY  |
| diar_standard        | 1       | READY  |
| ensemble_en_enhanced | 1       | READY  |
| ensemble_en_standard | 1       | READY  |
| lm_en_enhanced       | 1       | READY  |
+----------------------+---------+--------+
...
I1215 11:43:57.375233 1 grpc_server.cc:4819] Started GRPCInferenceService at 0.0.0.0:8001
I1215 11:43:57.375473 1 http_server.cc:3477] Started HTTPService at 0.0.0.0:8000
I1215 11:43:57.417749 1 http_server.cc:184] Started Metrics Service at 0.0.0.0:8002
```

### Batch or realtime mode

The server runs in batch mode (whole files) by default. For realtime, pass `SM_BATCH_MODE=false` to `docker run`. A server supports one mode at a time. Match the client image:

- `rt-asr-transcriber-en:<version>` with a realtime-mode server
- `batch-asr-transcriber-en:<version>` with a batch-mode server

### Linking a transcriber

Run the CPU transcriber with `SM_INFERENCE_ENDPOINT=<server>:<port>`. See [cpu-batch.md](cpu-batch.md#linking-to-a-gpu-inference-server) for the command and retry behavior.

### Running only one model

To save GPU memory for throughput, load one model with `SM_MODEL` set to `standard` or `enhanced`.

- `SM_MODEL` replaces `SM_OPERATING_POINT`, which is deprecated but still works with the same values.
- On the all-language Standard image (`sm-gpu-inference-server-standard-all`) you must set `SM_MODEL=standard`.

### Loading only selected languages

Multi-language images load every language at startup. Set `SM_LANGUAGES` to a comma-separated list to load a subset:

```bash
# load only English, German, and French
-e SM_LANGUAGES=en,de,fr
```

- Codes must be languages the image contains. Any other code fails startup with an error.
- Unset means all languages load.
- Available from container version 15.18.0.
- Combine with `SM_MODEL`: `SM_MODEL=standard` with `SM_LANGUAGES=en,de` loads the Standard model for English and German only.

### GPU models

GPU inference uses GPU-specific models, also named `standard` and `enhanced`. Results are not identical to CPU-based inference.

## Melia 1 and Oak 1 server

Melia 1 and Oak 1 are multilingual, GPU-only models. Oak 1 is tuned for healthcare audio. Both run on the same transcriber and inference server images.

```bash
docker run --rm -it \
    -v $PWD/license.json:/license.json \
    --gpus '"device=0"' \
    -e CUDA_VISIBLE_DEVICES \
    -p 8001:8001 \
    speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0
```

Ready output in batch mode:

```
+--------------+---------+--------+
| Model        | Version | Status |
+--------------+---------+--------+
| aed          | 1       | READY  |
| body         | 1       | READY  |
| detokenizer  | 1       | READY  |
| dz           | 1       | READY  |
| ensemble     | 1       | READY  |
| preprocessor | 1       | READY  |
+--------------+---------+--------+
...
"Started GRPCInferenceService at 0.0.0.0:8001"
"Started HTTPService at 0.0.0.0:8000"
"Started Metrics Service at 0.0.0.0:8002"
```

The server runs in Batch (default) or Realtime mode, one at a time. The transcriber does not need a GPU and uses one image for both modes: set `SM_ASR_MODE` to `batch` or `rt`.

### Selecting a model

```json
{
  "transcription_config": {
    "model": "oak-1",
    "language": "multi"
  }
}
```

`model` is `melia-1` or `oak-1`. `language` must be `multi`.

### Batch inference

```bash
docker run --rm -it \
  -e SM_INFERENCE_ENDPOINT=<server>:<port> \
  -e SM_ASR_MODE=batch \
  -v $PWD/license.json:/license.json \
  -v $PWD/example.wav:/input.audio \
  speechmaticspublic.azurecr.io/sm-asr-transcriber:1.13.0
```

To accept multiple jobs over HTTP without restarting, run the transcriber as a [batch persistent worker](batch-persistent-worker.md).

### Realtime inference

Requires container version 1.13.0 or later. Start the server with `SM_STREAMING=true`:

```bash
docker run --rm -it \
    -v $PWD/license.json:/license.json \
    --gpus '"device=0"' \
    -e CUDA_VISIBLE_DEVICES \
    -e SM_STREAMING=true \
    -p 8001:8001 \
    speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0
```

Ready output lists the streaming models:

```
+--------------------+---------+--------+
| Model              | Version | Status |
+--------------------+---------+--------+
| aed                | 1       | READY  |
| body               | 1       | READY  |
| preprocessor       | 1       | READY  |
| streaming          | 1       | READY  |
| streaming_ensemble | 1       | READY  |
+--------------------+---------+--------+
```

Then run the transcriber:

```bash
docker run --rm -it \
  -e SM_INFERENCE_ENDPOINT=<server>:<port> \
  -e SM_ASR_MODE=rt \
  -v $PWD/license.json:/license.json \
  -p 9000:9000 \
  speechmaticspublic.azurecr.io/sm-asr-transcriber:1.13.0
```

Connect over WebSocket as for the CPU realtime container ([cpu-realtime.md](cpu-realtime.md)) and select the model in the `StartRecognition` message. For supported Realtime features, see https://docs.speechmatics.com/speech-to-text/models#melia-1-and-oak-1-on-realtime.

By default the transcriber accepts one WebSocket connection. Set `SM_MAX_CONCURRENT_CONNECTIONS` for more. `/ready` then returns true while a connection is free. CPU usage scales with active sessions; most memory is shared.

## Monitoring

All inference servers are based on Nvidia Triton. Monitor with Triton's Prometheus metrics or its gRPC/HTTP APIs. Map port 8002 (Prometheus) or 8000 (HTTP) externally to expose them.

## Docker Compose files

All assume `license.json` is in the current working directory.

### Standard and Enhanced inference server

```yaml
version: "3.8"

networks:
  transcriber:
    driver: bridge

services:
  triton:
    image: speechmaticspublic.azurecr.io/sm-gpu-inference-server-en:17.1.0
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
    volumes:
      - $PWD/license.json:/license.json:ro
```

### Melia 1 and Oak 1, Realtime

```yaml
version: "3.8"

networks:
  transcriber:
    driver: bridge

services:
  triton:
    image: speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0
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
      - SM_STREAMING=true
    volumes:
      - $PWD/license.json:/license.json:ro
  transcriber:
    image: speechmaticspublic.azurecr.io/sm-asr-transcriber:1.13.0
    networks:
      - transcriber
    ports:
      - 9000:9000
    environment:
      - SM_INFERENCE_ENDPOINT=triton:8001
      - SM_MAX_CONCURRENT_CONNECTIONS=1
      - SM_ASR_MODE=rt
    volumes:
      - $PWD/license.json:/license.json:ro
```

### Melia 1 and Oak 1, batch persistent worker

```yaml
version: "3.8"

networks:
  transcriber:
    driver: bridge

services:
  triton:
    image: speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0
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
    volumes:
      - $PWD/license.json:/license.json:ro
  transcriber:
    image: speechmaticspublic.azurecr.io/sm-asr-transcriber:1.13.0
    networks:
      - transcriber
    ports:
      - 18000:18000
    environment:
      - SM_INFERENCE_ENDPOINT=triton:8001
      - SM_ASR_MODE=batch
    command: --run-mode http --parallel=10
    volumes:
      - $PWD/license.json:/license.json:ro
```

A server-only variant for Melia 1 and Oak 1 is the first file with the image `speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0`.
