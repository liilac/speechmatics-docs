# Realtime code examples and guides

Docs:

- Quickstart: https://docs.speechmatics.com/speech-to-text/realtime/quickstart
- Python microphone input: https://docs.speechmatics.com/speech-to-text/realtime/guides/python-using-microphone
- Python using FFmpeg: https://docs.speechmatics.com/speech-to-text/realtime/guides/python-using-ffmpeg

## Contents

- [Packages](#packages)
- [JavaScript: microphone with sox](#javascript-microphone-with-sox)
- [JavaScript: transcribe a radio stream](#javascript-transcribe-a-radio-stream)
- [Python: microphone with speechmatics-python](#python-microphone-with-speechmatics-python)
- [Python: transcribe a URL stream](#python-transcribe-a-url-stream)
- [FFmpeg piped into the speechmatics CLI](#ffmpeg-piped-into-the-speechmatics-cli)

Other complete samples: the `speechmatics-rt` Python quickstart is in [../SKILL.md](../SKILL.md), end of utterance samples in [turn-detection.md](turn-detection.md), speaker identification samples in [diarization.md](diarization.md).

## Packages

| Package | Install | Used in |
| --- | --- | --- |
| `speechmatics-rt` (Python) | `pip install speechmatics-rt pyaudio` | Quickstart. Imports from `speechmatics.rt`: `AsyncClient`, `TranscriptionConfig`, `AudioFormat`, `AudioEncoding`, `Microphone`, `ServerMessageType`, `TranscriptResult`, `AuthenticationError`. |
| `speechmatics-python` (Python library and `speechmatics` CLI) | `pip3 install speechmatics-python` (Python 3.7 or later) | Microphone guide, FFmpeg guide, turn detection and speaker identification samples. Uses `speechmatics.client.WebsocketClient` and `speechmatics.models`. |
| `@speechmatics/real-time-client` and `@speechmatics/auth` (JavaScript) | `npm install @speechmatics/real-time-client @speechmatics/auth` | Quickstart. [JavaScript SDK on GitHub](https://github.com/speechmatics/speechmatics-js-sdk). |
| `@speechmatics/browser-audio-input` (JavaScript) | npm | Capturing raw audio in the browser. |

The two Python packages have different APIs. Do not mix `speechmatics.rt` imports with `speechmatics.client` / `speechmatics.models` code.

## JavaScript: microphone with sox

Requires `sox`: `brew install sox` (macOS) or `apt install sox` (Linux). Replace `YOUR_API_KEY`. Press `Ctrl+C` to stop.

```javascript
import { spawn } from "node:child_process";
import { createSpeechmaticsJWT } from "@speechmatics/auth";
import { RealtimeClient } from "@speechmatics/real-time-client";

const apiKey = YOUR_API_KEY;
const client = new RealtimeClient();

const audio_format = {
  type: "raw",
  encoding: "pcm_s16le",
  sample_rate: 44100,
};

async function transcribe() {
  client.addEventListener("receiveMessage", ({ data }) => {
    if (data.message === "AddTranscript") {
      const transcript = data.metadata?.transcript;
      if (transcript) console.log(`[Final]: ${transcript}`);
    } else if (data.message === "Error") {
      console.error(`Error [${data.type}]: ${data.reason}`);
      process.exit(1);
    }
  });

  const jwt = await createSpeechmaticsJWT({ type: "rt", apiKey, ttl: 60 });

  await client.start(jwt, {
    transcription_config: {
      language: "en",
      max_delay: 0.7,
      model: "enhanced",
    },
    audio_format,
  });

  const recorder = spawn("sox", [
    "-d", // default audio device (mic)
    "-q", // quiet
    "-r",
    String(audio_format.sample_rate), // sample rate
    "-e",
    "signed-integer", // match pcm_s16le
    "-b",
    "16", // match pcm_s16le
    "-c",
    "1", // mono
    "-t",
    "raw", // raw PCM output
    "-", // pipe to stdout
  ]);

  recorder.stdout.on("data", (chunk) => client.sendAudio(chunk));
  recorder.stderr.on("data", (d) => console.error(`sox: ${d}`));

  process.on("SIGINT", () => {
    recorder.kill();
    client.stopRecognition({ noTimeout: true });
  });
}

transcribe().catch((err) => {
  console.error(err);
  process.exit(1);
});
```

Expected output:

```
[Final]: Hello, welcome to Speechmatics.
[Final]: This is a real-time transcription example.
```

To add Partials, set `enable_partials: true` in `transcription_config` and handle `AddPartialTranscript`:

```javascript
client.addEventListener("receiveMessage", ({ data }) => {
    if (data.message === "AddTranscript") {
        console.log(`[Final]:   ${data.metadata.transcript}`);
    } else if (data.message === "AddPartialTranscript") {
        console.log(`[Partial]: ${data.metadata.transcript}\r`);
    }
});
```

## JavaScript: transcribe a radio stream

Streams an MP3 radio URL to the API. No `audio_format` is passed to `client.start`. Builds text from `results` and uses `transcript_filtering_config.remove_disfluencies`.

```javascript
import https from "node:https";
import { createSpeechmaticsJWT } from "@speechmatics/auth";
import { RealtimeClient } from "@speechmatics/real-time-client";

const apiKey = YOUR_API_KEY;
const client = new RealtimeClient();
const streamURL = "https://media-ice.musicradio.com/LBCUKMP3";

async function transcribe() {
  // Print transcript as we receive it
  client.addEventListener("receiveMessage", ({ data }) => {
    if (data.message === "AddTranscript") {
      for (const result of data.results) {
        if (result.type === "word") {
          process.stdout.write(" ");
        }
        process.stdout.write(`${result.alternatives?.[0].content}`);
        if (result.is_eos) {
          process.stdout.write("\n");
        }
      }
    } else if (data.message === "EndOfTranscript") {
      process.stdout.write("\n");
      process.exit(0);
    } else if (data.message === "Error") {
      process.stdout.write(`\n${JSON.stringify(data)}\n`);
      process.exit(1);
    }
  });

  const jwt = await createSpeechmaticsJWT({
    type: "rt",
    apiKey,
    ttl: 60, // 1 minute
  });

  await client.start(jwt, {
    transcription_config: {
      language: "en",
      model: "enhanced",
      max_delay: 1.0,
      transcript_filtering_config: {
        remove_disfluencies: true,
      },
    },
  });

  const stream = https.get(streamURL, (response) => {
    // Handle the response stream
    response.on("data", (chunk) => {
      client.sendAudio(chunk);
    });

    response.on("end", () => {
      console.log("Stream ended");
      client.stopRecognition({ noTimeout: true });
    });

    response.on("error", (error) => {
      console.error("Stream error:", error);
      client.stopRecognition();
    });
  });

  stream.on("error", (error) => {
    console.error("Request error:", error);
    client.stopRecognition();
  });
}

transcribe();
```

## Python: microphone with speechmatics-python

Setup:

```bash
pip3 install speechmatics-python
pip3 install pyaudio
```

On Mac M1/M2, install PyAudio with:

```bash
brew install portaudio
brew link portaudio
BREW_PREFIX=$(brew --prefix)
CFLAGS="-I$BREW_PREFIX/include -L$BREW_PREFIX/lib" python3 -m pip install pyaudio
```

The script lists input devices, uses the default device unless `DEVICE_INDEX` is set, captures 32-bit float audio at the device's default sample rate, and prints Partials and Finals. Replace `YOUR_API_KEY`.

```python
import speechmatics
from httpx import HTTPStatusError
import asyncio
import pyaudio

API_KEY = "YOUR_API_KEY"
LANGUAGE = "en"
CONNECTION_URL = f"wss://eu.rt.speechmatics.com/v2/{LANGUAGE}"
DEVICE_INDEX = -1
CHUNK_SIZE = 1024


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
        return


audio_processor = AudioProcessor()


# PyAudio callback
def stream_callback(in_data, frame_count, time_info, status):
    audio_processor.write_audio(in_data)
    return in_data, pyaudio.paContinue


# Set up PyAudio
p = pyaudio.PyAudio()
if DEVICE_INDEX == -1:
    DEVICE_INDEX = p.get_default_input_device_info()["index"]
    device_name = p.get_default_input_device_info()["name"]
    DEF_SAMPLE_RATE = int(p.get_device_info_by_index(DEVICE_INDEX)["defaultSampleRate"])
    print(
        f"***\nIf you want to use a different microphone, update DEVICE_INDEX at the start of the code to one of the following:"
    )
    # Filter out duplicates that are reported on some systems
    device_seen = set()
    for i in range(p.get_device_count()):
        if p.get_device_info_by_index(i)["name"] not in device_seen:
            device_seen.add(p.get_device_info_by_index(i)["name"])
            try:
                supports_input = p.is_format_supported(
                    DEF_SAMPLE_RATE,
                    input_device=i,
                    input_channels=1,
                    input_format=pyaudio.paFloat32,
                )
            except Exception:
                supports_input = False
            if supports_input:
                print(
                    f"-- To use << {p.get_device_info_by_index(i)['name']} >>, set DEVICE_INDEX to {i}"
                )
    print("***\n")

SAMPLE_RATE = int(p.get_device_info_by_index(DEVICE_INDEX)["defaultSampleRate"])
device_name = p.get_device_info_by_index(DEVICE_INDEX)["name"]

print(f"\nUsing << {device_name} >> which is DEVICE_INDEX {DEVICE_INDEX}")
print("Starting transcription (type Ctrl-C to stop):")

stream = p.open(
    format=pyaudio.paFloat32,
    channels=1,
    rate=SAMPLE_RATE,
    input=True,
    frames_per_buffer=CHUNK_SIZE,
    input_device_index=DEVICE_INDEX,
    stream_callback=stream_callback,
)

# Define connection parameters
conn = speechmatics.models.ConnectionSettings(
    url=CONNECTION_URL,
    auth_token=API_KEY,
)

# Create a transcription client
ws = speechmatics.client.WebsocketClient(conn)

# Define transcription parameters
# Full list of parameters described here: https://speechmatics.github.io/speechmatics-python/models
conf = speechmatics.models.TranscriptionConfig(
    language=LANGUAGE,
    enable_partials=True,
    model="enhanced",
    max_delay=1,
)


# Define an event handler to print the partial transcript
def print_partial_transcript(msg):
    print(f"[partial] {msg['metadata']['transcript']}")


# Define an event handler to print the full transcript
def print_transcript(msg):
    print(f"[  FINAL] {msg['metadata']['transcript']}")


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

settings = speechmatics.models.AudioSettings()
settings.encoding = "pcm_f32le"
settings.sample_rate = SAMPLE_RATE
settings.chunk_size = CHUNK_SIZE

print("Starting transcription (type Ctrl-C to stop):")
try:
    ws.run_synchronously(audio_processor, conf, settings)
except KeyboardInterrupt:
    print("\nTranscription stopped.")
except HTTPStatusError as e:
    if e.response.status_code == 401:
        print("Invalid API key - Check your API_KEY at the top of the code!")
    else:
        raise e
```

Notes:

- This sample connects to `wss://eu.rt.speechmatics.com/v2/{LANGUAGE}`; the other samples connect to `wss://eu.rt.speechmatics.com/v2`. If a language code is in the URL, `transcription_config.language` must be consistent with it.
- To add end of utterance detection, pass `conversation_config=speechmatics.models.ConversationConfig(end_of_utterance_silence_trigger=...)` in `TranscriptionConfig` and handle `ServerMessageType.EndOfUtterance`. See [turn-detection.md](turn-detection.md).
- A 401 surfaces as `httpx.HTTPStatusError`.

## Python: transcribe a URL stream

Streams an MP3 radio URL with default `speechmatics.models.AudioSettings()`.

```python
import speechmatics
from httpx import HTTPStatusError
from urllib.request import urlopen

API_KEY = "YOUR_API_KEY"
LANGUAGE = "en"
CONNECTION_URL = "wss://eu.rt.speechmatics.com/v2"

# The raw audio stream will be a few seconds ahead of the radio
AUDIO_STREAM_URL = "https://media-ice.musicradio.com/LBCUKMP3"  # LBC Radio stream

audio_stream = urlopen(AUDIO_STREAM_URL)

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

settings = speechmatics.models.AudioSettings()

# Define transcription parameters
# Full list of parameters described here: https://speechmatics.github.io/speechmatics-python/models
conf = speechmatics.models.TranscriptionConfig(
    model="enhanced",
    language=LANGUAGE,
    enable_partials=True,
    max_delay=1,
)

print("Starting transcription (type Ctrl-C to stop):")
try:
    ws.run_synchronously(audio_stream, conf, settings)
except KeyboardInterrupt:
    print("\nTranscription stopped.")
except HTTPStatusError as e:
    if e.response.status_code == 401:
        print("Invalid API key - Check your API_KEY at the top of the code!")
    else:
        raise e
```

## FFmpeg piped into the speechmatics CLI

Use FFmpeg to capture microphone audio and pipe it into the `speechmatics` CLI.

### 1. Install the CLI

Requires Python 3.7 or later.

```bash
pip install speechmatics-python
speechmatics -h
```

### 2. Configure the CLI

Same on every OS:

```bash
speechmatics config set --auth-token {YOUR_API_KEY} --generate-temp-token
```

### 3. Install FFmpeg and run

Linux (needs `apt`, for example Ubuntu 22 or Debian 11; otherwise build from [source](https://ffmpeg.org/download.html#build-linux)):

```bash
sudo apt update
sudo apt install ffmpeg libasound2 alsa-utils
ffmpeg -version
```

```bash
ffmpeg -loglevel quiet -f alsa -i hw:0 -f wav - | \
    speechmatics transcribe --max-delay 2 -
```

`hw:0` is the default device index. List devices with `arecord -l`, then replace `hw:0` with `hw:{CARD_NO},{DEVICE_NO},{OPTIONAL:SUB_DEVICE_NO}`.

macOS (with [Homebrew](https://brew.sh/)):

```bash
brew update
brew upgrade
brew install ffmpeg
```

```bash
ffmpeg -loglevel quiet -f avfoundation -i ":default" -f wav - | \
    speechmatics transcribe --max-delay 2 -
```

The default device may not always work. List devices with the command below, then replace `:default` with the chosen device index.

```bash
ffmpeg -f avfoundation -list_devices true -i ""
```

Windows:

1. Download a zip build from the [FFmpeg site](https://ffmpeg.org/download.html#build-windows) and extract it (for example with 7-zip).
2. Rename the extracted folder to `ffmpeg` and move it somewhere permanent, for example `C:\ffmpeg`.
3. Add the `bin` folder to the path: search for **system variables**, select **Edit the system environment variables**, under **User variables** select **Path**, select **Edit**, select **New**, add `C:\ffmpeg\bin`, and select **OK**.
4. Open a new terminal window and verify with `ffmpeg -version`.

List audio devices:

```
ffmpeg -list_devices true -f dshow -i dummy -
```

Run with the chosen device:

```
ffmpeg -loglevel quiet -f dshow -i audio="<audio device>" -f wav - | \
    speechmatics transcribe --max-delay 2 -
```

In every case FFmpeg writes WAV to stdout (`-f wav -`) and the CLI reads from stdin (the trailing `-`).
