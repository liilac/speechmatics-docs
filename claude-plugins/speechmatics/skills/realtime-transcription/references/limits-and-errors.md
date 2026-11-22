# Realtime limits, errors, and reconnection

Docs:

- Limits: https://docs.speechmatics.com/speech-to-text/realtime/limits
- Errors and close codes: https://docs.speechmatics.com/api-ref/realtime-transcription-websocket#error

## Concurrent sessions

| Account type | Maximum concurrent sessions |
| --- | --- |
| Free | 2 |
| Pro | 50 |
| Enterprise | Custom |

Contact [Support](https://support.speechmatics.com) to raise these limits.

The server reports current usage in an `Info` message of type `concurrent_session_usage` straight after the handshake, with `usage`, `quota`, `last_updated`, and `region`. Exceeding the quota gives an `Error` of type `quota_exceeded` and close code `4005`.

## Session limits

A Realtime SaaS session is ended automatically when any of these is met:

- Session duration reaches 48 hours.
- No audio data (`AddAudio` messages) sent for 1 hour.
- No audio or ping/pongs sent for 3 minutes.

The service sends an in-band `Error`, then a closing handshake with code `1008`.

Advance warnings:

| `Warning` type | Sent before timeout at | `reason` format |
| --- | --- | --- |
| `idle_timeout` | 15, 10, and 5 minutes | `Session will timeout in {time_remaining}m due to inactivity, no audio sent within the last {time_elapsed}m` |
| `session_timeout` | 45, 30, and 15 minutes | `Session will timeout in {time_remaining}m due to max duration, session has been active for {time_elapsed}m` |

On timeout the final `Error` has type `idle_timeout` or `session_timeout`.

### Handling long-running sessions

- Disconnect a session before it is terminated and immediately reconnect a new one. New sessions typically start in less than a second.
- For a seamless transition, connect the new session a few seconds before disconnecting the old one.
- Network issues can drop WebSocket connections unpredictably. Handle session termination gracefully in long-running sessions.

## Other limits

| Limit | Value | Result when exceeded |
| --- | --- | --- |
| Custom dictionary (`additional_vocab`) items | 20,000 | In-band `Error` of type `protocol_error`, then close code `1003`. |
| Speaker identifiers across all `speakers` | 50 | |
| Channels for channel diarization (SaaS) | 2 | |
| `max_delay` | 0.7 to 4 seconds | |
| `end_of_utterance_silence_trigger` | 0 to 2 seconds | |
| `max_speakers` | minimum 2 | |
| Single utterance duration | reported in `duration_limit` | `Warning` of type `duration_limit_exceeded`; further audio is acknowledged but ignored, and the server proceeds to `EndOfTranscript`. |

## Data retention

Speechmatics Realtime SaaS does not store audio files, transcripts, or configuration data.

## Sending audio too fast

When audio is sent faster than real time, the server may read slower than the client writes. `AudioAdded` is sent only after the binary data is read. TCP buffers can fill, causing WebSocket write failures and connection closure. Monitor the WebSocket `bufferedAmount` attribute and throttle. If the server cannot process audio as fast as it is sent and the backlog grows too large, it returns `job_error`.

## Error handling

After any `Error` message the transcription is terminated and the connection is closed.

| `Error` type | Likely cause | Action |
| --- | --- | --- |
| `invalid_message` | Message not understood. | Fix the message JSON. |
| `invalid_model` | Language not supported or not available to the account. | Check `language` and `model`. |
| `invalid_language` | Language not valid or not supported. | Check the language code. |
| `invalid_config` | Wrong or unsupported config fields, or too many translation targets. | Fix `StartRecognition` or `SetRecognitionConfig`. |
| `invalid_audio_type` | Audio type unsupported, deprecated, or malformed. | Fix `audio_format`. |
| `invalid_output_format` | Output format unsupported, deprecated, or malformed. | |
| `not_authorised` | User not recognized or API key invalid. | Check the API key or temporary key. |
| `not_allowed` | Action not permitted for the user. | |
| `job_error` | Server could not work on the job, or the audio backlog grew too large. | Retry after 5–10 seconds; throttle audio. |
| `protocol_error` | Messages in the wrong order, or a protocol limit such as the custom dictionary size. | Fix message ordering. |
| `quota_exceeded` | Concurrent connection limit reached. | Retry after 5–10 seconds; reduce concurrency. |
| `timelimit_exceeded` | Usage quota for the contract reached. | |
| `idle_timeout` | No audio for 1 hour. | Reconnect when audio resumes. |
| `session_timeout` | 48-hour maximum reached. | Reconnect. |
| `unknown_error` | Anything else. | |

## Close codes

| Close code | Reason | Retry |
| --- | --- | --- |
| 1003 | `protocol_error` | No |
| 1008 | `policy_violation` (includes idle and session timeouts) | No |
| 1011 | `internal_error` | After at least 5–10 seconds |
| 4001 | `not_authorised` | No |
| 4003 | `not_allowed` | No |
| 4004 | `invalid_model` | No |
| 4005 | `quota_exceeded` | After at least 5–10 seconds |
| 4006 | `timelimit_exceeded` | No |
| 4013 | `job_error` | After at least 5–10 seconds |

"No" means the docs name only `4005`, `4013`, and `1011` as retryable; reconnecting after a `1008` timeout with a fresh session is still expected.

## Handshake failures

| HTTP status | Meaning |
| --- | --- |
| 400 | The handshake request is malformed. |
| 401 | The API key or temporary key is not valid. |
| 405 | The request method is not `GET`. |
