# WER methodology

Source: https://docs.speechmatics.com/speech-to-text/accuracy-benchmarking

## What is needed

- A test set of audio representative of the intended use case.
- For each audio file, a perfect reference transcript produced by a human.
- For each audio file, the hypothesis transcript produced by the ASR engine.

WER compares the two to find the minimum number of edits required to make them match, the Minimum Edit or Levenshtein distance (https://en.wikipedia.org/wiki/Levenshtein_distance).

State-of-the-art ASR systems achieve below 5% on many test sets. The result depends heavily on the audio and the speakers.

## Picking the test set

Picking an appropriate test set is one of the most important parts of benchmarking.

### Audio quality

ASR performance differs significantly with:

- Background noise
- Codec (8-bit audio is lower quality)
- Cross-talk between speakers

Test sets must be representative of the use case. Contact center audio is generally much noisier and harder to transcribe than clean broadcast audio for captioning.

Librispeech (https://www.openslr.org/12) and CallHome (https://ca.talkbank.org/access/CallHome/eng.html), two commonly cited ASR test sets, frequently exhibit up to a 10% WER difference for the same engine. Librispeech is high-quality audiobook narration; CallHome is lower-quality conversational audio.

Avoid an open-source corpus for benchmarking where possible. Many ASR models are trained on data from these corpora, so results may not be representative: the models can "remember" the training data.

### Speaker diversity

Speaker characteristics also affect ASR performance significantly:

- Age
- Accent
- Gender

Some test sets provide breakdowns by ethnic background and age, such as the Casual Conversations Dataset (https://ai.meta.com/datasets/casual-conversations-dataset/) and CORAAL (https://oraal.uoregon.edu/coraal).

Across the industry, women and older people are generally recognized less easily than men and younger people. Speechmatics has published benchmarking across demographics: https://www.speechmatics.com/company/articles-and-news/achieving-accessibility-through-incredible-accuracy-with-ursa

### Dataset size

A sufficiently large dataset is needed for statistical significance when comparing WER between engines.

- Rule of thumb: at least 10,000 words, or around 1 hour of continuous speech, for each language tested.
- A chi-squared test for some competitive engines on a 5,000-word corpus would probably not show significant differences at a 95% confidence interval, whereas there might be a significant difference on a 10,000-word corpus.

## Calculating WER

WER quantifies errors in the hypothesis and expresses them as a percentage of the reference transcript's word count (`N`).

| Error | Symbol | Meaning |
|---|---|---|
| Insertion | `I` | Adding a word not in the reference to the hypothesis |
| Deletion | `D` | Removing a word present in the reference from the hypothesis |
| Substitution | `S` | Replacing a word in the reference with an incorrect word in the hypothesis |

```text
WER      = (I + D + S) / N × 100
Accuracy = 100 − WER
```

A transcript with a WER of 5% has an accuracy of 95%.

### Worked example

| | Text |
|---|---|
| Reference | The quick brown fox jumps over the lazy dog |
| Hypothesis | quick black fox jumps over the lazy brown dog |
| Diff | [deleted: The] quick [substituted: black] fox jumps over the lazy [inserted: brown] dog |

Minimum edits: 1 deletion, 1 substitution, 1 insertion.

```text
WER = (1 + 1 + 1) / 9 × 100 = 33%
```

## Normalization

Normalization minimizes differences in capitalization, punctuation, and formatting between reference and hypothesis. Do it before evaluating WER; otherwise these differences hide the real differences in word recognition accuracy.

### Formatting guidelines

Normalization is inherently language specific. Key themes:

| Normalization | Example |
|---|---|
| Convert to lowercase | "Hello, my name is Dan" -> "hello, my name is dan" |
| Replace symbols and digits with words | "my favourite number is 42" -> "my favourite number is forty-two" |
| Collapse whitespace | "hello     my name is dan" -> "hello my name is dan" |
| Expand contractions and abbreviations | "it's great to see you dr. doom" -> "it is great to see you doctor doom" |
| Standardize spellings | "colourise" -> "colorize" |
| Remove punctuation | "yeah, he went that way!" -> "yeah he went that way" |

This list is not exhaustive. Edge cases often need investigation.

### Normalization example

Two transcripts that are identical in spoken form:

| | Reference | Hypothesis |
|---|---|---|
| Raw | The Dr., who's from the US, worked part-time in London. He liked to get a £5 meal deal from Tescos for lunch. | The doctor, who is from the U.S., worked part time in London. He liked to get a five pound meal deal from Tescos for lunch! |
| Normalized | the doctor who is from the us worked part time in london he liked to get a £5 meal deal from tescos for lunch | the doctor who is from the u s worked part time in london he liked to get a £5 meal deal from tescos for lunch |

- Raw: 9 errors, WER = 9 / 22 × 100 = 41%.
- Normalized with the Speechmatics WER toolkit: 2 errors ("us" versus "u s": one substitution and one insertion), WER = 2 / 24 × 100 = 8%.

Normalization is not perfect. Always spot-check where the errors occur.

## Limitations of WER

WER remains the gold standard for measuring ASR performance, with limits:

- Reference transcripts are costly to produce. Manual transcription costs around $100 per hour.
- WER treats all errors equally. Some significantly alter sentence meaning; others are mere spelling mistakes. See https://www.speechmatics.com/company/articles-and-news/the-problem-with-word-error-rate-wer
- Punctuation, capitalization, and diarization are not measured, but matter a great deal for readability.

When reporting results, state the test set, its size, the normalization applied, and the model and config used, and review a sample of the diffs alongside the number.

## Benchmark design checklist

- Audio matches production: same channel, codec, noise, and speaking style.
- Speakers match the user population: accents, ages, genders.
- At least 10,000 words per language.
- Not drawn from an open-source corpus when avoidable.
- Human-verified references.
- Identical normalization for reference and every hypothesis.
- Same files for every engine or model compared.
- Diffs spot-checked for normalization artifacts.

## Further reading

Blogs:

- Speechmatics Ursa model benchmarking: https://www.speechmatics.com/company/articles-and-news/introducing-ursa-the-worlds-most-accurate-speech-to-text
- Achieving accessibility through incredible accuracy with Ursa: https://www.speechmatics.com/company/articles-and-news/achieving-accessibility-through-incredible-accuracy-with-ursa
- The future of Word Error Rate: https://www.speechmatics.com/company/articles-and-news/the-future-of-word-error-rate

Datasets:

- Librispeech: https://www.openslr.org/12
- CallHome: https://ca.talkbank.org/access/CallHome/eng.html
- Casual Conversations Dataset: https://ai.meta.com/datasets/casual-conversations-dataset/
- CORAAL: https://oraal.uoregon.edu/coraal

Other:

- Speech and Language Processing, chapter 2, by Jurafsky and Martin: https://web.stanford.edu/~jurafsky/slp3/2.pdf
- Speechmatics Python client: https://github.com/speechmatics/speechmatics-python
