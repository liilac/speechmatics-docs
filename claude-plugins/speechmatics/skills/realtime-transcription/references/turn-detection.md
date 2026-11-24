# Realtime turn detection

Docs: https://docs.speechmatics.com/speech-to-text/realtime/turn-detection

Use end of utterance detection to detect when a person has finished speaking, for voice AI, realtime translation, and dictation. For turn-based segments with built-in turn messages, consider `speechmatics:agent-stt` instead.

## Options

| Approach | How | Models |
| --- | --- | --- |
| Silence-based end of utterance | `conversation_config.end_of_utterance_silence_trigger` | Enhanced, Standard |
| Client-side turn detection | Send `ForceEndOfUtterance` | Enhanced, Standard, Melia 1, Oak 1 |
| Semantic turn detection | Combine silence-based detection with conversation context in the application | See the linked guide |

Melia 1 and Oak 1 do not support automatic silence-based detection and reject `end_of_utterance_silence_trigger` in `conversation_config`. Omit it and send `ForceEndOfUtterance` from the client. (The opening paragraph of the turn detection page names only Melia 1 as unsupported; the same page's client-side section and the API schema name both Melia 1 and Oak 1.)

## Silence-based end of utterance

The server uses word timings to detect periods without speech. When a word is detected, a countdown begins. A new word restarts it. If the configured interval passes without another word, an end of utterance is triggered: the server sends a Final transcript (`AddTranscript`), followed by an `EndOfUtterance` message.

### Configuration

The `"type": "transcription"` wrapper below is as shown in the docs; `StartRecognition` itself has no `type` field, so send only the `transcription_config` part. See [configuration.md](configuration.md).

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "conversation_config": {
      "end_of_utterance_silence_trigger": 0.5
    },
    "language": "en"
  }
}
```

`end_of_utterance_silence_trigger` (number): 0 to 2 seconds, default 0. The number of seconds of non-speech to wait before an end of utterance is identified. 0 disables detection.

Guidance:

- Use 0.5–0.8 seconds for most voice AI applications. Longer values (0.8–1.2 s) may suit dictation.
- Keep `end_of_utterance_silence_trigger` lower than `max_delay`.
- `EndOfUtterance` is sent only after some speech is recognized. Duplicates are never sent for the same period of silence.
- `EndOfUtterance` is not tied to any individual identified by diarization and contains no speaker information.
- The value can be changed mid-session with `SetRecognitionConfig`.

### EndOfUtterance message

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `message` | `"EndOfUtterance"` | Yes | |
| `metadata.start_time` | number | No | The time (seconds) that the end of utterance was detected. |
| `metadata.end_time` | number | No | The time (seconds) that the end of utterance was detected. |
| `channel` | string | No | Multichannel only. |
| `forced` | boolean | No | Present, with value `true`, only when triggered by `ForceEndOfUtterance`. |

`metadata` itself is required. Like punctuation, an `EndOfUtterance` has zero duration.

## Client-side turn detection

Send `ForceEndOfUtterance` to trigger an end of utterance at any point. This lets an application integrate its own end of turn detection model, for example voice activity detection.

```json
{
  "message": "ForceEndOfUtterance"
}
```

For higher accuracy, include the optional `timestamp`: seconds since the beginning of the audio that the request corresponds to.

```json
{
  "message": "ForceEndOfUtterance",
  "timestamp": 63.5
}
```

With multichannel diarization, name the channel:

```json
{
  "message": "ForceEndOfUtterance",
  "channel": "new_york"
}
```

The server responds with an `AddTranscript` followed by an `EndOfUtterance`. Both include `forced: true`.

## Semantic turn detection

Silence-based detection is enough for many use cases, but is often improved by combining it with the context of the conversation. See the [semantic turn detection guide](https://blog.speechmatics.com/semantic-turn-detection).

## Python example: live microphone

Uses `speechmatics-python` and `pyaudio`.

```python
import speechmatics
import pyaudio
import threading
import time
import asyncio

API_KEY = "YOUR_API_KEY"
LANGUAGE = "en"
CONNECTION_URL = f"wss://au.rt.speechmatics.com/v2"

# Audio recording parameters
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
FORMAT = pyaudio.paFloat32


class AudioProcessor:
    def __init__(self):
        self.wave_data = bytearray()
        self.read_offset = 0

    async def read(self, chunk_size):
        while self.read_offset + chunk_size > len(self.wave_data):
            await asyncio.sleep(0.001)

        new_offset = self.read_offset + chunk_size
        data = self.wave_data[self.read_offset : new_offset]
        self.read_offset = new_offset
        return data

    def write_audio(self, data):
        self.wave_data.extend(data)


