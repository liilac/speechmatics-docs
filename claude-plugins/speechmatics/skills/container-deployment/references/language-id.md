# Language ID container

Docs: https://docs.speechmatics.com/deployments/container/language-id

The batch language identification container predicts the most likely predominant language spoken in a media file. Use the result to select the correct transcriber when the language is unknown. For the SaaS feature, see `speechmatics:batch-transcription`.

Image: `speechmaticspublic.azurecr.io/langid:2.2.1` (current at time of writing; check the docs).

## Prerequisites

- A license file or token with language ID enabled. The docs example license lists `"features": ["MAPBA", "ALID"]`.
- Access to the Docker repository.
- An audio file with at least 60 seconds of speech in the predominant language for reliable results.

## System requirements

Per running container:

- 1 vCPU
- 1 GB RAM
- AMD or Intel CPU with modern AVX instructions; pass AVX through any hypervisor

Image size is around 2.1GB. The container uses CPU and does not run on a GPU.

## Workflow

1. Run the language ID container with an audio file.
2. Read the predicted language code from the output JSON.
3. Run transcription with that language code on any Speechmatics deployment.

## Licensing

```bash
# Volume-mapped file
docker run ... -v /my_license.json:/license.json:ro speechmaticspublic.azurecr.io/langid:2.2.1

# Environment variable holding the signedclaimstoken value
docker run ... -e LICENSE_TOKEN=eyJhbGciOiJ... speechmaticspublic.azurecr.io/langid:2.2.1
```

If both are provided, the volume-mapped file is ignored.

## Running

STDIN:

```bash
cat ~/$AUDIO_FILE | docker run -i -e LICENSE_TOKEN=eyJhbGciOiJ... speechmaticspublic.azurecr.io/langid:2.2.1
```

Mapped file. The media file must be mapped to `/input.audio`:

```bash
docker run -v $AUDIO_FILE:/input.audio -e LICENSE_TOKEN=eyJhbGciOiJ... speechmaticspublic.azurecr.io/langid:2.2.1
```

Both give the same result. The JSON result is written to STDOUT.

## Output

```json
{
  "format": "1.1",
  "metadata": {
    "created_at": "2023-08-30T10:45:27+0000",
    "type": "language_identification",
    "language_identification_config": {},
    "duration": 60.029388,
    "processed_duration": 60
  },
  "results": [
    {
      "alternatives": [
        { "language": "cs", "confidence": 0.94 },
        { "language": "sk", "confidence": 0.02 },
        { "language": "uk", "confidence": 0.02 },
        { "language": "pl", "confidence": 0.01 },
        { "language": "en", "confidence": 0 },
        { "language": "sl", "confidence": 0 },
        { "language": "el", "confidence": 0 },
        { "language": "bg", "confidence": 0 },
        { "language": "be", "confidence": 0 },
        { "language": "ru", "confidence": 0 }
      ],
      "start_time": 0,
      "end_time": 60.03
    }
  ],
  "predicted_language": "cs"
}
```

- `predicted_language`: the predicted language code.
- `results[].alternatives`: the top 10 predicted languages by confidence.
- Language codes: https://docs.speechmatics.com/speech-to-text/languages
- Not supported for language identification: Interlingua (`ia`), Esperanto (`eo`), Uyghur (`ug`), Cantonese (`yue`).

## Errors

When the language cannot be identified, the `error` field holds one of:

| `error` | Meaning | Exit code |
|---|---|---|
| `LOW_CONFIDENCE` | The language cannot be determined with sufficient confidence | |
| `UNEXPECTED_LANGUAGE` | The identified language is not in the `expected_languages` list | |
| `NO_SPEECH` | The audio contains no speech | |
| `FILE_UNREADABLE` | The file could not be read, for example an unsupported audio format | 1 |
| `OTHER` | Generic error; details in `message` | 1 |

Example with no speech:

```json
{
  "format": "1.1",
  "metadata": {
    "created_at": "2023-09-01T12:49:27+0000",
    "type": "language_identification",
    "language_identification_config": {},
    "duration": 183.913313,
    "processed_duration": 90
  },
  "results": [],
  "error": "NO_SPEECH",
  "message": "No speech found for language identification"
}
```

Exit code `0` means identification succeeded and the output holds the result. A non-zero exit code means the job failed and the output explains why; include it in any Support request.

## Expected languages

Restrict identification to a known set with `expected_languages`.

CLI argument, comma-separated:

```bash
docker run -v $AUDIO_FILE:/input.audio -e LICENSE_TOKEN=eyJhbGciOiJ... speechmaticspublic.azurecr.io/langid:2.2.1 --expected-languages cs,sk,en
```

Or a JSON config mapped to `/config.json`:

```json
{
  "type": "language_identification",
  "language_identification_config": {
    "expected_languages": ["cs", "sk", "en"]
  }
}
```

```bash
docker run -v $(pwd)/config.json:/config.json -v $AUDIO_FILE:/input.audio -e LICENSE_TOKEN=eyJhbGciOiJ... speechmaticspublic.azurecr.io/langid:2.2.1
```

## Multiple cores

```bash
docker run -v $AUDIO_FILE:/input.audio -e LICENSE_TOKEN=eyJhbGciOiJ... speechmaticspublic.azurecr.io/langid:2.2.1 --parallel=2
```

Do not set `--parallel` above the available cores. The container only uses available cores. Results vary on shared hosts.

## Limitations

- Each channel of a multichannel file cannot be identified independently. Multichannel files are converted to mono first.
- Inverted multichannel audio, where the second channel is the inverse of the first, is not supported.
- CPU only.

## Verbose logging

Run with `-vv`. Logs go to STDERR.

```bash
docker run ... speechmaticspublic.azurecr.io/langid:2.2.1 -vv
```
