# Diarization and speaker identification

This file is the cross-mode overview. Configuration parameters, output shape and tuning are mode-specific:

- Batch: `speechmatics:batch-transcription` (https://docs.speechmatics.com/speech-to-text/batch/batch-diarization, https://docs.speechmatics.com/speech-to-text/batch/speaker-identification)
- Realtime: `speechmatics:realtime-transcription` (https://docs.speechmatics.com/speech-to-text/realtime/realtime-diarization, https://docs.speechmatics.com/speech-to-text/realtime/speaker-identification)

## Diarization

Docs: https://docs.speechmatics.com/speech-to-text/features/diarization

Separates a transcript into speakers or channels.

| Mode | `diarization` value | What it does | Batch | Realtime | Agent STT |
|---|---|---|---|---|---|
| Speaker diarization | `speaker` | Identifies each speaker by voice. For several speakers in one recording. | Yes | Yes | Yes |
| Channel diarization | `channel` | Transcribes each audio channel separately. For one speaker per channel. | Yes | Yes | No |
| Channel and speaker diarization | `channel_and_speaker` | Transcribes each channel separately and identifies speakers within each channel. | No | Yes | No |

`diarization` goes in `transcription_config`. Default `none`. Enum values confirmed in `spec/batch.yaml` (`none`, `speaker`, `channel`) and `spec/realtime.yaml` (adds `channel_and_speaker`).

Typical uses: contact centers (agent versus customer), video conferences, medical consultations, media production.

Related effects in other features:

- Translated sentences carry `speaker` when speaker diarization is on.
- Audio events carry `channel` when channel diarization is on.
- Disabling punctuation may slightly reduce speaker diarization accuracy.

## Speaker identification

Docs: https://docs.speechmatics.com/speech-to-text/features/speaker-identification

Available in Batch, Realtime and agent STT. Not supported by Melia 1 and Oak 1.

Tags known speakers with consistent labels across recordings using speaker identifiers: string-encoded voice representations generated from short audio samples. Providing identifiers can also improve diarization accuracy.

### Workflow

Requires speaker diarization (`"diarization": "speaker"`).

1. Enrollment. For each speaker, generate identifiers from short clips (5 to 30 seconds) where they ideally speak alone. For robustness, enroll the same speaker with several clips recorded under different acoustic conditions representative of the target audio.
2. Identification. Pass the enrolled identifiers with labels (for example `Alice`, `John`) in later transcription requests. Matching voices are tagged with those labels.

The relevant fields in `speaker_diarization_config` (both specs): `get_speakers` (boolean; return speaker identifiers at the end of the transcript) and `speakers` (labels linked to their identifiers). See the mode skills for request and response shapes.

### Limits

- Maximum 50 speaker identifiers across all speakers per session. Use as few as possible for best accuracy.
- Labels must not use reserved internal labels such as `UU`, `S1`, `S2`.
- Labels must not have leading or trailing spaces.

### Caveats

- Model-specific. Identifiers are tied to the model that generated them. Identifiers from a different model are ignored. Regenerate identifiers whenever a model is updated.
- Encrypted and scoped per customer. Identifiers cannot be shared across customers.
- Scoped per project. Identifiers cannot be used across projects under the same customer (https://docs.speechmatics.com/administration/projects).
- In every such case a warning is issued stating that the affected identifiers were ignored.

### On-prem

Batch speaker identification on-prem requires the GPU Speech to Text container (https://docs.speechmatics.com/deployments/container/gpu-speech-to-text), and you must manage speaker identification secrets yourself (https://docs.speechmatics.com/deployments/container/speaker-identification). SaaS handles both.
