# Entity Detection and PII Redaction

Docs:

- https://docs.speechmatics.com/speech-to-text/features/entity-detection
- https://docs.speechmatics.com/speech-to-text/features/pii-redaction
- https://docs.speechmatics.com/speech-to-text/features/entity-detection-classes
- All parameters: https://docs.speechmatics.com/api-ref/batch/create-a-new-job

Both features are available in Batch only. Not available in Realtime or agent STT.

## Entity Detection

Finds potentially sensitive data (names, dates of birth, health conditions, credit card numbers) and labels each value with an entity class.

### Enable

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en",
    "enable_entities": true,
    "entities_config": {
      "detect_advanced_entities": true
    }
  }
}
```

`entities_config` is only accepted when `enable_entities` is `true`.

### Output

For "Mark was born on the 25th of July 2000." (timings omitted):

```json
{
  "results": [
    {
      "type": "entity",
      "entity_class": "name_given",
      "alternatives": [{ "content": "Mark", "speaker": "S1" }]
    },
    { "type": "word", "alternatives": [{ "content": "was", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "born", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "on", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "the", "speaker": "S1" }] },
    {
      "type": "entity",
      "entity_class": "dob",
      "alternatives": [{ "content": "25th of July 2000", "speaker": "S1" }]
    },
    { "type": "punctuation", "alternatives": [{ "content": ".", "speaker": "S1" }] }
  ]
}
```

Each detected value has `type` `entity` and an `entity_class`. Entity Detection returns the most specific class that applies.

### Entity Detection versus smart formatting entities

`enable_entities` returns one of two kinds of entities. A job returns one kind or the other, not both.

| | Smart formatting entities | Entity Detection |
|---|---|---|
| Configuration | `enable_entities: true` | `enable_entities: true` and `entities_config.detect_advanced_entities: true` |
| Entity classes | `cardinal`, `date`, `money`, `percentage` and other smart formatting classes (see [formatting.md](formatting.md#smart-formatting-classes)) | Entity Detection classes such as `name_given`, `dob`, `credit_card` |
| `spoken_form` and `written_form` | Included | Not included |
| Models | Standard and Enhanced | All models |

On Melia 1 and Oak 1, `enable_entities` is only accepted with `detect_advanced_entities` set to `true`.

## PII Redaction

Replaces each sensitive value in a Batch transcript with a label for its entity class, such as `[name_given]`. Original values are removed throughout the JSON transcript.

### Enable

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en",
    "enable_redaction": true,
    "redaction_config": {
      "entity_classes": ["gdpr"]
    }
  }
}
```

If `enable_redaction` is `true` and `redaction_config.entity_classes` is missing, the job is rejected. Per `spec/batch.yaml`, `entity_classes` needs at least one item and items must be unique.

### Choose what to redact

Each value in `entity_classes` is an entity class group or a specific entity class. Mix freely.

- Regulation groups: `gdpr`, `gdpr_sensitive`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi`, `appi_sensitive`.
- Data type groups: `health`, `pci`, `pii`.
- Specific classes: for example `name_given`, `dob`, `credit_card`. A general class such as `name` or `location` also redacts its subclasses.

Start from the regulation group matching the compliance requirement, then add specific classes.

```json
{
  "type": "transcription",
  "transcription_config": {
    "language": "en",
    "enable_redaction": true,
    "redaction_config": {
      "entity_classes": ["gdpr", "name_given", "credit_card"]
    }
  }
}
```

`pii` is broad: it includes dates, times, amounts of money and organization names. Use it only when all of those should be removed.

### Redacted output

```json
{
  "results": [
    { "type": "word", "alternatives": [{ "content": "[name_given]", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "was", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "born", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "on", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "the", "speaker": "S1" }] },
    { "type": "word", "alternatives": [{ "content": "[dob]", "speaker": "S1" }] },
    { "type": "punctuation", "alternatives": [{ "content": ".", "speaker": "S1" }] }
  ]
}
```

### Combining with Entity Detection

- PII Redaction works on its own.
- Enable Entity Detection in the same job to return redacted values as `entity` results with an `entity_class`.
- If `enable_entities` is `true` in a redaction job, `entities_config.detect_advanced_entities` must also be `true`, or the job is rejected.
- PII Redaction cannot be combined with smart formatting entities.
- With PII Redaction enabled the transcript has no `spoken_form` or `written_form`.

### Python sample

```python
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError

API_KEY = "YOUR_API_KEY"
PATH_TO_FILE = "example.wav"
LANGUAGE = "en"  # Transcription language

settings = ConnectionSettings(
    url="https://au1.asr.api.speechmatics.com/v2",
    auth_token=API_KEY,
)

