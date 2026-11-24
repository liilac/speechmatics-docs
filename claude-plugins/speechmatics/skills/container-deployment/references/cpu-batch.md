# CPU batch transcriber container

Docs: https://docs.speechmatics.com/deployments/container/cpu-speech-to-text

The batch container processes one input file, writes one transcript in a predefined language, then exits. All data is transitory: the container removes all record of the operation when it finishes. For jobs over HTTP without restarts, see [batch-persistent-worker.md](batch-persistent-worker.md).

## Contents

- System requirements
- Input methods and output
- Exit codes
- Job config
- Custom images
- Parallel processing
- Multiple transcript formats
- Shared custom dictionary cache
- Linking to a GPU inference server

## System requirements

Per running container (CPU containers are split by language):

- 1 vCPU
- 2-5GB RAM (use the upper limit for the Enhanced model)
- 100MB hard disk space
- 3GB storage
- AMD or Intel CPU with modern AVX instructions
- Under a hypervisor, pass all AVX instruction sets through to the VM

With parallel processing, allow `N * RAM` where `N` is the number of vCPUs used. Two vCPUs need up to 10GB.

Input limit: 2 hours in length or 4GB in size.

## Input methods

Stream audio through STDIN:

```bash
cat ~/example.wav | docker run -i \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0
```

Or map a file to `/input.audio`:

```bash
docker run \
    -v ~/example.wav:/input.audio \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0
```

Both produce the same result. The JSON transcript is written to stdout; logs go to stderr. Intermediate files are stored in `/home/smuser/work`, whether running as root or non-root.

## Output

```json
{
  "format": "2.9",
  "metadata": {
    "created_at": "2023-08-02T15:43:50.871Z",
    "type": "transcription",
    "language_pack_info": {
      "adapted": false,
      "itn": true,
      "language_description": "English",
      "word_delimiter": " ",
      "writing_direction": "left-to-right"
    },
    "transcription_config": {
      "language": "en",
      "diarization": "none"
    }
  },
  "results": [
    {
      "alternatives": [
        {
          "confidence": 1.0,
          "content": "Are",
          "language": "en",
          "speaker": "UU"
        }
      ],
      "end_time": 3.61,
      "start_time": 3.49,
      "type": "word"
    },
    {
      "alternatives": [
        {
          "confidence": 1.0,
          "content": "on",
          "language": "en",
          "speaker": "UU"
        }
      ],
      "end_time": 3.73,
      "start_time": 3.61,
      "type": "word"
    }
  ]
}
```

For the transcript schema, see `speechmatics:batch-transcription`.

## Exit codes

- `0`: success. Output is the JSON transcript.
- Non-zero: output contains a stack trace and diagnostic information. Include it in any Support request.

Detailed codes: [troubleshooting.md](troubleshooting.md).

## Job config

Map a job config file into the container at `/config.json`:

```bash
cat ~/$AUDIO_FILE | docker run -i \
    -v ~/$CONFIG_FILE:/config.json \
    -e LICENSE_TOKEN=eyJhbGciOiJ... \
    batch-asr-transcriber-en:17.1.0
```

Or pass `--job-config <path in container>` after the image name (see [security.md](security.md)). The config can fetch audio with `fetch_data`, including `file://` URLs.

## Custom images

Build an image that uses the Speechmatics image as a layer when STDIN or volume mapping does not fit the workflow. Requirements:

- Copy the audio to `/input.audio` inside the running container.
- Start transcription by calling the `pipeline` application. It uses `/input.audio` as the source.
- Set the working directory to `/opt/orchestrator` when running `pipeline` (Dockerfile `WORKDIR`, `cd`, or similar).
- Move the transcription data out of the container when `pipeline` finishes.

```dockerfile
FROM batch-asr-transcriber-en:17.1.0
ADD download_audio.sh /usr/local/bin/download_audio.sh
RUN chmod +x /usr/local/bin/download_audio.sh
CMD ["/usr/local/bin/download_audio.sh"]
```

`download_audio.sh` is your script, for example one that pulls a file from a web server, copies it to `/input.audio`, then starts `pipeline`.

Support assumes the Speechmatics image is unmodified. Reproduce issues with the unmodified image before raising a ticket.

## Parallel processing

Pass `--parallel` to use multiple CPUs for one job:

```bash
docker run -i \
    -v ~/example.wav:/input.audio \
    batch-asr-transcriber-en:17.1.0 \
    --parallel=4
```

