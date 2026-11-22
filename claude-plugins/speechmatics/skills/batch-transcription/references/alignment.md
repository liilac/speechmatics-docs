# Alignment

Docs: https://docs.speechmatics.com/speech-to-text/batch/alignment

Submit an audio file and a text file, and get back the timing of each word in the text.

## Check availability first

- Alignment requires access. Contact Support (https://support.speechmatics.com) or your Account Manager.
- The alignment page is not linked in the Batch docs sidebar, and the current Batch API spec lists `transcription` as the only job `type` and does not define the `/alignment`, `/text`, or `/data` endpoints. Everything below comes from the alignment docs page only. Confirm with Support that alignment is enabled for the account before building on it.

## Input text

- The text file must be UTF-8 encoded plain text. Characters outside this format cause the job to be rejected.
- Any string of characters separated by whitespace (space, tab, newline) is a word.
- SGML-like markup is treated as comments and ignored: text inside `<!--` `-->` or inside `<` `>`.

Given:

```
Hello <markup> world <!-- comment > comment --> how are you?
```

These words are aligned:

```
Hello world how are you?
```

## Submit a job

`POST /v2/jobs` with these form fields. All three inputs are required, or the job is rejected.

| Form field | Content |
|---|---|
| `config` | The job config for alignment |
| `data_file` | The media file containing the speech. Can instead be given in `config` with `fetch_data` |
| `text_file` | The text file containing the transcript. Can instead be given in `config` with `fetch_text` |

The config states the `alignment` type and the language of the audio and text:

```json
{
  "type": "alignment",
  "alignment_config": {
    "language": "en"
  }
}
```

### Fetch inputs from URLs

```json
{
  "type": "alignment",
  "fetch_data": { "url": "$MY_AUDIO_URL" },
  "fetch_text": { "url": "$MY_TRANSCRIPT" },
  "alignment_config": { "language": "en" }
}
```

You can upload one input and fetch the other. Do not provide the same input both as an uploaded file and through `fetch_data` or `fetch_text`; the job fails.

## Retrieve the result

Check status the same way as for transcription jobs (`GET /v2/jobs/{jobid}`).

| Endpoint | Returns |
|---|---|
| `GET /v2/jobs/<JOB_ID>/alignment` | The aligned text. `tags` query parameter selects the format |
| `GET /v2/jobs/<JOB_ID>/text` | The text file submitted |
| `GET /v2/jobs/<JOB_ID>/data` | The audio file submitted |

```bash
curl -X GET "https://eu1.asr.api.speechmatics.com/v2/jobs/${JOB_ID}/alignment?tags=one_per_line" \
    -H "Authorization: Bearer ${API_KEY}"
```

### Output formats

`word_start_and_end` (default):

```
<time=0.12>Hello<time=0.23> <markup> <time=0.34>world<time=0.45> <!-- comment > comment -->
<time=0.56>how<time=0.67> <time=0.78>are<time=0.89> <time=0.90>you?<time=1.00>
```

`one_per_line` (request with `tags=one_per_line`):

```
[00:00:00.1] Hello <markup> world <!-- comment > comment --> how are you?
```

## Notifications

Include `notification_config` in the job config. Allowlist the Speechmatics egress IPs; see [notifications.md](notifications.md).

```json
{
  "type": "alignment",
  "alignment_config": {
    "language": "en"
  },
  "notification_config": [
    {
      "contents": ["alignment"],
      "url": "https://lorem.ipsum/"
    },
    {
      "contents": ["alignment.one_per_line", "text"],
      "method": "post",
      "url": "https://dolor.sit.amet/"
    }
  ]
}
```

Supported `contents` for alignment jobs:

| Value | Content |
|---|---|
| `alignment`, `alignment.one_per_line`, `alignment.word_start_and_end` | The aligned transcript |
| `text` | The non-aligned transcript submitted with the job |
| `data` | The media file submitted with the job |
| `jobinfo` | Summary information about the job |

## Data retention

Alignment follows the same 7-day data retention as transcription.