# Define transcription parameters
conf = {
    "type": "transcription",
    "transcription_config": {
        "language": LANGUAGE,
        "enable_redaction": True,
        "redaction_config": {"entity_classes": ["gdpr"]},
    },
}

# Open the client using a context manager
with BatchClient(settings) as client:
    try:
        job_id = client.submit_job(
            audio=PATH_TO_FILE,
            transcription_config=conf,
        )
        print(f"job {job_id} submitted successfully, waiting for transcript")

        # Note that in production, you should set up notifications instead of polling.
        # Notifications are described here: https://docs.speechmatics.com/speech-to-text/batch/notifications
        transcript = client.wait_for_completion(job_id, transcription_format="json-v2")
        print(transcript["results"])  # print the redacted results
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key - Check your API_KEY at the top of the code!")
        elif e.response.status_code == 400:
            print(e.response.json()["detail"])
        else:
            raise e
```

## Supported languages

Entity Detection and PII Redaction support all transcription languages (https://docs.speechmatics.com/speech-to-text/languages#transcription-languages) except:

Bashkir, Basque, Esperanto, Galician, Interlingua, Irish, Maltese, Marathi, Mongolian, Urdu, Uyghur, Welsh.

For Mandarin, use the Simplified output locale (`cmn-Hans`, the default). Traditional characters (`cmn-Hant`) are not supported yet.

## Entity classes

- Some classes have subclasses: `location_city` is a subclass of `location`; `name_given` is a subclass of `name`. Entity Detection returns the most specific class. Redacting a general class also redacts its subclasses.
- Class names are English but international equivalents are detected. For example `ssn` covers equivalent government identification numbers in other countries.

### Entity class groups

| Group | Covers |
|---|---|
| `gdpr` | Personal data under the EU General Data Protection Regulation (GDPR). |
| `gdpr_sensitive` | Special categories of personal data under GDPR. |
| `hipaa_safe_harbor` | Identifiers under the HIPAA Safe Harbor de-identification method. |
| `cpra` | Personal information under the California Privacy Rights Act (CPRA). |
| `quebec_privacy_act` | Personal information under the Quebec Privacy Act (Law 25). |
| `appi` | Personal information under Japan's Act on the Protection of Personal Information (APPI). |
| `appi_sensitive` | Special care-required personal information under APPI. |
| `health` | All classes in the PHI table below. |
| `pci` | All classes in the PCI table below. |
| `pii` | All classes in the PII table below. Broad: includes dates, times, amounts of money and organization names. |

`pci` covers only payment-specific classes. Cardholder names and account numbers fall under `name` and `account_number`; add those alongside `pci`.

### Personally identifiable information (PII)

| Entity class | Description | Example | Groups |
|---|---|---|---|
| `account_number` | Customer account or membership identification number | Member ID: HZ-5235-001 | `pii`, `hipaa_safe_harbor` |
| `age` | Numbers associated with an individual's age | 27 years old | `pii`, `gdpr`, `hipaa_safe_harbor`, `quebec_privacy_act`, `appi` |
| `date` | Specific calendar dates, including days of the week, months, or years | Friday, Dec. 18, 2002 | `pii`, `hipaa_safe_harbor`, `quebec_privacy_act` |
| `date_interval` | Broader time periods, including date ranges, months, seasons, years, and decades | 5–9 May | `pii`, `hipaa_safe_harbor` |
| `dob` | Dates of birth | Born March 7, 1961 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `driver_license` | Driver's permit numbers | DL# 134711-320 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `duration` | Periods of time, specified as a number and a unit of time | 8 months | `pii` |
| `email_address` | Email addresses | support@speechmatics.com | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `event` | Names of events or holidays | Olympics | `pii` |
| `filename` | Names of computer files, including the extension or file path | brad-tax-returns.pdf | `pii` |
| `gender` | Terms indicating gender identity | female | `pii`, `gdpr`, `gdpr_sensitive`, `cpra`, `appi_sensitive` |
| `healthcare_number` | Healthcare numbers and health plan beneficiary numbers | Policy No. 5584-486-674-YM | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `ip_address` | IPv4 and IPv6 addresses | 192.168.0.1 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `language` | Names of natural languages | Korean | `pii`, `gdpr`, `gdpr_sensitive`, `appi_sensitive` |
| `location` | Any named location; covers the `location_*` classes | Lake Victoria | `pii`, `gdpr`, `hipaa_safe_harbor`, `appi` |
| `location_address` | Full or partial mailing addresses | 25/300 Adelaide T., Perth WA 6000 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `location_address_street` | Building number and street name, including unit or floor numbers | 25/300 Adelaide T. | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `location_city` | Municipality names, including villages, towns, and cities | Toronto | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `location_coordinate` | Latitude, longitude, or elevation coordinates | 40.748440, -73.984559 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `location_country` | Country names | Namibia | `pii`, `gdpr`, `appi` |
| `location_state` | State, province, territory, or prefecture names | Ontario | `pii`, `gdpr`, `appi` |
| `location_zip` | Zip codes and postcodes | B2N 3E3 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `marital_status` | Terms indicating marital status | married | `pii`, `appi_sensitive` |
| `money` | Names or amounts of currency | $94.50 | `pii` |
| `name` | Names of individuals, without personal titles; covers `name_given` and `name_family` | Dwayne Johnson | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `name_family` | Family names, often a last name in Western cultures | Johnson | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `name_given` | Given names, often a first or middle name in Western cultures | Dwayne | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `name_medical_professional` | Full names of medical professionals, including titles | Dr. Kay Martinez, MD | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `numerical_pii` | Numerical or alphanumeric PII not covered by other classes, such as order or tracking numbers | — | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `occupation` | Job titles or professions | engineer | `pii`, `quebec_privacy_act`, `appi` |
| `organization` | Names of organizations or departments | LAPD | `pii`, `quebec_privacy_act`, `appi` |
| `organization_id` | Organization identification numbers | — | `pii`, `quebec_privacy_act`, `appi` |
| `organization_medical_facility` | Names of medical facilities, such as hospitals and clinics | Northwest General Hospital | `pii`, `quebec_privacy_act`, `appi` |
| `origin` | Terms indicating nationality, ethnicity, or provenance | Canadian | `pii`, `gdpr`, `gdpr_sensitive`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `passport_number` | Passport numbers | PA4568332 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `password` | Passwords, PINs, access keys, or verification answers | My mother's maiden name is Smith | `pii`, `cpra`, `appi` |
| `phone_number` | Telephone or fax numbers | 0115 957 1512 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `physical_attribute` | Distinctive bodily attributes, including terms indicating race | I'm 190cm tall | `pii`, `gdpr`, `gdpr_sensitive`, `cpra`, `appi_sensitive` |
| `political_affiliation` | Political parties, movements, or ideologies | Republican | `pii`, `gdpr`, `gdpr_sensitive`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `religion` | Terms indicating religious affiliation | Presbyterian | `pii`, `gdpr`, `gdpr_sensitive`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `sexuality` | Terms indicating sexual orientation | bisexual | `pii`, `gdpr`, `gdpr_sensitive`, `cpra`, `appi_sensitive` |
| `ssn` | Social Security Numbers or equivalent government identification numbers | 078-05-1120 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `ssn_in_aadhaar` | Aadhaar numbers | — | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `time` | Clock times | 10pm EST | `pii` |
| `url` | Internet addresses | www.speechmatics.com | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act` |
| `username` | Usernames, login names, or handles | @Speechmatics | `pii`, `gdpr`, `cpra`, `appi` |
| `vehicle_id` | Vehicle identification numbers and license plates | BIF7547 | `pii`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `appi` |
| `zodiac_sign` | Names of zodiac signs | Aries | `pii` |