- Files are split into 5 minute chunks. Files shorter than 5 minutes see no parallelization.
- Optimum cores is `N / 5`, where `N` is the audio length in minutes. Higher values add little.
- Do not set `parallel` above the available cores (platform limits or the Docker `--cpu` flag). The container only uses available cores.
- The first and last processing stages cannot be parallelized, so returns diminish for large files and many cores.
- Increase the value until performance plateaus, then keep it.
- The value must be an integer of at least 1. `0` exits with code 2.
- Results vary on shared hosts.

## Multiple transcript formats

`--all-formats <dir>` (or `--allformats <dir>`) writes JSON, TXT and SRT transcripts to a directory. Mount the directory to retrieve the files:

```bash
docker run \
    -v ~/example.wav:/input.audio \
    -v ~/tmp/output:/output_dir_name \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0 \
    --all-formats /output_dir_name
```

After the run, `~/tmp/output` holds three transcripts.

## Shared custom dictionary cache

An optional cache that reduces session initialization time when the same custom dictionary is reused. The improvement applies from the second use onward. Works with batch and realtime transcribers.

Setup:

- Volume-map the cache location to `/cache`.
- Set `SM_CUSTOM_DICTIONARY_CACHE_TYPE=shared` (mandatory).
- Optionally set `SM_CUSTOM_DICTIONARY_CACHE_ENTRY_MAX_SIZE` to the maximum size in bytes of a single cached custom dictionary.
  - `10000000` allows entries up to 10MB.
  - A 1000-word list produces a cache entry of around 200 kB (200000 bytes).
  - `-1` caches every custom dictionary. This is the default.
  - A larger entry is still used for transcription but not cached.

Behavior:

- The cache volume is safe for concurrent use by multiple containers if the operating system and filesystem support file locking.
- It can hold multiple custom dictionaries in any language, including several in the same language.
- When the cache is full, the least recently used entries are removed to make room. Size the cache for the number of dictionaries you use; the docs suggest a relatively large cache, for example 50 MB, when processing multiple custom dictionaries.
- Use a Docker volume on a dedicated filesystem with a limited size. If the volume shares the host filesystem, you must purge the cache yourself.

Batch example (allows entries up to 5MB):

```bash
docker volume create speechmatics-cache

docker run -i -v /home/user/sm_audio.wav:/input.audio \
  -e SM_CUSTOM_DICTIONARY_CACHE_TYPE=shared \
  -e SM_CUSTOM_DICTIONARY_CACHE_ENTRY_MAX_SIZE=5000000 \
  -v speechmatics-cache:/cache \
  -e LICENSE_TOKEN=$TOKEN_VALUE \
  batch-asr-transcriber-en:17.1.0
```

Realtime example:

```bash
docker volume create speechmatics-cache

docker run --rm -d \
  -p 9000:9000 \
  -e SM_CUSTOM_DICTIONARY_CACHE_TYPE=shared \
  -e SM_CUSTOM_DICTIONARY_CACHE_ENTRY_MAX_SIZE=5000000 \
  -v speechmatics-cache:/cache \
  -e LICENSE_TOKEN=$TOKEN_VALUE \
  rt-asr-transcriber-en:17.1.0

speechmatics transcribe --additional-vocab gnocchi --url ws://localhost:9000/v2 --ssl-mode=none test.mp3
```

View cache entries. Each shows the language, sampling rate and checksum:

```bash
ls $(docker inspect -f "{{.Mountpoint}}" speechmatics-cache)/custom_dictionary
en,16kHz,bef53e5bcca838a39c3707f1134bda6a09ff87aaa09203617528774734455edd
```

Reduce the cache by removing entries:

```bash
rm -rf $(docker inspect -f "{{.Mountpoint}}" speechmatics-cache)/custom_dictionary/*
```

Before purging manually, ensure no container has the volume mounted, or transcription may error. Consider a temporary volume while purging.

## Linking to a GPU inference server

Run the CPU container as normal with `SM_INFERENCE_ENDPOINT` set to the gRPC endpoint of the inference server. Containers in GPU mode use less local CPU and memory, so they pack more densely on a host.

```bash
docker run \
  --rm \
  -it \
  -e SM_INFERENCE_ENDPOINT=<server>:<port> \
  -v $PWD/license.json:/license.json \
  -v $PWD/example.wav:/input.audio \
  <speech_container_image_name>
```

- At startup the container opens a TCP connection to `SM_INFERENCE_ENDPOINT`. If that fails, transcription terminates with an error.
- Batch: on a connection error during transcription, the transcriber retries for up to 60 seconds with exponential backoff. Change the period with `SM_SPLIT_RETRY_TIMEOUT` (whole seconds).
- Realtime: the transcriber retries the connection for a maximum of 250ms before giving up.

Server setup: [gpu-inference.md](gpu-inference.md).
