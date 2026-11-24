# Speechmatics plugin for Claude Code

Agent Skills that teach Claude how to build with Speechmatics. The skills are written from the documentation in this repository.

## Install

Add this repository as a plugin marketplace, then install the plugin:

```bash
claude plugin marketplace add liilac/speechmatics-docs
```

```bash
claude plugin install speechmatics@speechmatics
```

Inside a Claude Code session, use `/plugin marketplace add liilac/speechmatics-docs` and `/plugin install speechmatics@speechmatics` instead.

## Skills

Claude loads a skill when a request matches its description. To invoke one directly, type `/speechmatics:<skill-name>`.

| Skill | Use it to |
|---|---|
| `get-started` | Choose a product and model, authenticate, pick a region and language, and install an SDK |
| `batch-transcription` | Transcribe pre-recorded files with the Batch API |
| `speech-intelligence` | Add summarization, sentiment analysis, topic detection, and auto chapters to a batch job |
| `realtime-transcription` | Transcribe live audio with the Realtime API |
| `agent-stt` | Get turn-based transcription for a voice agent with agent STT |
| `transcription-features` | Configure diarization, custom dictionary, translation, Entity Detection, PII Redaction, audio events, and formatting |
| `text-to-speech` | Generate speech with the Text to Speech API |
| `voice-agent-integrations` | Use Speechmatics with LiveKit, Pipecat, Twilio, Vapi, the Voice SDK, and Zapier |
| `container-deployment` | Run Speechmatics containers on-prem, including GPU inference and usage reporting |
| `kubernetes-deployment` | Deploy Speechmatics on Kubernetes with the Helm chart |
| `virtual-appliance` | Install and administer the virtual appliance |
| `account-administration` | Manage workspaces, projects, members, API keys, billing, and usage |
| `accuracy-benchmarking` | Measure Word Error Rate (WER) and benchmark transcription accuracy |

## Default region

The skills default to the AU1 (Australia) endpoints: `au1.asr.api.speechmatics.com` for the Batch API and `au.rt.speechmatics.com` for the Realtime API and agent STT. The docs samples use EU1. To change the default, edit the "Regions and endpoints" section of `skills/get-started/SKILL.md` and the sample hostnames in the other skills.

## Maintain

Each skill lives in `skills/<skill-name>/`. `SKILL.md` holds the core instructions, and `references/` holds the detail Claude reads on demand.

When a docs page changes, update the skill that covers it. Validate the plugin before you commit:

```bash
claude plugin validate . --strict
```

## Test

`evals/cases/` holds four prompts per skill, each with the facts a correct answer must contain. The runner sends each prompt to `claude -p` and checks that Claude loads the expected skill and gives those facts. Install the plugin first, then run:

```bash
python3 claude-plugins/speechmatics/evals/run.py
```

Pass a filter to run one skill, for example `run.py batch`. Each case is a real Claude request, so a full run costs a few dollars.
