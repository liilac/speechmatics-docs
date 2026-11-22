# Agent STT segmentation and turn detection

Docs:

- Segmentation: https://docs.speechmatics.com/speech-to-text/agent-stt/segmentation
- Turn detection: https://docs.speechmatics.com/speech-to-text/agent-stt/turn-detection

## Contents

- [Partial and final segments](#partial-and-final-segments)
- [What closes a segment](#what-closes-a-segment)
- [Segment payload](#segment-payload)
- [Speaker labels](#speaker-labels)
- [Speaker identification](#speaker-identification)
- [Sentence-level segments](#sentence-level-segments)
- [Turn messages](#turn-messages)
- [Speech signals are not turn boundaries](#speech-signals-are-not-turn-boundaries)
- [Choosing who ends a turn](#choosing-who-ends-a-turn)
- [Message order in a turn](#message-order-in-a-turn)

## Partial and final segments

Agent STT groups words into whole segments: punctuated, attributed to a speaker, and ready to pass to an LLM. Two messages carry the transcript:

- `AddPartialSegment`: an interim preview of the segment being built. Each one replaces the previous one. Display the latest and discard the rest. Never concatenate them.
- `AddSegment`: the finalized segment. It will not change, and it is the message to act on.

Partials arrive only when `transcription_config.enable_partials` is `true`.

## What closes a segment

A segment ends at the first boundary it reaches:

| Boundary | When it applies |
| --- | --- |
| End of turn | Always |
| Speaker change | When diarization is enabled |
| End of sentence | When `emit_sentences` is `true` |
| Duration cap | Always. A segment never covers more than two minutes of audio. |

A single turn therefore often produces several `AddSegment` messages. To reconstruct everything one speaker said, join the segments for that speaker between `StartOfTurn` and `EndOfTurn`.

Reaching the duration cap is a sign that turn detection is not closing turns, rather than an ordinary boundary.

## Segment payload

`AddSegment` and `AddPartialSegment` have the same shape:

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

| Field | Description |
| --- | --- |
| `segment.transcript` | The segment text, punctuated. |
| `segment.speaker` | The speaker label. Present only when diarization attributed one. |
| `metadata.start_time` | Segment start, in seconds from the start of the session. |
| `metadata.end_time` | Segment end, in seconds from the start of the session. |

In the SDK, read the text from `message["segment"]["transcript"]` and the speaker from `message["segment"]["speaker"]` (use `.get("speaker")`, since it can be absent).

## Speaker labels

Set `transcription_config.diarization` to `speaker` to attribute each segment acoustically. Labels are `S1`, `S2`, and so on, in the order each speaker is first heard. A segment never spans two speakers, because a speaker change is itself a boundary.

Tune attribution with `transcription_config.speaker_diarization_config`:

| Field | Description |
| --- | --- |
| `speaker_sensitivity` | How readily a new speaker is identified, between `0` and `1`. Default `0.5`. Raise it when fewer speakers appear than expected. |
| `max_speakers` | The maximum number of speakers to identify in the stream. Minimum `2`. Unrestricted when omitted. |
| `prefer_current_speaker` | Keeps the active speaker when the match is good enough, rather than switching to a marginally better one. Reduces flipping between similar voices. |
| `get_speakers` | Returns speaker identifiers at the end of the transcript. |

## Speaker identification

Labels such as `S1` are per-session: the same person is not necessarily `S1` in the next call. Speaker identification carries a speaker across sessions, under a label the application chooses.

Enroll: set `get_speakers` to `true` to receive identifiers at the end of the transcript, or send `GetSpeakers` mid-session with `final` set to `true` to wait for the end of the stream. Either way the server replies with `SpeakersResult`, holding a `speaker_identifiers` value for each label.

```json
{ "message": "GetSpeakers", "final": true }
```

Identify: store those identifiers and pass them back in a later session as `speaker_diarization_config.speakers`, each with a custom `label`:

```json
{
  "diarization": "speaker",
  "speaker_diarization_config": {
    "speakers": [
      { "label": "Alice", "speaker_identifiers": ["<alice_id>"] }
    ]
  }
}
```

Alice's segments are then labeled `Alice` rather than `S1`. Anyone not enrolled keeps an `S1`-style label.

Rules:

- Custom labels must not look like the internal format: `S1`, `S2`, and `UU` are rejected.
- `diarization` must be `speaker` when `speakers` or `get_speakers` is set.
- Identifiers are tied to the model that generated them and are scoped to the project.
- There is a limit on how many identifiers can be sent in one session.

For enrollment guidance and the full caveats, see the [speaker identification feature page](https://docs.speechmatics.com/speech-to-text/features/speaker-identification) and `speechmatics:transcription-features`.

## Sentence-level segments

Set `emit_sentences` to `true` to add a boundary at every sentence, so each segment holds one sentence. Leave it off for the largest coherent chunk per speaker, which is usually what an LLM should receive.

## Turn messages

A turn is one speaker's contribution to a conversation. Knowing it has ended tells the agent to stop listening and respond. Close too early and the agent interrupts; close too late and the conversation drags.

`StartOfTurn` and `EndOfTurn` bound each turn:

- `StartOfTurn` is emitted on the first word of transcript rather than the first sound, so a cough or a door closing does not open a turn.
- `EndOfTurn` is always the turn's last message, arriving after the final `AddSegment`. Nothing further is coming for that speaker and the agent can respond.

Between the two, segments carry the transcript.

## Speech signals are not turn boundaries

`SpeechStarted` and `SpeechEnded` report voice activity only, and are sent in `vad` mode. They indicate that the microphone has picked up speech, not that a thought is finished. A pause mid-sentence produces `SpeechEnded` while the turn stays open.

- Use `SpeechStarted` and `SpeechEnded` for interruption handling and UI feedback.
- Use `EndOfTurn` to decide when to respond.

## Choosing who ends a turn

`turn_config.turn_detection_mode` decides which side closes turns:

| Mode | Who decides | Use it when |
| --- | --- | --- |
| `vad` (default) | The service, from voice activity | The application streams audio and has no endpointing of its own. |
| `external` | The application, with `ForceEndOfUtterance` | Something upstream already detects turn ends: Pipecat, LiveKit, or a push-to-talk control. |

Running two detectors against the same audio produces conflicting boundaries. Pick the one that owns the decision.

### vad mode

The service runs voice activity detection over the audio and closes the turn when speech stops. Nothing is required from the application beyond streaming audio. `ForceEndOfUtterance` is not supported. Voice activity detection is not currently configurable.

### external mode

No voice activity detection runs, no `SpeechStarted` or `SpeechEnded` is sent, and no turn ends on its own. The application closes each turn by sending `ForceEndOfUtterance` with the audio timestamp to cut at:

```json
{
  "message": "ForceEndOfUtterance",
  "timestamp": 3.24
}
```

- `timestamp` is the point in the audio where the turn should end, in seconds from the start of the session. The cut lands where speech stopped rather than wherever the message arrives.
- Each timestamp must be later than the last, or the message is rejected with a `Warning`.
- The flushed text arrives as a normal `AddSegment`, followed by `EndOfTurn`.

Nothing else closes a turn in this mode. An application that stops sending `ForceEndOfUtterance` receives segments but no `EndOfTurn`, and the agent never learns that the speaker has finished.

With the SDK:

```python
from speechmatics.agent_stt import TurnConfig, TurnDetectionMode

client = AgentSttAsyncClient(
    transcription_config=TranscriptionConfig(language="en"),
    turn_config=TurnConfig(turn_detection_mode=TurnDetectionMode.EXTERNAL),
)
```

```python
client.finalize()
```

`finalize()` is stamped with the audio position at the moment it is called.

## Message order in a turn

| Step | `vad` mode | `external` mode |
| --- | --- | --- |
| Speech begins | `SpeechStarted` | (not sent) |
| First word transcribed | `StartOfTurn` | `StartOfTurn` |
| While speaking | `AddPartialSegment` (if enabled), `AddSegment` at each segment boundary | Same |
| Mid-sentence pause | `SpeechEnded`, then `SpeechStarted` when speech resumes; the turn stays open | (not sent) |
| Turn closes | Service detects speech has stopped | Client sends `ForceEndOfUtterance` |
| Final output | Final `AddSegment`, then `EndOfTurn` | Final `AddSegment`, then `EndOfTurn` |

The exact interleaving of `SpeechStarted`/`SpeechEnded` with segment messages is not specified in the docs. Rely only on these guarantees: `StartOfTurn` precedes a turn's segments, and `EndOfTurn` follows the turn's final `AddSegment`.
