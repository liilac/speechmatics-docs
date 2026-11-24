---
name: accuracy-benchmarking
description: Measures and benchmarks Speechmatics Speech to Text accuracy with Word Error Rate (WER). Covers choosing a representative test set, reference and hypothesis transcripts, the WER formula (insertions, deletions, substitutions), transcript normalization, the `sm-metrics` command-line tool from the `speechmatics-python` package (`sm-metrics wer --diff`, `.dbl` file lists, Character Error Rate), and the limits of WER. Also covers app analytics with the `sm-app` query parameter for applications where users supply their own API key. Use when asked to evaluate, compare, or benchmark transcription accuracy, calculate WER or CER, normalize transcripts before scoring, compare Speechmatics models or other ASR engines, or track per-application usage with an application ID.
---

# Accuracy benchmarking

Word Error Rate (WER) is the standard metric for benchmarking transcription accuracy. It compares a human-made reference transcript with the hypothesis transcript an Automatic Speech Recognition (ASR) engine produced.

Docs: https://docs.speechmatics.com/speech-to-text/accuracy-benchmarking

## When to use another skill

- Producing the hypothesis transcripts: `speechmatics:batch-transcription` or `speechmatics:realtime-transcription`.
- Choosing which model to benchmark (`standard`, `enhanced`, `melia-1`, `oak-1`): `speechmatics:get-started`.
- Improving accuracy with custom dictionary, output locale, or diarization: `speechmatics:transcription-features`.
- Workspace usage and billing: `speechmatics:account-administration`.

## Workflow

1. Build a test set representative of the real use case: same audio quality, codecs, noise, accents, and speakers.
2. Size it for significance: at least 10,000 words, or around 1 hour of continuous speech, per language tested.
3. Get a perfect human reference transcript for every audio file, as plain `.txt`.
4. Transcribe each file with every engine or model under test and save each hypothesis as plain `.txt`.
5. Normalize reference and hypothesis the same way.
6. Compute WER, then spot-check the diff to see where errors occur.

## Formula

```text
WER      = (I + D + S) / N × 100
Accuracy = 100 − WER
```

- `I` insertions: a word in the hypothesis that is not in the reference.
- `D` deletions: a word in the reference missing from the hypothesis.
- `S` substitutions: a reference word replaced by an incorrect word.
- `N`: word count of the reference transcript.

The edit count is the minimum number of edits needed to make the two transcripts match (the Levenshtein distance). A WER of 5% means an accuracy of 95%.

Example:

| Reference | Hypothesis |
|---|---|
| The quick brown fox jumps over the lazy dog | quick black fox jumps over the lazy brown dog |

1 deletion ("The"), 1 substitution ("brown" to "black"), 1 insertion ("brown"): `(1 + 1 + 1) / 9 × 100 = 33%`.

## Normalize before scoring

Normalization removes differences in capitalization, punctuation, and formatting so WER reflects word recognition only. It is language specific.

| Normalization | Example |
|---|---|
| Convert to lowercase | "Hello, my name is Dan" to "hello, my name is dan" |
| Replace symbols and digits with words | "my favourite number is 42" to "my favourite number is forty-two" |
| Collapse whitespace | "hello     my name is dan" to "hello my name is dan" |
| Expand contractions and abbreviations | "it's great to see you dr. doom" to "it is great to see you doctor doom" |
| Standardize spellings | "colourise" to "colorize" |
| Remove punctuation | "yeah, he went that way!" to "yeah he went that way" |

In the docs' worked example, the same pair of transcripts scores 41% WER raw (9 errors over 22 words) and 8% after normalization (2 errors over 24 words). Never compare engines on raw transcripts.

## Compute WER with `sm-metrics`

Speechmatics publishes a free toolkit that normalizes transcripts, calculates WER and Character Error Rate (CER), counts substitutions, deletions, and insertions, and visualizes the alignment between reference and hypothesis.

Install:

```bash
pip install speechmatics-python
```

This installs the `sm-metrics` command. Compute WER and print a diff of reference against hypothesis:

```bash
sm-metrics wer --diff <reference_path> <hypothesis_path>
```

Each path is either a plain `.txt` transcript or a `.dbl` file: a plain text file where each line is a path to a `.txt` transcript.

```text
/audio_transcripts/audio1_reference.txt
/audio_transcripts/audio2_reference.txt
/audio_transcripts/audio3_reference.txt
```

- Package: https://pypi.org/project/speechmatics-python/
- Module source: https://github.com/speechmatics/speechmatics-python/tree/master/asr_metrics/wer
- Sample reference and hypothesis files: https://github.com/speechmatics/speechmatics-python/tree/master/asr_metrics/examples

For flags beyond `wer --diff`, read the module source or run the tool's help. Do not invent options.

## Gotchas

- Avoid open-source corpora (for example Librispeech, CallHome) where possible. Many ASR models are trained on them, so results may not be representative.
- Test sets differ widely: Librispeech and CallHome frequently show up to a 10% WER difference for the same engine.
- A 5,000-word corpus would probably not show significant differences between competitive engines at a 95% confidence interval; 10,000 words might.
- The `--diff` output merges adjacent sections with different edit types into one highlighted section for readability. This does not change the WER number.
- Normalization is not perfect. In the docs' example "US" versus "U.S." still counts as 2 errors after normalization. Spot-check.
- WER treats all errors equally and does not measure punctuation, capitalization, or diarization. Accuracy as a reader experiences it is broader than WER.
- Use the same normalization, the same reference, and the same audio for every engine compared.
- Order matters: reference path first, hypothesis path second.

## App analytics

If an application lets users enter their own Speechmatics API key, Speechmatics can provide aggregated analytics about those users' usage: number of unique users, hours processed, languages used, and more. Contact support (https://support.speechmatics.com) to get set up, then tag requests with the `sm-app` query parameter.

Batch:

```bash
curl -L -X POST "https://eu1.asr.api.speechmatics.com/v2/jobs/?sm-app=${APP_ID}" \
    -H "Authorization: Bearer ${API_KEY}" \
    -F data_file=@${PATH_TO_FILE} \
    -F config='{"type": "transcription","transcription_config": { "model": "enhanced","language": "en" }}'
```

Realtime:

```text
wss://eu.rt.speechmatics.com/v2?sm-app=YourAppID
```

Docs: https://docs.speechmatics.com/speech-to-text/app-analytics

## References

- [references/wer-methodology.md](references/wer-methodology.md): test set selection (audio quality, speaker diversity, dataset size), the full normalization example, limitations, datasets, and further reading. Read when designing a benchmark or explaining results.
- [references/sm-metrics.md](references/sm-metrics.md): toolkit capabilities, input formats, how to read the diff output, and an end-to-end benchmarking recipe. Read when running the numbers.
- [references/app-analytics.md](references/app-analytics.md): `sm-app` setup and complete examples. Read when adding an application ID to requests.
