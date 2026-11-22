# Languages and language codes

Source: https://docs.speechmatics.com/speech-to-text/languages

## How language selection works

- The languages, packs, and options here apply to the Enhanced and Standard models. Set the code as `language` in `transcription_config`.
- Melia 1 and Oak 1 are multilingual. Set `"language": "multi"`; they transcribe the individual languages below and switch automatically. Use the codes below as language hints on Batch and Realtime. They do not support `auto`, the bilingual and multi-language pack codes, or translation.
- Agent STT uses Linden 1, which supports the same languages as Realtime transcription. Translation is not available.
- Codes are two-letter ISO 639-1 or three-letter ISO 639-3, in requests and responses.
- Speechmatics is global-first: one language pack covers many accents and dialects. There are no accent-specific packs. To standardize spelling (for example US versus British English, or Simplified versus Traditional Mandarin), set the output locale. See `speechmatics:transcription-features`.
- Availability depends on the languages you are contracted to use.
- To detect the language of a file automatically, use language identification (Batch only). See `speechmatics:batch-transcription`.
- To discover current languages and features programmatically, use the feature discovery endpoint. See `speechmatics:transcription-features`.

## Transcription languages

| Language | Code | Notes |
|---|---|---|
| Automatic | `auto` | Detects the language with language identification. Batch only. |
| Arabic | `ar` | Global Arabic: many accents and dialects, including Modern Standard Arabic and Arabic spoken in the Gulf, Egypt, and the Levant. |
| Arabic and English bilingual | `ar_en` | Arabic and English in the same file or stream. |
| Bashkir | `ba` | |
| Basque | `eu` | |
| Belarusian | `be` | |
| Bengali | `bn` | |
| Bulgarian | `bg` | |
| Cantonese | `yue` | |
| Catalan | `ca` | |
| Croatian | `hr` | |
| Czech | `cs` | |
| Danish | `da` | |
| Dutch | `nl` | |
| English | `en` | Global English: UK, US, Australia, New Zealand, non-native speakers, and more. Set the output locale to standardize spelling. |
| Esperanto | `eo` | |
| Estonian | `et` | |
| Finnish | `fi` | |
| French | `fr` | Global French: France, Canada, Belgium, and more. |
| Galician | `gl` | |
| German | `de` | Global German: Germany, Austria, Switzerland, and more. |
| Greek | `el` | |
| Hebrew | `he` | |
| Hindi | `hi` | |
| Hungarian | `hu` | |
| Indonesian | `id` | |
| Interlingua | `ia` | |
| Irish | `ga` | |
| Italian | `it` | |
| Japanese | `ja` | |
| Korean | `ko` | |
| Latvian | `lv` | |
| Lithuanian | `lt` | |
| Malay | `ms` | |
| Malay and English bilingual | `en_ms` | Malay and English in the same file or stream. |
| Maltese | `mt` | |
| Mandarin | `cmn` | Global Mandarin: China, Taiwan, Singapore, Malaysia, and more. Outputs Traditional or Simplified characters via the output locale. |
| Mandarin and English bilingual | `cmn_en` | Mandarin and English in the same file or stream. |
| Mandarin Malay Tamil and English | `cmn_en_ms_ta` | All four languages in the same file or stream. |
| Marathi | `mr` | |
| Mongolian | `mn` | |
| Norwegian | `no` | |
| Persian | `fa` | |
| Polish | `pl` | |
| Portuguese | `pt` | Global Portuguese: Portugal, Brazil, and more. |
| Romanian | `ro` | |
| Russian | `ru` | |
| Slovakian | `sk` | |
| Slovenian | `sl` | |
| Spanish | `es` | Global Spanish: Spain, the US, Mexico, Colombia, Argentina, Venezuela, Chile, Peru, and more. |
| Spanish and English bilingual | `es` with `"domain": "bilingual-en"` | Spanish and English in the same file or stream. Requires the `domain` property. |
| Swahili | `sw` | |
| Swedish | `sv` | |
| Tagalog (Filipino) and English bilingual | `tl` | Tagalog and English in the same file or stream. |
| Tamil | `ta` | |
| Tamil and English bilingual | `en_ta` | Tamil and English in the same file or stream. |
| Thai | `th` | |
| Turkish | `tr` | |
| Ukrainian | `uk` | |
| Urdu | `ur` | |
| Uyghur | `ug` | |
| Vietnamese | `vi` | |
| Welsh | `cy` | With language identification, add Welsh explicitly to the expected languages list, or a "language not supported for transcription" error is returned. |