class VoiceAITranscriber:
    def __init__(self):
        self.ws = speechmatics.client.WebsocketClient(
            speechmatics.models.ConnectionSettings(
                url=CONNECTION_URL,
                auth_token=API_KEY,
            )
        )
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_processor = AudioProcessor()

        # Set up event handlers
        self.ws.add_event_handler(
            event_name=speechmatics.models.ServerMessageType.AddPartialTranscript,
            event_handler=self.handle_partial_transcript,
        )

        self.ws.add_event_handler(
            event_name=speechmatics.models.ServerMessageType.AddTranscript,
            event_handler=self.handle_final_transcript,
        )

        self.ws.add_event_handler(
            event_name=speechmatics.models.ServerMessageType.EndOfUtterance,
            event_handler=self.handle_end_of_utterance,
        )

    def handle_partial_transcript(self, msg):
        transcript = msg["metadata"]["transcript"]
        print(f"[Listening...] {transcript}")

    def handle_final_transcript(self, msg):
        transcript = msg["metadata"]["transcript"]
        print(f"[Complete] {transcript}")

    def handle_end_of_utterance(self, msg):
        print("End of utterance detected - ready for AI response!")
        # This is where your voice AI would process the complete utterance
        # and generate a response

    def stream_callback(self, in_data, frame_count, time_info, status):
        self.audio_processor.write_audio(in_data)
        return in_data, pyaudio.paContinue

    def start_streaming(self):
        try:
            # Set up pyaudio stream with callback
            self.stream = self.audio.open(
                format=FORMAT,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
                stream_callback=self.stream_callback,
            )

            # Configure audio settings
            settings = speechmatics.models.AudioSettings()
            settings.encoding = "pcm_f32le"
            settings.sample_rate = SAMPLE_RATE
            settings.chunk_size = CHUNK_SIZE

            # Configure transcription with end-of-utterance detection

            conversation_config = speechmatics.models.ConversationConfig(
                end_of_utterance_silence_trigger=0.75
            )  # Adjust as needed

            conf = speechmatics.models.TranscriptionConfig(
                model="enhanced",
                language=LANGUAGE,
                enable_partials=True,
                max_delay=1,
                conversation_config=conversation_config,
            )

            print("Voice AI ready - start speaking!")
            print("Press Ctrl+C to stop...")

            # Start transcription using the working approach
            self.ws.run_synchronously(
                transcription_config=conf,
                stream=self.audio_processor,
                audio_settings=settings,
            )

        except KeyboardInterrupt:
            print("\nStopping voice AI transcriber...")
        except Exception as e:
            print(f"Error in transcription: {e}")
        finally:
            self.stop_streaming()

    def stop_streaming(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


# Usage
if __name__ == "__main__":
    transcriber = VoiceAITranscriber()
    transcriber.start_streaming()
```

## Python example: file

```python
import speechmatics

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"
CONNECTION_URL = "wss://au.rt.speechmatics.com/v2"

# Create a transcription client
ws = speechmatics.client.WebsocketClient(
    speechmatics.models.ConnectionSettings(
        url=CONNECTION_URL,
        auth_token=API_KEY,
    )
)


# Define an event handler to print the partial transcript
def print_partial_transcript(msg):
    print(f"[partial] {msg['metadata']['transcript']}")


# Define an event handler to print the full transcript
def print_transcript(msg):
    print(f"[   FULL] {msg['metadata']['transcript']}")


# Define an event handler for the end-of-utterance event
def print_eou(msg):
    print("EndOfUtterance")


# Register the event handler for partial transcript
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AddPartialTranscript,
    event_handler=print_partial_transcript,
)

# Register the event handler for full transcript
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.AddTranscript,
    event_handler=print_transcript,
)

# Register the event handler for end of utterance
ws.add_event_handler(
    event_name=speechmatics.models.ServerMessageType.EndOfUtterance,
    event_handler=print_eou,
)

settings = speechmatics.models.AudioSettings()

# Define transcription parameters
# Full list of parameters described here: https://speechmatics.github.io/speechmatics-python/models

conversation_config = speechmatics.models.ConversationConfig(
    end_of_utterance_silence_trigger=0.75
)  # Adjust as needed

conf = speechmatics.models.TranscriptionConfig(
    model="enhanced",
    language=LANGUAGE,
    enable_partials=True,
    max_delay=1,
    conversation_config=conversation_config,
)

print("Starting transcription (type Ctrl-C to stop):")
with open(PATH_TO_FILE, "rb") as fd:
    try:
        ws.run_synchronously(fd, conf, settings)
    except KeyboardInterrupt:
        print("\nTranscription stopped.")
```
