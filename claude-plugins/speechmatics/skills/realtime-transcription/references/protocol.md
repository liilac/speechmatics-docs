# Realtime WebSocket protocol

Docs: https://docs.speechmatics.com/api-ref/realtime-transcription-websocket

One WebSocket connection carries the whole session. Audio is sent as binary messages; every other message is a JSON object that names itself in its `message` field.

## Contents

- [Server and handshake](#server-and-handshake)
- [Message summary](#message-summary)
- [Client messages](#client-messages)
- [Server messages](#server-messages)
- [Info, Warning, and Error types](#info-warning-and-error-types)
- [Connection close](#connection-close)

## Server and handshake

- Default server: `wss://global.rt.speechmatics.com/v2` (WebSocket protocol version 13, RFC 6455). It routes each connection to the nearest region.
- Regional endpoints keep data in one region, for example `wss://eu.rt.speechmatics.com/v2`. Hosts: `eu.rt.speechmatics.com`, `us.rt.speechmatics.com`, `au.rt.speechmatics.com`.
- The connection is opened with an HTTP `GET` upgrade request.

Authentication (either one):

| Scheme | How | Use for |
| --- | --- | --- |
| API key | `Authorization: Bearer <API key>` header | Server-side connections |
| Temporary key | `jwt` query parameter, for example `wss://au.rt.speechmatics.com/v2?jwt=<temporary-key>` | Browsers, which cannot set the `Authorization` header and should not hold the long-lived API key |

A successful handshake request:

```http
GET /v2/ HTTP/1.1
Host: au.rt.speechmatics.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: ujRTbIaQsXO/0uCbjjkSZQ==
Sec-WebSocket-Version: 13
Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
Authorization: Bearer YOUR_API_KEY
User-Agent: Python/3.8 websockets/8.1
```

And its response:

```http
HTTP/1.1 101 Switching Protocols
Server: nginx/1.17.8
Date: Wed, 06 Jan 2021 11:01:05 GMT
Connection: upgrade
Upgrade: WebSocket
Sec-WebSocket-Accept: 87kiC/LI5WgXG52nSylnfXdz260=
```

| Status | Meaning |
| --- | --- |
| 101 | Switching Protocols. Connected: send `StartRecognition` to begin. |
| 400 | Bad Request. The handshake request is malformed. |
| 401 | Unauthorized. The API key or temporary key is not valid. |
| 405 | Method Not Allowed. The request method is not `GET`. |

## Message summary

Client to server:

| Message | Purpose |
| --- | --- |
| `StartRecognition` | Initiates a new recognition session. |
| `AddAudio` | A binary chunk of audio. |
| `AddChannelAudio` | Audio belonging to a specific channel (channel diarization). |
| `EndOfStream` | Declares that the client has no more audio to send. |
| `EndOfChannel` | Declares that a channel has no more audio to send. |
| `ForceEndOfUtterance` | Requests a finalized transcript followed by `EndOfUtterance`. |
| `SetRecognitionConfig` | Reconfigures the session mid-stream. |
| `GetSpeakers` | Requests detected speaker identifiers. Not supported by Melia 1 and Oak 1. |

Server to client:

| Message | Purpose |
| --- | --- |
| `RecognitionStarted` | Acknowledges `StartRecognition`; the session is ready for audio. |
| `AudioAdded` | Acknowledges an `AddAudio`. |
| `ChannelAudioAdded` | Acknowledges an `AddChannelAudio`. |
| `AddPartialTranscript` | A Partial transcript that later messages can revise. |
| `AddTranscript` | The Final transcript of part of the audio. |
| `AddPartialTranslation` | A work-in-progress translation. |
| `AddTranslation` | The final translation of part of the audio. |
| `EndOfTranscript` | Response to `EndOfStream`, after all `AddTranscript` messages are sent. |
| `AudioEventStarted` / `AudioEventEnded` | Start and end of a detected audio event. |
| `EndOfUtterance` | End of an utterance. |
| `LanguageInfo` | Word delimiter and writing direction for a detected language (Melia 1 and Oak 1 only). |
| `Info` | Additional information. |
| `Warning` | A non-fatal problem. |
| `Error` | A fatal problem. The transcription is terminated and the connection is closed. |
| `SpeakersResult` | Response to `GetSpeakers`. |

## Client messages

### StartRecognition

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"StartRecognition"` | Yes | |
| `audio_format` | object | Yes | See [configuration.md](configuration.md#audio_format). |
| `transcription_config` | object | Yes | See [configuration.md](configuration.md#transcription_config). |
| `translation_config` | object | No | See [configuration.md](configuration.md#translation_config). |
| `audio_events_config` | object | No | See [configuration.md](configuration.md#audio_events_config). |

Example with partials, translation, and audio events:

```json
{
  "message": "StartRecognition",
  "audio_format": { "type": "raw", "encoding": "pcm_f32le", "sample_rate": 16000 },
  "transcription_config": {
    "language": "en",
    "model": "enhanced",
    "output_locale": "en-US",
    "additional_vocab": ["gnocchi", "bucatini", "bigoli"],
    "diarization": "speaker",
    "max_delay": 1.0,
    "enable_partials": true
  },
  "translation_config": { "target_languages": ["es", "de"], "enable_partials": true },
  "audio_events_config": { "types": ["applause", "music"] }
}
```

### AddAudio

A binary WebSocket message (`application/octet-stream`): raw audio bytes in the encoding and sample rate given by `audio_format` in `StartRecognition`. It has no JSON envelope. The server confirms each one with `AudioAdded`.

Send audio only after `RecognitionStarted` has arrived.

### AddChannelAudio

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"AddChannelAudio"` | Yes | |
| `channel` | string | Yes | The channel identifier to which the audio belongs. |
| `data` | string | Yes | The audio data in base64 format. |

### EndOfStream

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"EndOfStream"` | Yes | |
| `last_seq_no` | integer | Yes | The schema gives no description. Its example (`312`) is captioned "No more audio after the 312th AddAudio", so send the `seq_no` of the last acknowledged audio message. |

```json
{ "message": "EndOfStream", "last_seq_no": 312 }
```

This example declares no more audio after the 312th `AddAudio`.

### EndOfChannel

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"EndOfChannel"` | Yes | |
| `channel` | string | Yes | The channel identifier. |
| `last_seq_no` | integer | Yes | Last sequence number for that channel. |

### ForceEndOfUtterance

Requests a finalized transcript followed by an `EndOfUtterance` message. Supported by Enhanced, Standard, Melia 1, and Oak 1. The client decides when to send it using its own turn detection.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"ForceEndOfUtterance"` | Yes | |
| `channel` | string | No | The channel to request a finalized transcript from. Multichannel only. |
| `timestamp` | number, minimum 0 | No | Seconds since the beginning of the audio that the request corresponds to. |

### SetRecognitionConfig

Reconfigures the session. Only the fields below can change. `language` may be included but must match the value in `StartRecognition`. Changing the language or any unlisted parameter results in an error.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"SetRecognitionConfig"` | Yes | |
| `transcription_config` | object | Yes | Mid-session config, fields below. |

| `transcription_config` field | Type | Notes |
| --- | --- | --- |
| `language` | string | Must match the original. |
| `max_delay` | number, 0.7 to 4 | Default 4. |
| `max_delay_mode` | `flexible` or `fixed` | Default `flexible`. |
| `audio_filtering_config` | object | `volume_threshold`: 0 to 100. |
| `enable_partials` | boolean | Default `false`. |
| `conversation_config` | object | `end_of_utterance_silence_trigger`: 0 to 2. |

```json
{
  "message": "SetRecognitionConfig",
  "transcription_config": { "language": "en", "max_delay": 2, "enable_partials": true }
}
```

### GetSpeakers

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"GetSpeakers"` | Yes | |
| `final` | boolean | No | Default `false`. |

- `final: false`: multiple requests can be sent during transcription, each returning the speaker identifiers generated so far. To reduce the chance of empty results, send after at least one `AddTranscript` has been received.
- `final: true`: identifiers are returned only once, at the end of the transcription, regardless of how many `final: true` requests are sent. `final: false` requests can still be sent for intermediate updates.

## Server messages

### RecognitionStarted

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"RecognitionStarted"` | Yes | |
| `orchestrator_version` | string | No | |
| `id` | string | No | |
| `language_pack_info` | object | No | See below. |
| `channel_ids` | array of string | No | Channel list for channel diarization. The realtime diarization page shows this list under the name `channels`; accept either. |

`language_pack_info`:

| Field | Type | Description |
| --- | --- | --- |
| `word_delimiter` | string | Required. The character to use to separate words. |
| `language_description` | string | Full descriptive name of the language, for example "Japanese". |
| `writing_direction` | `left-to-right` or `right-to-left` | The direction words should be written and read in. |
| `itn` | boolean | Whether inverse text normalization is available for the language pack. |
| `adapted` | boolean | Whether language model adaptation has been applied. |

```json
{
  "message": "RecognitionStarted",
  "orchestrator_version": "2025.11.07+cd4ff775c0+14.7.0",
  "id": "807670e9-14af-4fa2-9e8f-5d525c22156e",
  "language_pack_info": {
    "adapted": false,
    "itn": true,
    "language_description": "English",
    "word_delimiter": " ",
    "writing_direction": "left-to-right"
  }
}
```

### AudioAdded

| Field | Type | Required |
| --- | --- | --- |
| `message` | `"AudioAdded"` | Yes |
| `seq_no` | integer | Yes |

When clients send audio faster than real time, the server may read data slower than it is sent. If binary `AddAudio` messages exceed the server's internal buffer, the server processes other WebSocket messages until buffer space is available. `AudioAdded` is sent only after the binary data is read. This can fill TCP buffers, causing WebSocket write failures and connection closure. Monitor the WebSocket's `bufferedAmount` attribute to prevent this.

### ChannelAudioAdded

| Field | Type | Required |
| --- | --- | --- |
| `message` | `"ChannelAudioAdded"` | Yes |
| `channel` | string | Yes |
| `seq_no` | integer | Yes |

### AddTranscript and AddPartialTranscript

Both have the same structure. `AddPartialTranscript` is sent only when `transcription_config.enable_partials` is `true`, and can be superseded by later Partials until the `AddTranscript` Final for that audio is sent. On Partials, `confidence` has no meaning.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"AddTranscript"` or `"AddPartialTranscript"` | Yes | |
| `format` | string | No | JSON output format version, for example `"2.1"`. |
| `metadata` | object | Yes | `start_time`, `end_time`, `transcript` (all required). |
| `results` | array | Yes | Recognition results, below. |
| `channel` | string | No | Channel identifier. Multichannel only. |
| `forced` | boolean | No | Present, with value `true`, only when triggered by `ForceEndOfUtterance`. |

`metadata.transcript` is the whole transcript for the message as formatted text, ready to concatenate. It lacks the per-word timings and confidences found in `results`.

Each item in `results`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | `word`, `punctuation`, or `entity` | Yes | |
| `start_time` | number | Yes | Seconds. |
| `end_time` | number | Yes | Seconds. |
| `attaches_to` | `next`, `previous`, `none`, or `both` | No | How punctuation attaches to neighboring words. |
| `is_eos` | boolean | No | Whether a punctuation mark ends a sentence. |
| `alternatives` | array | No | See below. |
| `volume` | number, 0 to 100 | No | |
| `entity_class` | string | No | `entity` results only. The class the entity was formatted as, for example `date`, `money`, `number`. |
| `spoken_form` | array | No | `entity` results only. The individual words directly spoken; each item has `type` (`word` or `punctuation`), `start_time`, `end_time`, `alternatives`. |
| `written_form` | array | No | `entity` results only. The formatted entity split into words; each item has `type` (`word`), `start_time`, `end_time`, `alternatives`. |

Each item in `alternatives`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `content` | string | Yes | A word or punctuation mark. |
| `confidence` | number | Yes | 0.0 (least confident) to 1.0 (most confident). |
| `language` | string | No | Language the word is assumed to be spoken in. For `standard` and `enhanced` this is always the requested language. `melia-1` and `oak-1` detect the language per word. |
| `display` | object | No | `direction`: `ltr` or `rtl`. |
| `speaker` | string | No | Who said the word. Set only when diarization is enabled. |
| `tags` | array | No | `disfluency` and/or `profanity`. `profanity` is available in English, Spanish, and Italian. |

```json
{
  "message": "AddTranscript",
  "format": "2.1",
  "metadata": { "start_time": 1.45, "end_time": 2.2, "transcript": "Hello, world." },
  "results": [
    {
      "type": "word",
      "start_time": 1.45,
      "end_time": 1.8,
      "alternatives": [{ "content": "Hello", "confidence": 0.98, "language": "en", "speaker": "S1" }]
    },
    {
      "type": "punctuation",
      "start_time": 1.8,
      "end_time": 1.8,
      "is_eos": false,
      "attaches_to": "previous",
      "alternatives": [{ "content": ",", "confidence": 1.0, "language": "en", "speaker": "S1" }]
    },
    {
      "type": "word",
      "start_time": 1.85,
      "end_time": 2.2,
      "alternatives": [{ "content": "world", "confidence": 0.95, "language": "en", "speaker": "S1" }]
    },
    {
      "type": "punctuation",
      "start_time": 2.2,
      "end_time": 2.2,
      "is_eos": true,
      "attaches_to": "previous",
      "alternatives": [{ "content": ".", "confidence": 1.0, "language": "en", "speaker": "S1" }]
    }
  ]
}
```

### AddTranslation and AddPartialTranslation

Sent when `translation_config` is set. Partials require `translation_config.enable_partials`. See `speechmatics:transcription-features` for translation itself.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"AddTranslation"` or `"AddPartialTranslation"` | Yes | |
| `format` | string | No | JSON output format version. |
| `language` | string | Yes | Target language of the translation, as an ISO language code. |
| `results` | array | Yes | Translated sentences. |

Each item in `results`:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `content` | string | Yes | Translated text. |
| `start_time` | number | Yes | Start (seconds) of the original transcribed audio segment. |
| `end_time` | number | Yes | End (seconds) of the original transcribed audio segment. |
| `speaker` | string | No | The speaker, if speaker diarization is enabled. |

Translation messages do not include the `channel` property.

### EndOfTranscript

```json
{ "message": "EndOfTranscript" }
```

Sent in response to `EndOfStream`, after the server has finished sending all `AddTranscript` messages.

### EndOfUtterance

Indicates the end of an utterance, triggered by a configured period of non-speech or by a client-sent `ForceEndOfUtterance`. Like punctuation, it has zero duration.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"EndOfUtterance"` | Yes | |
| `metadata` | object | Yes | `start_time` and `end_time`: the time (seconds) the end of utterance was detected. |
| `channel` | string | No | Multichannel only. |
| `forced` | boolean | No | Present, with value `true`, only when triggered by `ForceEndOfUtterance`. |

### LanguageInfo

Sent only by `melia-1` and `oak-1`, once per language code, immediately before that language first appears in an `AddPartialTranscript` or `AddTranscript`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"LanguageInfo"` | Yes | |
| `language` | string | Yes | The detected language code. |
| `word_delimiter` | string | Yes | Delimiter to place between words of this language. |
| `writing_direction` | `left-to-right` or `right-to-left` | Yes | |
| `partial` | boolean | No | Present only when `true`: a Partial transcript triggered the message. |

### AudioEventStarted and AudioEventEnded

Sent when `audio_events_config` is set.

| Message | Field | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `AudioEventStarted` | `event.type` | string | Yes | The audio event type. |
| | `event.start_time` | number | Yes | Time (seconds) of the beginning of the event. |
| | `event.confidence` | number, 0 to 1 | Yes | Confidence score. |
| | `channel` | string | No | Multichannel only. |
| `AudioEventEnded` | `event.type` | string | Yes | The audio event type. |
| | `event.end_time` | number | Yes | |
| | `channel` | string | No | Multichannel only. |

### SpeakersResult

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"SpeakersResult"` | Yes | |
| `speakers` | array | Yes | Each item: `label` (string, required) and `speaker_identifiers` (array of unique strings, at least one, required). |

```json
{
  "message": "SpeakersResult",
  "speakers": [
    {"label": "S1", "speaker_identifiers": ["<id1>"]},
    {"label": "S2", "speaker_identifiers": ["<id2>"]}
  ]
}
```

## Info, Warning, and Error types

All three share `message`, `type`, and `reason` (required), plus optional `code` (integer) and `seq_no` (integer).

### Info

| `type` | Meaning | Extra fields |
| --- | --- | --- |
| `recognition_quality` | Which quality-based model handles the recognition. Sent immediately after the WebSocket handshake completes. | `quality`: `telephony` or `broadcast`. Selected automatically: broadcast for high-quality audio (12 kHz and above), telephony for lower quality audio. |
| `concurrent_session_usage` | The concurrent session quota and how much is in use. Sent immediately after the WebSocket handshake completes. | `usage` (active concurrent sessions), `quota` (maximum allowed), `last_updated` (`YYYY-MM-DDTHH:MM:SSZ`, UTC; may be empty or outdated), `region` (for example `eu`). |

### Warning

| `type` | Meaning |
| --- | --- |
| `duration_limit_exceeded` | The maximum allowed duration of a single utterance has been exceeded. Further `AddAudio` messages are confirmed with `AudioAdded` but ignored by the engine. This triggers the same mechanism as `EndOfStream`, so the server eventually sends `EndOfTranscript`. Extra field `duration_limit` (seconds). |
| `unsupported_translation_pair` | A requested translation target language is unsupported for the source language. The message names the pair. |
| `idle_timeout` | The session is approaching the idle limit (no audio in the last hour). `reason`: `Session will timeout in {time_remaining}m due to inactivity, no audio sent within the last {time_elapsed}m`. Sent 15, 10, and 5 minutes before timeout. |
| `session_timeout` | The session is approaching the 48-hour maximum. `reason`: `Session will timeout in {time_remaining}m due to max duration, session has been active for {time_elapsed}m`. Sent 45, 30, and 15 minutes before timeout. |
| `empty_translation_target_list` | No supported translation target languages specified. Translation will not run. |
| `add_audio_after_eos` | Audio was sent after `EndOfStream`. It is ignored. |
| `speaker_id` | A speaker identification related issue. |

### Error

After any error, the transcription is terminated and the connection is closed. `invalid_message`, `protocol_error`, and `unknown_error` can be triggered in response to any message.

| `type` | Meaning |
| --- | --- |
| `invalid_message` | The message received was not understood. |
| `invalid_model` | Unable to use the model for the recognition. The language is not supported at all, or is not available for the user. |
| `invalid_language` | The requested language is not valid or is not supported. |
| `invalid_config` | The config contains wrong or unsupported fields, or too many translation target languages were requested. |
| `invalid_audio_type` | Audio type is not supported, is deprecated, or is malformed. |
| `invalid_output_format` | Output format is not supported, is deprecated, or is malformed. |
| `not_authorised` | User was not recognized, or the API key is not valid. |
| `not_allowed` | User is not allowed to perform the action the message would invoke. |
| `job_error` | Unable to do any work on this job (for example a server timeout). Also returned if the server cannot process audio as fast as it is sent and the backlog grows too large. |
| `protocol_error` | The message was syntactically correct but could not be accepted due to protocol limitations, usually messages sent in the wrong order. |
| `quota_exceeded` | Maximum number of concurrent connections allowed for the contract has been reached. |
| `timelimit_exceeded` | Usage quota for the contract has been reached. |
| `idle_timeout` | Idle limit reached (no audio in the last hour). A closing handshake with code `1008` follows. |
| `session_timeout` | Maximum session duration (48 hours) reached. A closing handshake with code `1008` follows. |
| `unknown_error` | An error that did not fit any type above. |

```json
{
  "message": "Error",
  "type": "invalid_model",
  "reason": "We are not able to serve the requested language: xx"
}
```

## Connection close

An `Error` message can be followed by a WebSocket close frame. Close codes do not map one-to-one onto `Error` types.

| Close code | Reason |
| --- | --- |
| 1003 | `protocol_error` |
| 1008 | `policy_violation` |
| 1011 | `internal_error` |
| 4001 | `not_authorised` |
| 4003 | `not_allowed` |
| 4004 | `invalid_model` |
| 4005 | `quota_exceeded` |
| 4006 | `timelimit_exceeded` |
| 4013 | `job_error` |

For `4005`, `4013`, and `1011` only, retry after at least 5–10 seconds.

Sessions also close when they idle or run too long. See [limits-and-errors.md](limits-and-errors.md).
