# Vapi integration

Docs: https://docs.speechmatics.com/integrations-and-sdks/vapi

Vapi offers a native integration with Speechmatics for real-time STT in AI voice agents, with no code required. Speechmatics is embedded within the Vapi platform as a transcriber provider.

## What Speechmatics adds on Vapi

- **Native availability**: no separate setup beyond selecting the provider.
- **High accuracy and low latency**: an accurate, low-latency input layer for natural conversations, robust to background noise, diverse accents, and multiple speakers.
- **Speaker diarization**: Speechmatics is the only transcriber on Vapi that provides speaker diarization, labeling who said what in multi-speaker scenarios.

Typical uses: task automation, live call analysis, hands-free control, global voice support, interactive conversational bots.

## Requirements

- Vapi account (https://vapi.ai)
- Vapi private key (https://dashboard.vapi.ai)
- Speechmatics account (https://portal.speechmatics.com)

## Dashboard setup

1. Go to the assistants tab in the Vapi dashboard.
2. Choose an existing assistant or create a new one.
3. Open the transcriber tab, or scroll down to the transcriber module settings.
4. Select Speechmatics in the provider dropdown menu.
5. Optional: add your own Speechmatics API key (generated at https://portal.speechmatics.com/settings/api-keys) in the Vapi dashboard under Provider Keys (https://dashboard.vapi.ai/settings/integrations/speechmatics).

## Python usage

Set `VAPI_API_KEY` to your Vapi private key.

```python
import os
from vapi import Vapi
from vapi.types import SpeechmaticsTranscriber

client = Vapi(token=os.environ["VAPI_API_KEY"])

assistant = client.assistants.create(
    name="Speechmatics Quickstart",
    transcriber=SpeechmaticsTranscriber(
        provider="speechmatics",
        language="en",
    ),
)

print(f"Assistant ID: {assistant.id}")
```

The docs show only `provider` and `language` on `SpeechmaticsTranscriber`. For other transcriber fields, consult Vapi's own documentation rather than guessing names.

## Best practices

- **Model**: select the Enhanced model for the best accuracy in real-time voice agents.
- **Region**: choose the region closest to your users to reduce latency (regions: https://docs.speechmatics.com/administration/regions).
- **Custom vocabulary**: add key terms (product names, medical terminology) and use the "sounds like" option for tricky pronunciations.

More examples: https://github.com/speechmatics/speechmatics-academy
