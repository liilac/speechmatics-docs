# Twilio integration

Docs: https://docs.speechmatics.com/integrations-and-sdks/twilio

Reference repo: https://github.com/speechmatics/speechmatics-twilio-integration ([Python](https://github.com/speechmatics/speechmatics-twilio-integration/tree/main/python), [Node.js](https://github.com/speechmatics/speechmatics-twilio-integration/tree/main/js))

This is a reference implementation: clone it, run it, and adapt it. It is not a hosted service or a Twilio Marketplace add-on.

Twilio [Media Streams](https://www.twilio.com/docs/voice/media-streams) sends a live copy of a call's audio to a URL you control. The proxy takes that stream and feeds it into the Speechmatics Realtime API, printing per-channel transcripts to your console as the call unfolds.

## How the proxy works

```text
Caller A <--voice--> Twilio <--voice--> Caller B
                       |
                       | copy of audio (μ-law 8 kHz)
                       v
              Proxy (proxy.py / proxy.ts)
                       |
                       | Realtime WebSocket
                       v
            Speechmatics Realtime API --> per-channel transcripts --> your console
```

- Caller A dials your Twilio number, which forwards to Caller B. The two talk like a direct call.
- Twilio sends a live copy of the audio to your proxy over a WebSocket.
- The proxy hands that audio to Speechmatics with channel diarization turned on.
- Each speaker (`inbound` from Caller A, `outbound` from Caller B) gets its own transcript stream.
- Speechmatics returns transcripts, and the proxy prints them under per-channel labels.

Everything runs on your machine. [ngrok](https://ngrok.com) gives Twilio a public URL to reach you.

## Prerequisites

- A Speechmatics API key from the portal (https://portal.speechmatics.com).
- A Twilio account, a voice-capable Twilio phone number, your Account SID, and your Auth Token.
- A second phone number you own or have verified with Twilio to call.
- An ngrok account and auth token.
- Python 3.9+ or Node.js 20+, depending on the implementation.

## Clone

```bash
git clone https://github.com/speechmatics/speechmatics-twilio-integration.git
cd speechmatics-twilio-integration
```

The repo contains a `python/` folder and a `js/` folder alongside a shared `.env.example` at the root. Both implementations read the same `.env`.

## Credentials

```bash
cp .env.example .env
```

Set every variable. The proxy won't run if any are missing.

| Variable | Value |
|---|---|
| `SPEECHMATICS_API_KEY` | Your Speechmatics Realtime API key |
| `NGROK_AUTHTOKEN` | Your ngrok auth token from the ngrok dashboard |
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID (starts with `AC`) |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Your Twilio number in E.164 form, for example `+442475429721` |
| `FORWARD_TO_NUMBER` | The E.164 number the call bridges to (the second speaker) |

## Install and run

Python:

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python proxy.py
```

Node.js:

```bash
cd js
npm install
npm start
```

Startup banner:

```text
Listening on ws://localhost:5000/twilio
Twilio number +XX... pointed at wss://abc123.../twilio. Call it now.
```

## Make a call

With the proxy running, dial your Twilio number from any phone.

1. Twilio answers, plays the short greeting, then dials `FORWARD_TO_NUMBER`.
2. Answer the second phone. You're now on a normal two-way call.
3. Speak into either handset. Transcripts appear in the console within seconds:

```text
[outbound] This call is being transcribed.
[inbound ] Hello. Can you hear me?
[outbound] Hey, hey. Yes, loud and clear.
[inbound ] Awesome.
```

- `inbound`: whoever dialed your Twilio number.
- `outbound`: the party Twilio forwards to.
- Transcripts from the two channels interleave as they arrive, so a closing `.` or `?` can land on a later line.

Press `Ctrl-C` to stop the proxy. Your Twilio number's Voice URL stays pointed at the last ngrok tunnel; the next run overwrites it, so you never have to touch the Twilio Console after the first time.

## What the proxy does under the hood

1. **Receive Twilio's audio.** Twilio sends 20 ms of μ-law-encoded 8 kHz mono audio at a time (160 bytes per frame). Each frame arrives on the WebSocket as a JSON `media` event with a base64 `payload` and a `track` label (`inbound` or `outbound`). The proxy uses that label to keep the two speakers apart.
2. **Forward the audio to Speechmatics as-is.** The Realtime API accepts μ-law 8 kHz directly, so the proxy passes bytes straight through without re-encoding. That keeps latency down and avoids audio-quality loss.
3. **Ask Speechmatics for per-channel transcripts.** The session is configured with `diarization: "channel"` and channel labels `["inbound", "outbound"]`. Every transcript that comes back carries a `channel` field, and the proxy prints it under the matching label.

The proxy listens for the media stream on `/twilio` (see the startup banner) and serves the call instructions, including the greeting, on `/twiml`.

When adapting the proxy, see `speechmatics:realtime-transcription` for the Realtime API session and `speechmatics:transcription-features` for channel diarization.

## Troubleshooting

| Problem | What to try |
|---|---|
| `Missing required env vars in .env: ...` | Copy `.env.example` to `.env` at the repo root and fill in every listed value. Both languages read the same file |
| `Could not authenticate with Speechmatics: ...` | The proxy checks your key when it starts and exits if it's rejected, before it opens ngrok or changes your Twilio number. Check `SPEECHMATICS_API_KEY` in `.env` |
| `Twilio number ... not found on this account` | Check `TWILIO_PHONE_NUMBER` is in E.164 form (leading `+`, country code, no spaces) and belongs to the account whose SID and token you're using |
| Twilio Debugger shows `21219 - 'To' phone number not verified` | Your Twilio account is in trial mode. Add `FORWARD_TO_NUMBER` at [Verified Caller IDs](https://console.twilio.com/us1/develop/phone-numbers/manage/verified), or upgrade the account |
| The caller hears "an application error has occurred" | Open the [Twilio Debugger](https://console.twilio.com/us1/monitor/logs/debugger) for the specific error code. Confirm ngrok is still running and the URL in the startup banner matches your number's Voice URL in the Twilio Console |
| No transcripts appear | Confirm you heard the "This call is being transcribed" greeting, which proves Twilio reached `/twiml`. If not, the proxy isn't reachable. If yes but transcripts still don't come through, double-check `SPEECHMATICS_API_KEY` |

Still stuck: [Twilio support](https://support.twilio.com) or [contact Speechmatics](https://www.speechmatics.com/company/contact).

## Related docs

- Channel diarization: https://docs.speechmatics.com/speech-to-text/features/diarization
- Languages: https://docs.speechmatics.com/speech-to-text/languages
- Realtime API reference: https://docs.speechmatics.com/api-ref/realtime-transcription-websocket
- More integrations: https://github.com/speechmatics/speechmatics-academy
