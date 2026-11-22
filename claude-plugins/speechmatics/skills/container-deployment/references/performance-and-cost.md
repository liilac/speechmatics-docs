# Performance and cost

Docs: https://docs.speechmatics.com/deployments/container/performance-and-cost

Benchmarks of transcription on standard Azure VMs: maximum concurrent realtime sessions (session density) and maximum batch throughput on a single instance. Use them as sizing starting points, not guarantees.

## Batch transcription

| Metric | CPU Standard | CPU Enhanced | GPU Standard | GPU Enhanced | GPU Melia 1 |
|---|---|---|---|---|---|
| Lowest processing cost (US cents per hour) | 1.7 | 3.8 | 0.34 | 1.67 | 0.19 |
| Cost vs CPU Standard | - | 224% | 20% | 98% | 11% |
| Cost vs CPU Enhanced | 45% | - | 9% | 44% | 5% |
| Cost vs GPU Standard | 500% | 1118% | - | 491% | 56% |
| Cost vs GPU Enhanced | 102% | 228% | 20% | - | 11% |
| Maximum throughput | 53.2 | 23.7 | 350 | 45 | 3600 |
| Representative real-time factor (RTF) | 0.085 | 0.2 | 0.034 | 0.120 | 0.018 |
| Job concurrency | 20 | 20 | 15 | 6 | 70 |

Definitions:

- Throughput: hours of audio per hour of runtime. A throughput of 50 means the system transcribes 50 hours of audio in one hour.
- RTF: an RTF of 1 means a one hour file takes one hour. An RTF of 0.1 means it takes six minutes. Benchmark RTFs are representative for files over 20 minutes using `parallel=4`.
- GPU job concurrency: multiple jobs are handled by a single worker configured with the required concurrency.

Benchmark configuration:

| Detail | Value |
|---|---|
| Version | 15.7.0 (Standard, Enhanced), 1.3.0 (Melia 1) |
| Language | English only |
| CPU | D16ds_v5 |
| GPU Standard | Standard_NC16as_T4_v3 |
| GPU Enhanced | Standard_NC8as_T4_v3 |
| GPU Melia 1 | Standard_NC40ads_H100_v5 |
| Price basis | Azure PAYG East US, Linux, Standard |

For GPU models, transcribers and inference servers all ran on a single VM node. Diarization was disabled.

## Realtime transcription

| Metric | CPU Standard | CPU Enhanced | GPU Standard | GPU Enhanced |
|---|---|---|---|---|
| Lowest processing cost (US cents per hour) | 1.97 | 2.95 | 0.86 | 2.51 |
| Cost vs CPU Standard | - | 150% | 44% | 127% |
| Cost vs CPU Enhanced | 67% | - | 29% | 85% |
| Session density | 40 | 24 | 140 | 30 |

GPU session density: multiple sessions are handled by a single worker configured with the required concurrency. Results reflect a fully loaded inference server at the session density recommended for the GPU platform.

Benchmark configuration:

| Detail | Value |
|---|---|
| Version | 13.4.0 |
| Language | English only |
| CPU | D16ds_v5 |
| GPU Standard | Standard_NC16as_T4_v3 |
| GPU Enhanced | Standard_NC8as_T4_v3 |
| Price basis | Azure PAYG East US, Linux, Standard |

For GPU models, transcribers and inference servers ran on a single VM node. Diarization was disabled.

Realtime transcriber resource use when linked to a GPU inference server:

- First session: 0.25 cores for both models, with 1.2 GB memory (Standard) or 3 GB memory (Enhanced).
- Each additional session: 0.1 cores and 100 MB memory.

## Translation (GPU)

On a 4-core T4, translation has an RTF of roughly 0.008. It handles up to 125 hours of batch audio per hour, or 125 realtime transcription streams. Each target language counts as a stream: one realtime stream requesting 5 target languages loads the translation server as much as 5 streams requesting one target language each.

## Per-container requirements

| Container | CPU | RAM | Other |
|---|---|---|---|
| CPU transcriber (batch or realtime) | 1 vCPU | 2-5GB (upper limit for Enhanced) | 100MB hard disk, 3GB storage, AVX |
| Batch with `--parallel=N` | N vCPUs | N times the RAM requirement | |
| Standard/Enhanced or Melia 1/Oak 1 GPU inference server | | 24 GB | Nvidia GPU with at least 16GB memory |
| Translation inference server | 4 vCPUs | 5GB | Nvidia GPU with at least 16GB memory, not shared with transcription |
| Language ID | 1 vCPU | 1 GB | AVX |
| Usage container | 1 vCPU | 1 GB | At least 1 GB persistent storage |
