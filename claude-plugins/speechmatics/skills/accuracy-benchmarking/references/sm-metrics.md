# The Word Error Rate toolkit (`sm-metrics`)

Source: https://docs.speechmatics.com/speech-to-text/accuracy-benchmarking#word-error-rate-toolkit

Speechmatics provides a free tool for normalization and WER calculation on a test set.

- PyPI: https://pypi.org/project/speechmatics-python/
- GitHub: https://github.com/speechmatics/speechmatics-python
- Module source: https://github.com/speechmatics/speechmatics-python/tree/master/asr_metrics/wer
- Sample reference and hypothesis files: https://github.com/speechmatics/speechmatics-python/tree/master/asr_metrics/examples

## Capabilities

- Normalize transcripts
- Calculate Word Error Rate and Character Error Rate
- Calculate the number of substitutions, deletions, and insertions for a given ASR transcript
- Visualize the alignment and differences between a reference and an ASR transcript

## Install

```bash
pip install speechmatics-python
```

Installation builds an `sm-metrics` binary for the command line.

## Usage

Compute the WER and show a transcript highlighting the difference between reference and hypothesis:

```bash
sm-metrics wer --diff <reference_path> <hypothesis_path>
```

### Input formats

Reference and hypothesis can each be:

- A plain `.txt` file containing the transcript.
- A `.dbl` file: a plain text file where each line is a file path to a `.txt` transcript file.

Example `.dbl`:

```text
/audio_transcripts/audio1_reference.txt
/audio_transcripts/audio2_reference.txt
/audio_transcripts/audio3_reference.txt
```

Use `.dbl` files to score a whole test set in one run: one `.dbl` listing the references and one listing the hypotheses.

The docs show only the `wer --diff` invocation. For other subcommands and flags (for example Character Error Rate), consult the module source or the tool's own help output rather than guessing.

## Reading the diff

The output shows the difference between reference and hypothesis at word level.

The tool merges sections with different edit types into a single highlighted section for visual clarity. This does not affect the WER calculation.

Example: the reference is "do you know morten [esperson]" and the ASR system recognizes "joe martin [espersen]". `sm-metrics` displays this as one simple substitution. The underlying WER calculation treats it as a deletion of "do you" plus a substitution of "know morten" with "joe martin".

So the number of highlighted regions in the diff can be lower than the number of counted errors. Trust the reported counts.

## End-to-end recipe

1. Collect audio and human reference transcripts. Save each reference as `<name>_reference.txt`.
2. Transcribe every audio file with the engine or model under test and save the transcript text as `<name>_hypothesis.txt`. To produce Speechmatics transcripts, use `speechmatics:batch-transcription` (or `speechmatics:realtime-transcription` when benchmarking the Realtime API). Keep the transcription config fixed across files and record it.
3. Write two `.dbl` files listing the reference paths and the hypothesis paths.
4. Run:

   ```bash
   sm-metrics wer --diff references.dbl hypotheses.dbl
   ```

5. Record WER and the insertion, deletion, and substitution counts.
6. Read the diff. Look for normalization artifacts (for example "us" versus "u s") and systematic misses such as product names.
7. Repeat steps 2 to 6 for each model or engine, using the same references.

The file names in steps 1 to 4 are illustrative; any paths work.

## Comparing Speechmatics models

Run the recipe once per `model` value. Model choice and constraints are in `speechmatics:get-started`:

- `standard` and `enhanced` take a specific `language`.
- `melia-1` and `oak-1` require `"language": "multi"`.
- Enhanced Medical is `"model": "enhanced"` with `"domain": "medical"`.

If systematic errors are domain terms, features such as custom dictionary may help on the models that support them (`speechmatics:transcription-features`). Benchmark with and without the feature and report both.

## Limits to keep in mind

- WER does not measure punctuation, capitalization, or diarization.
- All errors weigh the same regardless of their effect on meaning.
- Results from small or unrepresentative test sets do not generalize. See [wer-methodology.md](wer-methodology.md).
