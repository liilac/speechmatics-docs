# Licensing

Docs:

- https://docs.speechmatics.com/deployments/virtual-appliance/installation/licensing
- https://docs.speechmatics.com/deployments/virtual-appliance/installation/license-features

The virtual appliance uses a license identical to the one used by the Speechmatics containers.

All Management API requests need authentication unless it is explicitly turned off. The default username and password are `admin` and `admin`.

## Apply a license

Upload the license file, or paste it into the Management API web interface:

```bash
curl -L -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/license" -d @license.json
```

Only basic validation happens when the license is applied. See [Troubleshooting](#troubleshooting).

## Check the license

```bash
curl -L -u admin:admin -X 'GET' "http://${APPLIANCE_HOST}/v2/management/license" | jq
```

Returns 404 if no license is present. Otherwise:

```json
{
  "comment": "",
  "contractid": 1001,
  "creationdate": "2022-10-24 11:11:49",
  "customer": "Speechmatics",
  "id": "bb6df75951b14855ab654a09e6d00d80",
  "licensetype": "Evaluation",
  "metadata": {
    "key_pair_id": 1,
    "request": {
      "comment": "",
      "contractid": 1001,
      "customer": "Speechmatics",
      "features": ["MAPRT", "MAPBA", "LANY"],
      "notValidAfter": "2024-10-16",
      "validFrom": "2022-10-24"
    }
  },
  "signedclaimstoken": "ey..._w",
  "unitquantity": "",
  "unittype": "",
  "version": 1
}
```

Read the response as follows:

- `id`: unique license ID.
- `metadata.request.notValidAfter`: expiry date.
- `metadata.request.validFrom`: start date.
- `metadata.request.features`: licensed feature codes. The example allows batch (`MAPBA`) and realtime (`MAPRT`) modes in any language (`LANY`).

## Remove the license

Removing the license stops the appliance from transcribing:

```bash
curl -L -u admin:admin -X 'DELETE' \
    "http://${APPLIANCE_HOST}/v2/management/license" \
    | jq
```

## License feature codes

Some appliance features must be specifically licensed.

| Feature code | Description |
| --- | --- |
| `MAPBA` | Batch transcription |
| `MAPRT` | Realtime transcription (listed as currently not available in appliances) |
| `APR` | Custom dictionary |
| `ASS` | Speaker change |
| `APD` | Speaker diarization |
| `AOP2` | Enhanced operating point |
| `ALID` | Language identification |
| `ATRA` | Translation (currently not available in appliances) |
| `LANY` | Transcription in any language |
| `L*` | Transcription in specific languages: `LEN` is English, `LDE` is German, `LES` is Spanish, and so on |

The feature list marks `MAPRT` as currently not available in appliances, while other pages document a Realtime appliance in early access. Confirm Realtime licensing with Support.

## Usage reporting

- Online: if `usage.speechmatics.com` is reachable, usage reports are submitted there. Automatic (online) usage reporting is on by default and is opt out. See https://docs.speechmatics.com/deployments/usage-reporting/automatic.
- Offline: configure the appliance to run in offline mode. See https://docs.speechmatics.com/deployments/usage-reporting/offline.

Set the usage mode (`offline` or `online`):

```bash
curl -L -u admin:admin -X 'POST' \
  "http://${APPLIANCE_HOST}/v2/management/usagereporting" \
  -d '{"mode": "offline"}'
```

### Offline mode and exporting usage data

In `offline` mode a container inside the appliance collects usage. Recommended workflow:

1. Set the usage mode to `offline` before running any jobs.
2. At intervals of no more than a calendar month, export the usage data from each running appliance.
3. Email the unmodified export to billing-reporting@speechmatics.com.

Export a compressed archive:

```bash
curl -X 'GET' \
  "http://${APPLIANCE_HOST}/v1/export?since={start_time}&until={end_time}" \
  -H 'accept: application/gzip'
```

- `start_time` and `end_time` are inclusive ISO-8601 timestamps (`YYYY-MM-DDTHH:MM:SSZ`).
- Data is retained in the appliance for 90 days, then purged.
- The export is in compressed `json.gz` format. Send it in that format and do not modify it.
- To stay under the 25MB email attachment limit, chunk exports by time range (25MB is usually around 10,000 batch jobs or 1250 one-hour Realtime sessions).
- In `realtime` mode, usage for contract ID `-77777777777777` is a prewarming job from the transcriber's first startup and is not billed.

### Use a proxy server

Set a proxy for reaching `usage.speechmatics.com` in the `usagereporting` call:

```bash
curl -L -u admin:admin -X 'POST' \
  "https://${APPLIANCE_HOST}/v2/management/usagereporting" \
  -H 'Content-Type: application/json' \
  -d '{
  "mode": "online",
  "proxy": "https://proxy.example.com:3128/"
}'
```

| Field | Values |
| --- | --- |
| `mode` | `online` or `offline` |
| `proxy` | Proxy URL. May include credentials: `https://USER:PASS@proxy.example.com/` |

The proxy sets the `http_proxy` and `https_proxy` environment variables when the transcription process launches. In `offline` mode the proxy setting has no effect.

## Troubleshooting

### Invalid license

Runtime license errors are reported by the transcriber container running inside the appliance, not at upload time. If one occurs, contact [Support](https://support.speechmatics.com) with the full job log output and the license as reported by the appliance.

### Transcriber not starting

The transcriber needs a license before it can start. An unlicensed Realtime appliance reports `realtime_inference` as `unhealthy` on `/v2/management/health`.
