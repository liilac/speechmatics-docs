# Output formatting

Docs: https://docs.speechmatics.com/speech-to-text/formatting

All settings below go inside `transcription_config`.

## Output locale

Fixes regional spelling for languages with several conventions.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "output_locale": "en-GB"
  }
}
```

| Language | Locales |
|---|---|
| English | `en-GB` (British), `en-US` (US), `en-AU` (Australian) |
| Mandarin | `cmn-Hans` (Simplified, default), `cmn-Hant` (Traditional) |

Recommended for English: without a locale, spelling may be inconsistent within one transcript.

### Multilingual models

Melia 1 and Oak 1 accept an array, one locale per language in the audio. Works in Batch and Realtime.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "melia-1",
    "language": "multi",
    "output_locale": ["en-GB", "cmn-Hans"]
  }
}
```

Each locale must belong to a different language. Two locales for the same language (`en-GB` with `en-US`) are rejected.

## Profanities

Tagged automatically for English (`en`), Italian (`it`) and Spanish (`es`):

```json
"results": [
  {
    "alternatives": [
      {
        "confidence": 1.0,
        "content": "$PROFANITY",
        "language": "en",
        "tags": [
          "profanity"
        ]
      }
    ],
    "end_time": 18.03,
    "start_time": 17.61,
    "type": "word"
  }
]
```

