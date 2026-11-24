# App analytics

Source: https://docs.speechmatics.com/speech-to-text/app-analytics

## What it is

If an application lets users enter their own Speechmatics API key, Speechmatics can offer the application's developer aggregated analytics about those users' usage levels. This includes:

- Number of unique users
- Hours processed
- Languages used
- And more

Requests are attributed to the application through an application ID sent as the `sm-app` query parameter.

## Setup

Contact support at https://support.speechmatics.com to get set up. Add `sm-app` to requests once setup is complete.

## Batch transcription

Add `sm-app` to the query string when starting a job:

```bash
APP_ID="YourAppID"
API_KEY="YOUR_API_KEY"
PATH_TO_FILE="example.wav"

curl -L -X POST "https://eu1.asr.api.speechmatics.com/v2/jobs/?sm-app=${APP_ID}" \
    -H "Authorization: Bearer ${API_KEY}" \
    -F data_file=@${PATH_TO_FILE} \
    -F config='{"type": "transcription","transcription_config": { "model": "enhanced","language": "en" }}'
```

## Realtime transcription

Add `sm-app` to the connection string when starting a session:

```text
wss://eu.rt.speechmatics.com/v2?sm-app=YourAppID
```

## Notes

- `API_KEY` here is the end user's own key; the application ID identifies the application, not the user.
- The docs show `sm-app` for Batch job creation and for the Realtime connection URL only.
- The docs do not show `sm-app` combined with a temporary key query parameter (`jwt`). If both are needed, test the combined query string before relying on it.
- App analytics is separate from workspace usage reporting. For usage in your own workspace, see `speechmatics:account-administration`.
- Use the regional hostname that suits the user; the examples use EU1. Endpoint list: `speechmatics:get-started`.
