# Zapier integration

Docs: https://docs.speechmatics.com/integrations-and-sdks/zapier

The Speechmatics Zapier integration is in beta. Features and behavior may change.

[Zapier](https://zapier.com) is a no-code automation platform. Speechmatics is available as an action in Zaps: trigger from any app, send the transcript to any downstream step.

## Prerequisites

- A Speechmatics API key from the portal (https://portal.speechmatics.com).
- A Zapier account.

## Actions

| Action | What it does | Best for |
|---|---|---|
| **Get Transcript from Audio** | Sends audio to Speechmatics and returns the transcript inside the Zap | Short audio. Keeping the transcript in Zapier |
| **Submit Audio (Webhook)** | Sends audio to Speechmatics and delivers the finished transcript to a webhook URL you provide | Longer recordings. Sending the transcript to another system asynchronously |

## Build a Zap

1. Sign in to the [Zap dashboard](https://zapier.com/app/assets/zaps) and click **Create** to open a blank Zap in the editor.
2. **Set up a trigger**: pick the app whose event starts the Zap, for example a new file shared in Slack. Zapier might prompt you to sign in, and some apps need additional account permissions.
3. **Add the Speechmatics action**: click the Action box, search for Speechmatics, and choose an action (the docs example uses **Get Transcript from Audio**).
4. **Connect your account**: paste your API key into the Account section.
5. **Configure**: on the **Configure** tab, connect the trigger's file URL to the **Audio URL** field. Depending on the trigger app, that field might be called something like `/file` or `/url`; you may need to experiment to find it.
6. Set the transcription settings below.
7. **Test**: open the **Test** tab and click **Test Step**. Zapier validates the configuration and runs it.
8. When the test succeeds, click **Publish**. The Zap is live.

## Transcription settings

| Setting | What it does | Learn more |
|---|---|---|
| **Language hints** | Optional. Speechmatics auto-detects the language by default. Use hints to narrow detection to specific languages: search the dropdown by name, or type a language code | https://docs.speechmatics.com/speech-to-text/languages |
| **Speaker diarization** | Separates the transcript by speaker | https://docs.speechmatics.com/speech-to-text/features/diarization |
| **Output format** | Controls the shape of the returned transcript | https://docs.speechmatics.com/speech-to-text/batch/output |

## Troubleshooting

| Problem | What to try |
|---|---|
| You can't sign in to Speechmatics | Sign out from the Speechmatics account dropdown, then sign in again. If that fails, verify your login details in the portal |
| Your API key isn't accepted | Check that your account has credits in the usage and billing section of the portal |
| You can't find the right field for Audio URL | Field paths start with `/`; Zapier uses this to map fields between triggers and actions. Names vary by app; try `/file`, `/url`, or similar |
| Your test step keeps failing | Confirm you're passing an audio file, not another file type. To rule out a file problem, test with this [sample audio file](https://github.com/speechmatics/speechmatics-js-sdk/raw/7d219bfee9166736e6aa21598535a194387b84be/examples/nodejs/example.wav) |

Still stuck: [Zapier support](https://help.zapier.com/hc/en-us) or [contact Speechmatics](https://www.speechmatics.com/company/contact).

## Related docs

- Batch API capabilities: https://docs.speechmatics.com/speech-to-text/batch/quickstart
- Output formats: https://docs.speechmatics.com/speech-to-text/batch/output