For other languages, use [word replacement](#word-replacement).

## Disfluencies

Hesitation sounds ("um", "uh", "hmm") are tagged automatically with `disfluency`:

```json
"results": [
  {
    "alternatives": [
      {
        "confidence": 1.0,
        "content": "hmm",
        "language": "en",
        "tags": [
          "disfluency"
        ]
      }
    ],
    "end_time": 18.03,
    "start_time": 17.61,
    "type": "word"
  }
]
```

Tagged English disfluencies:

```
huh aha ah aw eh err hmm mm um uh uh-oh uh-huh uh-uh mhm a-ha aah aahh aaw ah-ha
ahaa ahh ahha aww eeh erm hhm hhmm hm huh-uh m-hm uggh ugh ughh uhh uhhm uhm uhmm
umm uuh uuhh uum
```

### Supported languages

Tagging and removal: Arabic (`ar`), Danish (`da`), Dutch (`nl`), English (`en`), French (`fr`), German (`de`), Greek (`el`), Hebrew (`he`), Hindi (`hi`), Hungarian (`hu`), Italian (`it`), Japanese (`ja`), Mandarin (`cmn`), Polish (`pl`), Portuguese (`pt`), Russian (`ru`), Spanish (`es`).

Coverage of hesitation sounds varies by language. Test with representative audio.

### Remove disfluencies

```json
"transcription_config": {
  "model": "enhanced",
  "language": "en",
  "transcript_filtering_config": {
    "remove_disfluencies": true
  }
}
```

Default `false`. Removal also fixes capitalization and spacing: "Um, what would you like, hmm?" becomes "What would you like?".

## Word replacement

Substitutes words or patterns after transcription.

```json
"transcription_config": {
  "model": "enhanced",
  "language": "en",
  "transcript_filtering_config": {
    "replacements": [
      {"from": "foo", "to": "bar"},
      {"from": "heavy", "to": "light"}
    ]
  }
}
```

- Each rule needs `from` and `to`.
- Case-sensitive: "Foo" is not replaced by the rule above.
- Uses: censoring profanities in languages without tagging, masking sensitive values, standardizing brand names, fixing known problem words.
- To add vocabulary instead, use the custom dictionary: [custom-dictionary.md](custom-dictionary.md).

### Regex

Write `from` as a regular expression between forward slashes. Patterns use RE2 syntax (https://github.com/google/re2/wiki/Syntax) from container version 17.4.0. Earlier container versions use ECMAScript syntax.

Each rule applies to one word at a time. A pattern cannot match across two words or match punctuation marks. `^` and `$` match the start and end of the word.

In JSON, write each backslash twice (`\d` becomes `\\d`):

```javascript
// Replace "Hello" and "hello" with "goodbye"
{"from": "/(?i)^hello$/", "to": "goodbye"}

// Replace every digit in a word with "#", so "4921" becomes "####"
{"from": "/\\d/", "to": "#"}

// Add brackets around "cheese" while preserving the original word
{"from": "/(cheese)/", "to": "[$1]"}
```

#### Supported pattern syntax

| Syntax | Matches |
|---|---|
| `[abc]`, `[^abc]`, `[a-z]` | One character in, or not in, the set or range |
| `.` | Any one character, including accented and non-Latin characters |
| `\d`, `\w` | An ASCII digit, or an ASCII letter, digit, or underscore |
| `\pL`, `\p{Greek}` | Any letter in any language, or a letter in the named script |
| `^`, `$`, `\b` | Start of the word, end of the word, or a boundary between ASCII letters and other characters |
| `*`, `+`, `?`, `{2,4}` | Repeats of the previous item. Counts go up to 1000. Add `?` to match as few as possible, such as `+?` |
| `cat\|dog` | Either alternative |
| `(...)`, `(?:...)`, `(?P<name>...)` | Capturing group, non-capturing group, named capturing group |
| `(?i)` | The rest of the pattern, ignoring case. Flags go inside the pattern: `/hello/i` does not end in `/`, so it is treated as a plain word |
| `\.`, `\Q...\E` | A literal punctuation character, or the literal text between `\Q` and `\E` |

#### Replacement syntax (`to`)

| Syntax | Inserts |
|---|---|
| `$1` to `$9` | Text captured by that group, or nothing if the pattern has no such group |
| `$&` or `$0` | The whole match |
| `$$` | A literal `$` |

All other characters, including `\`, are inserted as written. Refer to a named group by its number.

#### Unsupported syntax

- Lookahead and lookbehind: `(?=...)`, `(?<!...)`
- Backreferences: `(.)\1`
- Named groups written as `(?<name>...)`. Use `(?P<name>...)`.
- `\u` escapes such as `é`. Use the character itself or `\x{e9}`.

An invalid rule, unsupported RE2 syntax, or an empty pattern (`//`) fails the request before transcription starts. The error names the rule and the reason.

#### Rule order

For each word:

1. Plain word replacements are tried first.
2. If none match, regex replacements are tried in the order listed.
3. After the first matching rule, no further rules apply to that word.
4. A regex replacement replaces every match in the word.

## Smart formatting

Converts spoken numbers, dates, currencies and other entities to written form ("nineteen ninety nine" becomes "1999"). Applied by default on all models, including Melia 1 and Oak 1.

Set `enable_entities` to `true` to also expose each entity's structure in the JSON output.

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en",
    "enable_entities": true
  }
}
```

- Default `false` per the docs page. (`spec/realtime.yaml` lists a default of `true` for the Realtime API; set the value explicitly.)
- Entity metadata appears only in JSON output. SRT and TXT are unchanged.
- Smart formatting entities are returned only by Standard and Enhanced. Melia 1 and Oak 1 format the transcript but do not return smart formatting entities or classes.
- Not supported on agent STT.
- For names, dates of birth, card numbers and other sensitive data on any model, use Entity Detection or PII Redaction: [entity-detection-and-redaction.md](entity-detection-and-redaction.md).

### Output

With `enable_entities: true`:

- `type` is `entity` for formatted entities.
- `content` holds the full written form, including spaces and symbols.
- `entity_class` describes how the entity was formatted.
- `start_time` and `end_time` span all words in the entity.
- `spoken_form`: the words as spoken, each with timing and confidence.
- `written_form`: the formatted words, separated individually.

```json
{
  "results": [
    {
      "alternatives": [
        {
          "confidence": 0.99,
          "content": "17th of January 2022",
          "language": "en",
          "speaker": "UU"
        }
      ],
      "end_time": 3.14,
      "entity_class": "date",
      "spoken_form": [
        {
          "alternatives": [
            {
              "confidence": 1.0,
              "content": "seventeenth",
              "language": "en",
              "speaker": "UU"
            }
          ],
          "end_time": 1.41,
          "start_time": 0.72,
          "type": "word"
        },
        // Additional spoken words omitted for brevity
      ],
      "start_time": 0.72,
      "type": "entity",
      "written_form": [
        {
          "alternatives": [
            {
              "confidence": 0.99,
              "content": "17th",
              "language": "en",
              "speaker": "UU"
            }
          ],
          "end_time": 1.33,
          "start_time": 0.72,
          "type": "word"
        },
        // Additional written words omitted for brevity
      ]
    }
  ]
}
```

With `enable_entities: false`, the words appear individually.

Per `spec/batch.yaml`: `written_form` word times are estimates and can be inaccurate when written order differs from spoken order ("one hundred million dollars" and "$100 million"). Written words can contain non-breaking spaces.

### Smart formatting classes

Standard and Enhanced only.

| Entity class | Description | Spoken example | Written example |
|---|---|---|---|
| `alphanum` | Alphanumeric sequences (3+ characters) | "a z triple seven five four" | AZ77754 |
| `cardinal` | Whole numbers (in English, numbers ≤10 remain as words) | "nineteen" | 19 |
| `decimal` | Numbers with decimal point | "eighteen point one two" | 18.12 |
| `fraction` | Fractions (complex ones use n/d format) | "three sixteenths" | 3/16 |
| `ordinal` | Position numbers with suffix | "forty second" | 42nd |
| `money` | Currency values with symbol | "twenty dollars" | $20 |
| `percentage` | Percentages with % symbol | "two hundred percent" | 200% |
| `date` | Calendar dates and years | "fifteenth of January twenty twenty two" | 15th of January 2022 |
| `time` | Clock times with separators | "eleven forty a m" | 11:40 a.m. |
| `span` | Ranges (x to y format) | "one hundred to two hundred million pounds" | 100 to £200 million |
| `credit card` | Payment card number sequences | "one one one one..." | 1111 2222 3333 4444 |
| `telephone` | Phone number formatting | "five five five..." | (555) 429-2228 |
| `electronic` | Email and web addresses | "bob at speechmatics dot com" | bob@speechmatics.com |
| `measurement` | Units with abbreviations | "ten kilometers per second" | 10 km/s |

Classes are chosen from context, so a value can be classified differently than expected: "2001" may be `cardinal` or `date`.

### Language conventions

| Language | Thousands | Decimal | Currency symbol |
|---|---|---|---|
| English | comma (20,000) | point (10.5) | before the value ($10) |
| German | period (20.000) | comma (10,5) | after the value, non-breaking space (10 $) |
| French | non-breaking space (20 000) | comma (10,5) | after the value, non-breaking space (10 $) |

Languages with dedicated smart formatting work: Cantonese, Dutch, English, French, German, Hindi, Italian, Japanese, Mandarin (Simplified and Traditional), Mandarin and English (bilingual), Mandarin Malay Tamil and English (multilingual), Norwegian, Portuguese, Russian, Spanish, Swedish, Tamil and English (bilingual).

Other languages format on a best-effort basis with variable results. Test with representative audio. Feature discovery does not report formatting coverage.

## Punctuation

All language packs support punctuation.

| Language | Supported marks | End-of-sentence marks | Notes |
|---|---|---|---|
| Cantonese, Mandarin | ， 。 ？ ！ 、 | 。 ？ ！ | Full-width punctuation |
| Japanese | 。 、 | 。 | Full-width punctuation |
| Hindi | । ? , ! | । ? ! | |
| All other languages | . , ! ? | . ! ? | |

### Configuration

```json
"transcription_config": {
   "model": "enhanced",
   "language": "en",
   "punctuation_overrides": {
      "permitted_marks": [".", ","],
      "sensitivity": 0.4
   }
}
```

| Field | Values | Default |
|---|---|---|
| `permitted_marks` | List of single marks, or `["all"]`. An empty list removes all punctuation. Unsupported marks are ignored. | all |
| `sensitivity` | `0` to `1`. Higher values produce more punctuation. | `0.5` |

- `punctuation_overrides` is not supported on agent STT.
- Disabling punctuation may slightly reduce speaker diarization accuracy.
- Keep punctuation at defaults when using translation.
