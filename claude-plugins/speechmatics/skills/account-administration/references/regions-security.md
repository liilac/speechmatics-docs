# Regions, data handling, security, and compliance

Sources:

- https://docs.speechmatics.com/administration/regions
- https://docs.speechmatics.com/administration/security-and-compliance
- https://docs.speechmatics.com/get-started/authentication#supported-endpoints

## Regions

A region is the location where audio is processed. Each region is reached through its own API endpoint, so the endpoint called determines the region. Whether anything is stored depends on the processing mode, not the region.

### Available regions

Available to all customers:

- EU1 (Europe)
- US1 (United States)
- AU1 (Australia)

Batch and Realtime are both available in all three.

### Endpoint hostnames

| Region | Batch | Realtime and agent STT |
|---|---|---|
| EU1 | `eu1.asr.api.speechmatics.com` | `eu.rt.speechmatics.com` |
| US1 | `us1.asr.api.speechmatics.com` | `us.rt.speechmatics.com` |
| AU1 | `au1.asr.api.speechmatics.com` | `au.rt.speechmatics.com` |
| EU2 (enterprise only) | `eu2.asr.api.speechmatics.com` | N/A |
| US2 (enterprise only) | `us2.asr.api.speechmatics.com` | N/A |
| Global (auto-routed) | N/A | `global.rt.speechmatics.com` |

- `global.rt.speechmatics.com` routes each connection to the nearest region and may route to any region. With data residency or compliance requirements, use a regional endpoint.
- EU2 and US2 are for enterprise high availability and failover only. Jobs created there are not visible in the portal.

### Select a region

- Portal: use the **Region** selector in the top navigation. It sets the region for transcription started from the portal.
- API: the endpoint called determines the region. A job is created in the region of the endpoint used, and all requests relating to that job must use the same endpoint.

### Use multiple regions

Use more than one region to balance load or to fail over if one region is disrupted. Each job belongs to the region it was created in, so retrieve a job from the same region that created it.

Enterprise customers may have region arrangements set in their contract. To use a different region, contact the account manager or support (https://support.speechmatics.com).

### Regions and workspaces

A workspace is not tied to a region. Members of the same workspace can submit work to different regions.

### Regions and temporary keys

Batch temporary keys are valid in one region (`region`: `eu` default, `usa`, `au`). Realtime temporary keys work in every region. See `speechmatics:get-started`.

### Preview endpoint

Preview mode traffic is not served from a hosted region and has no data residency guarantees; data may be processed in either the US or the EU. See `speechmatics:get-started`.

## Data handling

How long data is stored depends on the processing mode:

- Realtime: audio is streamed over a WebSocket and is never recorded or stored. Transcripts are streamed back as they are produced and then discarded. Processing happens in memory.
- Batch: audio files, transcripts, and job configuration are stored for 7 days, then deleted automatically. Delete them sooner with the API: https://docs.speechmatics.com/api-ref/batch/delete-a-job (see `speechmatics:batch-transcription`).

Related settings:

- Model training (data logging), an opt-in on Pro that lets Speechmatics use anonymized data to improve models in exchange for a discount. Toggle it in **Manage workspace**. It applies to future usage only.
- Deleting a project permanently removes its transcripts, usage history, and API keys.

## Certifications and compliance standards

- ISO/IEC 27001:2022
- SOC 2 Type II
- GDPR
- HIPAA

Overview of how Speechmatics protects data: https://www.speechmatics.com/security

## Request compliance documentation

Certificates and reports are distributed through the Speechmatics Trust Center: https://speechmatics.safebase.us/

1. Request access in the Trust Center.
2. Agree to the non-disclosure agreement.
3. Download the documents needed.

Access is reviewed and granted by the Speechmatics security team.

## Guidance for residency-sensitive integrations

- Pin to a regional hostname. Do not use `global.rt.speechmatics.com`.
- Keep every request for a Batch job on the endpoint that created it.
- Mint Batch temporary keys with the matching `region`.
- Do not use the preview endpoint.
- For full control over data location, on-prem deployment is available on the Enterprise plan (`speechmatics:container-deployment`, `speechmatics:kubernetes-deployment`, `speechmatics:virtual-appliance`).
