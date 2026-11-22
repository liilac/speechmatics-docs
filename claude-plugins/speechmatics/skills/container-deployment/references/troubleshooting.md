# Troubleshooting containers

Docs: https://docs.speechmatics.com/deployments/container/troubleshooting

If a problem persists, enable logging and contact [Support](https://support.speechmatics.com) with the log output.

## Batch

### Enable logging

Pass `-stderr` to send logs to stderr:

```bash
docker run --rm -e SM_JOB_ID=123 -e SM_LOG_DIR=/logs \
    -v ~/$AUDIO_FILE:/input.audio \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0 \
    -stderr
```

To store logs, set:

- `SM_JOB_ID`: a job ID, for example `1`
- `SM_LOG_DIR`: the directory inside the container to write logs to, for example `/logs`

To keep the log file after the container exits, mount a host directory. Create it with the right permissions first. Example for job ID 124:

```bash
mkdir -p logs/124
sudo chown -R nobody:nogroup logs/
sudo chmod -R a+rwx logs/
```

```bash
docker run --rm -v ${PWD}/logs:/logs -e SM_JOB_ID=124 -e SM_LOG_DIR=/logs \
    -v ~/sm_audio.wav:/input.audio \
    -e LICENSE_TOKEN=$TOKEN_VALUE \
    batch-asr-transcriber-en:17.1.0

tail logs/124/sigurd.log
```

### Common errors

The container exits with a non-zero code when transcription fails. Several causes share one code, so read the logs.

| Exit code | Error | Resolution |
|---|---|---|
| 1 | `err: signal: illegal instruction` | The models could not be loaded. The Docker host needs an AVX-compatible CPU. Check the CPU flags inside the container: `docker run -it --entrypoint /bin/bash batch-asr-transcriber-en:17.1.0` then `cat /proc/cpuinfo \| grep flags` |
| 1 | `Unable to set up logging` | A directory is volume-mapped but a log file cannot be created in it. Example of mapping a writable directory: `docker run --rm -e SM_LOG_DIR=/xxx -e SM_JOB_ID=1 -v $PWD/tmp:/xxx batch-asr-transcriber-en:17.1.0` |
| 1 | `/input.audio is not valid` | Ensure a valid audio file is mapped in |
| 1 | `failed to get sample rate` | No sample rate could be read from the audio. Check the file with `ffmpeg -i /home/user/example.wav` |
| 1 | `exit status 1` | The container may be starved of memory. Verify the minimum CPU and RAM are assigned. Use `docker inspect` on the container and look for the `OOMKilled` value in its state |
| 1 | `License Error: illegal base64 data at input byte $NUMBER` | The license token was truncated or altered. Recopy the token or check the license file is not corrupt |
| 1 | `ERROR sentryserver could not load license: stat /license.json: no such file or directory` | No license file or token was passed. See [images-and-licensing.md](images-and-licensing.md) |
| 2 | `--parallel/-parallel: invalid check_parallel value: '0'` | `--parallel` needs an integer of at least 1. Valid example: `docker run -i -v /home/user/config.json:/config.json -v /home/user/example.wav:/input.audio -e LICENSE_TOKEN=$TOKEN_VALUE batch-asr-transcriber-en:17.1.0 --parallel 2` |

## Realtime

### Enable verbose logging

```bash
docker run -e DEBUG=true rt-asr-transcriber-en:17.1.0
```

### Successful startup

Check the container logs (`docker logs`). A licensed container logs something like:

```
INFO:__main__:Starting health service
INFO:orchestrator.health:Health check server starting...
INFO:__main__:Health service started.
INFO:orchestrator.license:Starting sentry server...
time="2020-03-27T11:50:18.9774596Z" level=info msg="Listening to port 52000, secure mode = false"
time="2020-03-27T11:50:18.9776369Z" level=info msg="Reading license from /license.json"
time="2020-03-27T11:50:18.9866595Z" level=info msg="Read token eyJkbGciOjJS..."
INFO:orchestrator.license:Sentry server started
time="2020-03-27T11:50:18.990334Z" level=info msg="License : licensed=true, customer=Speechmatics, contract_id=0, expires_at=2021-03-16 00:00:00 +0000 UTC, trial=false, features=MAPRT,MAPBA,AMCC,APD,APR,ASS"
time="2020-03-27T11:50:18.9904803Z" level=info msg="Starting server 3.0.0 [master]"
time="2020-03-27T11:50:18.9918058Z" level=info msg="Monitoring parent pid 1"
2020-03-27 11:50:19,005 orchestrator.transport.ws.common        INFO    Waiting for the model to be ready - checking /model/manifest.json
2020-03-27 11:50:20,673 orchestrator.transport.ws.common        INFO    Loading model en
2020-03-27 11:50:26,107 orchestrator.transport.ws.ws    INFO    transport websocket listening at ws://0.0.0.0:9000
2020-03-27 11:50:26,107 orchestrator.transport.ws.health_update INFO    Transport marked as started for health updates.
```

The `License :` line shows `licensed`, `expires_at` and the licensed `features`.

### License errors

An unlicensed container, or one with an invalid license, exits at startup with:

```
RuntimeError: Failed to launch sentry server licensing process on port 52000
```

| Log message | Cause | Fix |
|---|---|---|
| `level=error msg="could not load license file data: stat /license.json: no such file or directory"` | No license provided | Map the license file to `/license.json` or set `LICENSE_TOKEN` |
| `level=info msg="License : licensed=false, ... features="` followed by `level=error msg="Error in license : token is expired by 36h6m37s"` | License expired | Request a new license from Support. The `metadata` section of the license file shows the validity dates |
| `WARNING Sending an error to client: not_allowed - Unable to use provided configuration: No license for requested language - LEN; session ID ...` | Feature or language not licensed. Transcription is not performed | Contact Support to license the feature |
| `level=error msg="could not load license file data: unexpected end of JSON input"` | Malformed license file (volume-mapped file only) | Use the unmodified file from Support |
| `level=error msg="could not load license file data: No valid signedclaimstoken field found in license (too short)"` | Missing or damaged `signedclaimstoken` (volume-mapped file only) | The file must be valid JSON with a `signedclaimstoken` key |

### Common problems

Ensure the config object in the `StartRecognition` message is correctly formatted JSON.

## GPU inference

- Inference server unreachable at startup: the transcriber's TCP check of `SM_INFERENCE_ENDPOINT` fails and transcription terminates with an error.
- Startup fails after setting `SM_LANGUAGES`: a listed code is not in the image.
- Models fail to run: check the GPU architecture (Volta or older is unsupported) and the Nvidia driver release with `nvidia-smi`. See [gpu-inference.md](gpu-inference.md).
- Wrong mode: a server in batch mode cannot serve realtime transcribers. Set `SM_BATCH_MODE=false` (Standard/Enhanced) or `SM_STREAMING=true` (Melia 1/Oak 1).

## Usage reporting

Network failure and usage container log messages: [usage-reporting.md](usage-reporting.md).
