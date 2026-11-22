# Agent STT WebSocket API reference

Docs: https://docs.speechmatics.com/api-ref/agent-stt-websocket

One WebSocket connection carries a conversation. Open the connection, send `StartRecognition`, then stream audio as binary messages. Every other message is a JSON object that names itself in its `message` field.

## Contents

- [Server and handshake](#server-and-handshake)
- [Message summary](#message-summary)
- [StartRecognition](#startrecognition)
- [Other client messages](#other-client-messages)
- [Server messages](#server-messages)
- [Info, Warning, and Error types](#info-warning-and-error-types)
- [Connection close](#connection-close)
- [Differences from the Realtime API](#differences-from-the-realtime-api)

## Server and handshake

- Default server: `wss://global.rt.speechmatics.com/v2/agent` (WebSocket protocol version 13, RFC 6455). Routes each connection to the nearest region for the lowest latency.
- To keep data in one region, connect to that region's endpoint, such as `wss://eu.rt.speechmatics.com/v2/agent`. Hosts: `eu.rt.speechmatics.com`, `us.rt.speechmatics.com`, `au.rt.speechmatics.com`.
- The connection is opened with an HTTP `GET` upgrade request.

Authentication (either one):

| Scheme | How | Use for |
| --- | --- | --- |
| API key | `Authorization: Bearer <API key>` header | Server-side connections |
| Temporary key | `jwt` query parameter, for example `wss://global.rt.speechmatics.com/v2/agent?jwt=<temporary-key>` | Browsers, which cannot set the `Authorization` header and should not hold the long-lived API key. Use a Realtime (`type=rt`) temporary key. |

A successful handshake request:

```http
GET /v2/agent HTTP/1.1
Host: eu.rt.speechmatics.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: ujRTbIaQsXO/0uCbjjkSZQ==
Sec-WebSocket-Version: 13
Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits
Authorization: Bearer YOUR_API_KEY
User-Agent: Python/3.12 websockets/15.0
```

And its response:

```http
HTTP/1.1 101 Switching Protocols
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
| `AddAudio` | A binary chunk of audio. The server confirms receipt with `AudioAdded`. |
| `EndOfStream` | Declares that the client has no more audio to send. |
| `SetRecognitionConfig` | Reconfigures the session. |
| `GetSpeakers` | Requests any detected speaker identifiers. |
| `ForceEndOfUtterance` | Closes the current speaker turn. `external` mode only. |

Server to client:

| Message | Purpose |
| --- | --- |
| `RecognitionStarted` | Acknowledges `StartRecognition`. |
| `AudioAdded` | Acknowledges an `AddAudio`. |
| `AddPartialSegment` | An interim, best-guess preview of the segment being built. Subject to change. |
| `AddSegment` | A finalized, stable segment, sent when a segment boundary is reached. It will not change. |
| `SpeechStarted` | Voice activity detection detected the onset of speech. |
| `SpeechEnded` | Voice activity detection detected the end of speech. |
| `StartOfTurn` | Turn detection marked the start of a speaker turn. |
| `EndOfTurn` | Turn detection marked the end of a speaker turn. The last message of a turn. |
| `EndOfTranscript` | Response to `EndOfStream`, after all segment messages are sent. |
| `Error` | A fatal problem. Transcription is terminated and the connection is closed. |
| `Warning` | A non-fatal problem. |
| `Info` | Additional information. |
| `SpeakersResult` | Response to `GetSpeakers`. |

Three groups carry the conversation and are the ones agent logic acts on:

| Group | Messages | What they mean |
| --- | --- | --- |
| Speech signals | `SpeechStarted`, `SpeechEnded` | Voice activity. Sent in `vad` mode only, and not turn boundaries: a mid-sentence pause ends speech without ending the turn. |
| Segments | `AddPartialSegment`, `AddSegment` | The transcript. Each partial is a snapshot that replaces the last; `AddSegment` is final and will not change. |
| Turn signals | `StartOfTurn`, `EndOfTurn` | Where a speaker's turn starts and ends. `EndOfTurn` is the turn's last message, and the cue for the agent to respond. |

Pass `AddSegment` downstream to the LLM, and use `AddPartialSegment` only for display. The other server messages manage the session rather than the conversation.

## StartRecognition

No additional properties are accepted at any level.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"StartRecognition"` | Yes | |
| `audio_format` | object | Yes | Raw audio format, below. |
| `transcription_config` | object | Yes | Below. |
| `turn_config` | object | No | Below. |

### audio_format

Raw audio only. All fields are required.

| Field | Type | Values |
| --- | --- | --- |
| `type` | string | `raw` |
| `encoding` | string | `pcm_f32le`, `pcm_s16le` |
| `sample_rate` | integer | `8000`, `16000` |

### transcription_config

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `language` | string, minimum length 1 | Yes | | Language model to process the audio input, normally an ISO language code. |
| `model` | string | Yes | | `linden-1`. Agent STT is powered by `linden-1`. |
| `enable_partials` | boolean | No | `false` | Whether to send partials (`AddPartialSegment`) as well as finals. |
| `diarization` | string | No | `none` | `none`: no diarization labels are added. `speaker`: speaker attribution based on acoustic matching. |
| `emit_sentences` | boolean | No | `false` | Whether to split multi-sentence segments on sentence boundaries, so that each segment contains a single sentence. |
| `speaker_diarization_config` | object or null | No | | Below. |
| `additional_vocab` | array | No | | Custom words or phrases to recognize. Each item is a non-empty string, or an object with `content` (required) and `sounds_like` (array of at least one non-empty string) for alternative pronunciations. |
| `domain` | string, minimum length 1 | No | | Requests a specialized model based on `language` but optimized for a particular field, for example `finance` or `medical`. |
| `output_locale` | string | No | | Language locale used when generating the output, normally an ISO language code. |
| `transcript_filtering_config` | object or null | No | | `remove_disfluencies` (boolean): if `true`, words identified as disfluencies are removed; if `false`, they are tagged as `disfluency`. `replacements` (array of `{ "from": "...", "to": "..." }`, both required): `from` is the pattern to be replaced, `to` the replacement word or phrase. |

Rule: if `speaker_diarization_config.speakers` or `speaker_diarization_config.get_speakers` is provided, `diarization` must be `speaker`.

`speaker_diarization_config`:

| Field | Type | Description |
| --- | --- | --- |
| `speaker_sensitivity` | number, 0 to 1 | Controls the number of unique speakers detected. A higher value is likely to result in more unique speakers. Increase it when fewer speaker labels appear than expected. Default 0.5. |
| `max_speakers` | integer, minimum 2 | Maximum number of speakers allowed in a single audio stream. Unrestricted when omitted. |
| `prefer_current_speaker` | boolean | If `true`, the diarization engine prefers to stick with the currently active speaker if the match is good enough, even if not the best. Reduces incorrect flipping between similar speakers. |
| `get_speakers` | boolean | If `true`, speaker identifiers are returned at the end of the transcript. |
| `speakers` | array | Enrolled speakers. Each item: `label` (string, required, minimum length 1, must not match the internal format such as `S1`, `S2`, `UU`, and must not start or end with whitespace) and `speaker_identifiers` (array of unique strings, at least one, required). |

### turn_config

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `turn_detection_mode` | string | `vad` | `vad`: turn ends are detected automatically from voice activity. `external`: turn ends are signaled by the client with `ForceEndOfUtterance`. |

### Example

```json
{
  "message": "StartRecognition",
  "audio_format": { "type": "raw", "encoding": "pcm_s16le", "sample_rate": 16000 },
  "transcription_config": {
    "model": "linden-1",
    "language": "en",
    "enable_partials": true,
    "diarization": "speaker",
    "speaker_diarization_config": {
      "speakers": [
        { "label": "Alice", "speaker_identifiers": ["<alice_id>"] }
      ]
    }
  },
  "turn_config": { "turn_detection_mode": "external" }
}
```

## Other client messages

### AddAudio

A binary WebSocket message (`application/octet-stream`) holding raw audio in the declared `audio_format`. No JSON envelope. The server confirms receipt with `AudioAdded`.

### EndOfStream

| Field | Type | Required |
| --- | --- | --- |
| `message` | `"EndOfStream"` | Yes |
| `last_seq_no` | integer | Yes |

### SetRecognitionConfig

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"SetRecognitionConfig"` | Yes | |
| `transcription_config` | object | Yes | `enable_partials` (boolean, default `false`) and `language` (string) only. |

`language` can be included, but its value must match the language in the initial `StartRecognition`. Changing the language or any other transcription configuration parameter results in an error.

### GetSpeakers

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"GetSpeakers"` | Yes | |
| `final` | boolean | No | Set `true` to wait for the end of the stream. |

### ForceEndOfUtterance

Closes the current speaker turn. The transcript up to `timestamp` is flushed as an `AddSegment`, followed by `EndOfTurn`.

Supported only with `turn_config.turn_detection_mode: external`, where the client detects turn ends itself. In the default `vad` mode the service closes turns from voice activity.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"ForceEndOfUtterance"` | Yes | |
| `timestamp` | number, minimum 0 | Yes | The audio position the request corresponds to, in seconds since the beginning of the audio. |

```json
{
  "message": "ForceEndOfUtterance",
  "timestamp": 3.24
}
```

Each timestamp must be later than the last, or the message is rejected with a `Warning`.

## Server messages

### RecognitionStarted

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"RecognitionStarted"` | Yes | |
| `id` | string | Yes | |
| `orchestrator_version` | string | No | |
| `language_pack_info` | object | No | `word_delimiter` (string, required): the character to use to separate words. `language_description` (string): full descriptive name of the language. `writing_direction`: `left-to-right` or `right-to-left`. `itn` (boolean): whether inverse text normalization is available. `adapted` (boolean): whether language model adaptation has been applied. |

### AudioAdded

| Field | Type | Required |
| --- | --- | --- |
| `message` | `"AudioAdded"` | Yes |
| `seq_no` | integer, minimum 0 | Yes |

When clients send audio faster than real time, the server may read data slower than it is sent. If binary `AddAudio` messages exceed the server's internal buffer, the server processes other WebSocket messages until buffer space is available. `AudioAdded` is sent only after the binary data is read. This can fill TCP buffers, causing WebSocket write failures and connection closure. Monitor the WebSocket's `bufferedAmount` attribute to prevent this.

### AddPartialSegment and AddSegment

Same shape. `AddPartialSegment` is sent only when `enable_partials` is `true`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"AddPartialSegment"` or `"AddSegment"` | Yes | |
| `segment.transcript` | string | Yes | The rendered segment text, punctuated. |
| `segment.speaker` | string | No | Speaker label (for example `S1`). Present only when diarization attributed one. |
| `metadata.start_time` | number | Yes | Segment start, in seconds from session start. |
| `metadata.end_time` | number | Yes | Segment end, in seconds from session start. |

```json
{
  "message": "AddSegment",
  "segment": {
    "transcript": "Hello, I'd like to check on my order.",
    "speaker": "S1"
  },
  "metadata": {
    "start_time": 1.02,
    "end_time": 3.24
  }
}
```

### SpeechStarted and SpeechEnded

Sent in `vad` mode only.

| Message | Field | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `SpeechStarted` | `metadata.start_time` | number | Yes | Time speech began, in seconds from session start. |
| `SpeechEnded` | `metadata.end_time` | number | Yes | Time speech ended, in seconds from session start. |

### StartOfTurn and EndOfTurn

| Message | Field | Type | Required | Description |
| --- | --- | --- | --- | --- |
| `StartOfTurn` | `metadata.start_time` | number | Yes | Time the turn began, in seconds from session start. |
| `EndOfTurn` | `metadata.end_time` | number | Yes | Time the turn ended, in seconds from session start. |

### EndOfTranscript

```json
{ "message": "EndOfTranscript" }
```

Sent in response to `EndOfStream`, after the server has finished sending all segment messages.

### SpeakersResult

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"SpeakersResult"` | Yes | |
| `speakers` | array | Yes | Each item: `label` (string, required) and `speaker_identifiers` (array of unique strings, at least one, required). |

## Info, Warning, and Error types

### Info

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"Info"` | Yes | |
| `type` | string | Yes | `recognition_quality` or `concurrent_session_usage`. |
| `reason` | string | Yes | |
| `quality` | string | Only when `type` is `recognition_quality` (then required) | `broadcast`. |

### Warning

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"Warning"` | Yes | |
| `reason` | string | Yes | |
| `type` | string | No | `duration_limit_exceeded`, `idle_timeout`, `session_timeout`, `add_audio_after_eos`, `speaker_id`, or `unsupported_language`. |
| `duration_limit` | number, minimum 0 | No | |

### Error

After any error, transcription is terminated and the connection is closed.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"Error"` | Yes | |
| `type` | string | Yes | One of the values below. |
| `reason` | string | Yes | |

Error `type` values: `invalid_message`, `invalid_model`, `invalid_language`, `invalid_config`, `invalid_audio_type`, `not_authorised`, `not_allowed`, `job_error`, `protocol_error`, `start_recognition_timeout`.

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

## Differences from the Realtime API

| Aspect | Agent STT (`/v2/agent`) | Realtime (`/v2`) |
| --- | --- | --- |
| Model | `linden-1` (required) | `standard`, `enhanced`, `melia-1`, `oak-1` |
| Transcript messages | `AddPartialSegment`, `AddSegment` (text and speaker per segment) | `AddPartialTranscript`, `AddTranscript` (per-word `results`) |
| Turn messages | `StartOfTurn`, `EndOfTurn`, `SpeechStarted`, `SpeechEnded` | `EndOfUtterance` |
| Turn configuration | `turn_config.turn_detection_mode` | `conversation_config.end_of_utterance_silence_trigger` |
| `ForceEndOfUtterance` | `external` mode only; `timestamp` required | Any time; `timestamp` and `channel` optional |
| `audio_format` | `raw` only; `pcm_f32le` or `pcm_s16le`; 8000 or 16000 Hz | `raw` (also `mulaw`, any sample rate) or `file` |
| `diarization` | `none`, `speaker` | `none`, `speaker`, `channel`, `channel_and_speaker` |
| Mid-session config | `enable_partials` | `max_delay`, `max_delay_mode`, `enable_partials`, `audio_filtering_config`, `conversation_config` |
| Not in the agent STT schema | | `max_delay`, `max_delay_mode`, `translation_config`, `audio_events_config`, `punctuation_overrides`, `audio_filtering_config`, `enable_entities`, `language_hints`, `AddChannelAudio` |

For the Realtime protocol, see `speechmatics:realtime-transcription`.
