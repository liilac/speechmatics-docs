# Images and licensing

Docs: https://docs.speechmatics.com/deployments/container/accessing-images and https://docs.speechmatics.com/deployments/container/licensing

Tags below are current at time of writing; check the docs.

## Contents

- Registry access
- CPU transcriber images
- GPU inference server images (Standard and Enhanced)
- Melia 1 and Oak 1 images
- Translation, bilingual, language ID and usage images
- License file and how to apply it

## Registry access

You need:

- Speechmatics Docker repository credentials (from [Support](https://support.speechmatics.com))
- The ISO language code, for example `fr` for French
- `LICENSE_TOKEN`: the signed claims token inside the license file
- `TAG`: the image version

```bash
docker login https://speechmaticspublic.azurecr.io
```

Enter the supplied username and password. Success prints `Login Succeeded`.

Speechmatics requires all customers to cache a copy of the images in their own environment. After the first pull, re-host the image in a private container registry and reference that registry in deployments.

Container release information is in the knowledge base section of the [Support Portal](https://support.speechmatics.com).

## CPU transcriber images

One image per language pack. Repeat the pull for each language code.

```bash
# Batch Global English (en)
docker pull speechmaticspublic.azurecr.io/batch-asr-transcriber-en:17.1.0

# Batch Spanish (es)
docker pull speechmaticspublic.azurecr.io/batch-asr-transcriber-es:17.1.0

# Realtime Global English (en)
docker pull speechmaticspublic.azurecr.io/rt-asr-transcriber-en:17.1.0
```

Naming: `batch-asr-transcriber-<lang>` and `rt-asr-transcriber-<lang>`.

## GPU inference server images (Standard and Enhanced)

Required for the most accurate models. For additional language configurations, contact Support.

| Image | Models | Languages |
|---|---|---|
| `sm-gpu-inference-server-standard-all` | Standard | All |
| `sm-gpu-inference-server-en` (also `es`, `de`, `fr`) | Standard and Enhanced | That language |
| `sm-gpu-inference-server-enhanced-recipe1` | Enhanced | Language pack 1 |
| `sm-gpu-inference-server-enhanced-recipe2` | Enhanced | Language pack 2 |
| `sm-gpu-inference-server-enhanced-recipe3` | Enhanced | Language pack 3 |
| `sm-gpu-inference-server-enhanced-recipe4` | Enhanced | Language pack 4 |
| `sm-gpu-inference-server-all-lang` | Standard and Enhanced | All |

```bash
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-standard-all:17.1.0
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-en:17.1.0
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-enhanced-recipe1:17.1.0
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-enhanced-recipe2:17.1.0
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-enhanced-recipe3:17.1.0
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-enhanced-recipe4:17.1.0
docker pull speechmaticspublic.azurecr.io/sm-gpu-inference-server-all-lang:17.1.0
```

Enhanced language packs:

| Pack | Languages |
|---|---|
| 1 (`recipe1`) | Bashkir, Basque, Belarusian, English, Esperanto, Irish, Malay & English bilingual, Mandarin & English bilingual, Mandarin Malay Tamil & English multilingual, Marathi, Mongolian, Tamil, Tamil & English bilingual, Turkish, Ukrainian, Uyghur, Welsh |
| 2 (`recipe2`) | Bulgarian, Croatian, Estonian, Galician, Indonesian, Interlingua, Latvian, Lithuanian, Persian, Romanian, Slovakian, Slovenian, Spanish, Tagalog, Urdu |
| 3 (`recipe3`) | Arabic & English bilingual, Catalan, Czech, Danish, Finnish, German, Greek, Hebrew, Hindi, Hungarian, Italian, Korean, Malay, Swahili, Swedish |
| 4 (`recipe4`) | Arabic, Bengali, Cantonese, Dutch, French, Japanese, Maltese, Mandarin, Norwegian, Polish, Portuguese, Russian, Thai, Vietnamese |

The `all-lang` image contains both models and all languages. To load one model use `SM_MODEL`; to load some languages use `SM_LANGUAGES`. See [gpu-inference.md](gpu-inference.md).

## Melia 1 and Oak 1 images

Melia 1 and Oak 1 are multilingual, GPU-only models for Batch and Realtime. The same transcriber and inference server images serve both models and both modes.

```bash
docker pull speechmaticspublic.azurecr.io/sm-asr-transcriber:1.13.0
docker pull speechmaticspublic.azurecr.io/sm-asr-inference-server:1.13.0
```

## Translation image

Required for translation in Batch or Realtime. One image supports all translation pairs.

```bash
docker pull speechmaticspublic.azurecr.io/sm-translation-inference-server:17.1.0
```

## Bilingual images

Spanish and English bilingual transcription needs the CPU image below as the client plus the Spanish GPU inference server. Bilingual is GPU-only; Batch and Realtime are supported.

```bash
docker pull speechmaticspublic.azurecr.io/batch-asr-transcriber-es-bilingual-en:17.1.0
docker pull speechmaticspublic.azurecr.io/rt-asr-transcriber-es-bilingual-en:17.1.0
```

## Language ID image

```bash
docker pull speechmaticspublic.azurecr.io/langid:2.2.1
```

## Usage container image

```bash
docker pull speechmaticspublic.azurecr.io/asr-usage:0.5.3
```

## License file

Get a license from [Support](https://support.speechmatics.com). Licensing needs no network access and works offline.

```json
{
  "contractid": 1,
  "creationdate": "2020-03-24 17:43:35",
  "customer": "Speechmatics",
  "id": "c18a4eb990b143agadeb384cbj7b04c3",
  "is_trial": true,
  "metadata": {
    "key_pair_id": 1,
    "request": {
      "customer": "Speechmatics",
      "features": ["MAPBA", "LANY"],
      "isTrial": true,
      "notValidAfter": "2021-01-01",
      "validFrom": "2020-01-01"
    }
  },
  "signedclaimstoken": "exampleClaimsToken"
}
```

- `validFrom` and `notValidAfter` bound the license: valid from 00:00 UTC on the start date to 00:00 UTC on the expiry date.
- After expiry the container keeps running but does not transcribe. Request a new license before then.
- `features` lists the licensed features. A language ID license example in the docs lists `["MAPBA", "ALID"]`.
- Not all licenses cover all features. Translation and language ID must be enabled in the license.

## Applying the license

Volume-map the file to `/license.json`:

```bash
docker run -v ./my_license.json:/license.json batch-asr-transcriber-en:17.1.0
```

Or copy the `signedclaimstoken` value (without quotation marks) into `LICENSE_TOKEN`:

```bash
docker run -e LICENSE_TOKEN=exampleClaimsToken batch-asr-transcriber-en:17.1.0
```

If both are provided, the volume-mapped file is ignored.

Which containers need a license:

| Container | License |
|---|---|
| Batch and Realtime transcribers | Required |
| Standard/Enhanced and Melia 1/Oak 1 GPU inference servers | No specific license; runs with an existing Batch or Realtime container license. The docs examples mount `license.json` into the server |
| Translation inference server | None, but the client transcriber's license must have translation enabled |
| Language ID | Required, with language ID enabled |

License error messages: [troubleshooting.md](troubleshooting.md).