## Bilingual and multi-language packs

Enhanced and Standard can transcribe a selected, fixed combination of languages in one file or stream, including speakers who switch between the languages in that pack.

| Language pack | Transcription config |
|---|---|
| Arabic and English | `{"language": "ar_en"}` |
| Malay and English | `{"language": "en_ms"}` |
| Mandarin and English | `{"language": "cmn_en"}` |
| Mandarin Malay Tamil and English | `{"language": "cmn_en_ms_ta"}` |
| Spanish and English | `{"language": "es", "domain": "bilingual-en"}` |
| Tamil and English | `{"language": "en_ta"}` |
| Tagalog (Filipino) and English | `{"language": "tl"}` |

Mandarin and English:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "cmn_en"
  }
}
```

Spanish and English (requires `domain`):

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "es",
    "domain": "bilingual-en"
  }
}
```

To transcribe without selecting languages in advance, including spontaneous switching across all supported languages, use Melia 1, or Oak 1 for healthcare audio. See [models.md](models.md).

## Medical languages

Two models are tuned for healthcare audio: Enhanced Medical (`"model": "enhanced"`, `"domain": "medical"`, one selected language) and Oak 1 (`"model": "oak-1"`, `"language": "multi"`, automatic language detection).

| Language | Enhanced Medical | Oak 1 |
|---|---|---|
| Arabic | No | Available |
| Arabic and English | Available | No |
| Danish | Available | Available |
| Dutch | Available | Available |
| English | Available | Available |
| Finnish | Available | Available |
| French | Available | Available |
| German | Available | Available |
| Norwegian | Available | Available |
| Polish | No | Available |
| Spanish | Available | Available |
| Swedish | Available | Available |
| Additional languages | Contact sales | Contact sales |

- Outside this table, Enhanced Medical falls back to the standard Enhanced model, which still delivers high accuracy on healthcare audio without the medical tuning.
- Oak 1 transcribes all the individual languages in the transcription table regardless. This table lists only where Oak 1 has the additional medical terminology uplift (procedures, medications, conditions, anatomy).
- Contact sales: https://www.speechmatics.com/speak-to-sales

## Translation languages

Translation is available with the Enhanced and Standard models only. Configuration lives in `speechmatics:transcription-features`.

| Audio language | Translation target language |
|---|---|
| English (`en`) | Bulgarian (`bg`), Catalan (`ca`), Mandarin (`cmn`), Czech (`cs`), Danish (`da`), German (`de`), Greek (`el`), Spanish (`es`), Estonian (`et`), Finnish (`fi`), French (`fr`), Galician (`gl`), Hindi (`hi`), Croatian (`hr`), Hungarian (`hu`), Indonesian (`id`), Italian (`it`), Japanese (`ja`), Korean (`ko`), Lithuanian (`lt`), Latvian (`lv`), Malay (`ms`), Dutch (`nl`), Norwegian (`no`), Polish (`pl`), Portuguese (`pt`), Romanian (`ro`), Russian (`ru`), Slovakian (`sk`), Slovenian (`sl`), Swedish (`sv`), Turkish (`tr`), Ukrainian (`uk`), Vietnamese (`vi`) |
| Any language in the list above (`bg`, `ca`, `cmn`, `cs`, `da`, `de`, `el`, `es`, `et`, `fi`, `fr`, `gl`, `hi`, `hr`, `hu`, `id`, `it`, `ja`, `ko`, `lt`, `lv`, `ms`, `nl`, `no`, `pl`, `pt`, `ro`, `ru`, `sk`, `sl`, `sv`, `tr`, `uk`, `vi`) | English (`en`) |
| Norwegian Bokmål (`no`) | Norwegian Nynorsk (`nn`) |

## Quick rules

| Situation | Config |
|---|---|
| One known language | `"language": "<code>"` with `standard` or `enhanced` |
| Unknown single language, Batch | `"language": "auto"` with `standard` or `enhanced` |
| Fixed known language pair with a pack | The pack code, with `standard` or `enhanced` |
| Arbitrary or spontaneous language switching | `"model": "melia-1"`, `"language": "multi"` |
| Multilingual healthcare audio | `"model": "oak-1"`, `"language": "multi"` |
| Single-language healthcare audio | `"model": "enhanced"`, `"domain": "medical"` |
| Agent STT | `"model": "linden-1"`, `"language": "<code>"` |