### Protected health information (PHI)

| Entity class | Description | Example | Groups |
|---|---|---|---|
| `blood_type` | Blood types | type AB positive | `health`, `gdpr`, `cpra`, `quebec_privacy_act` |
| `condition` | Medical conditions, diseases, syndromes, and disorders | arrhythmia | `health`, `gdpr`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `dose` | Prescribed quantity of a medication | 700 mg/day | `health` |
| `drug` | Medications, vitamins, and supplements | acetaminophen | `health`, `gdpr`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `injury` | Bodily injuries, including dislocations | sprained wrist | `health`, `gdpr`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `medical_process` | Treatments, procedures, and tests | CT scan | `health`, `gdpr`, `cpra`, `quebec_privacy_act`, `appi_sensitive` |
| `statistics` | Medical statistics | 18% of patients | `health`, `quebec_privacy_act` |

### Payment card information (PCI)

| Entity class | Description | Example | Groups |
|---|---|---|---|
| `bank_account` | Bank account numbers, including IBAN | Acct. No. 012345-67 | `pci`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `credit_card` | Credit card numbers | 0123 0123 0123 0123 | `pci`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `credit_card_expiration` | Credit card expiration dates | Exp: 02/28 | `pci`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `cvv` | 3- or 4-digit card verification codes | CVV: 080 | `pci`, `gdpr`, `hipaa_safe_harbor`, `cpra`, `quebec_privacy_act`, `appi` |
| `routing_number` | Bank routing numbers | 012345678 | `pci` |
