# Summarization

Docs: https://docs.speechmatics.com/speech-to-text/batch/speech-intelligence/summarization

Generate a summary of the audio in the same Batch API call that transcribes it.

## Enable

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "summarization_config": {}
}
```

## `summarization_config`

| Field | Values | Default | Description |
|---|---|---|---|
| `content_type` | `auto`, `informative`, `conversational` | Not stated in the spec | `conversational`: best for dialogues with multiple participants, such as calls, meetings, or discussions. Summarizes the key points of the conversation. `informative`: for more structured information delivered by one or more people, such as videos, podcasts, lectures, and presentations. `auto`: selects the most appropriate content type from an analysis of the transcript |
| `summary_length` | `brief`, `detailed` | `brief` | `brief`: a succinct summary of a few sentences. `detailed`: a longer, structured summary. For conversational content it includes key topics and a summary of the entire conversation. For informative content it divides the audio into sections and summarizes each |
| `summary_type` | `paragraphs`, `bullets` | Not stated in the spec | Output layout |

Fully specified:

```json
{
  "type": "transcription",
  "transcription_config": {
    "model": "enhanced",
    "language": "en"
  },
  "summarization_config": {
    "content_type": "informative",
    "summary_length": "detailed",
    "summary_type": "bullets"
  }
}
```

## Python example

Uses the older `speechmatics.batch_client` client, as in the docs:

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
    "transcription_config": {"language": LANGUAGE, "model": "enhanced"},
    "summarization_config": {},  # You can also configure the summary. See below for more detail.
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
        summary = transcript["summary"]["content"]
        print(summary)  # print the returned summary
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid API key - Check your API_KEY at the top of the code!")
        elif e.response.status_code == 400:
            print(e.response.json()["detail"])
        else:
            raise e
```

## Response

The summary is only present in the JSON output, as a top-level `summary` object with one string field, `content`.

```json
{
  "job": { ... },
  "metadata": {
    "created_at": "2023-05-26T15:01:48.412714Z",
    "type": "transcription",
    "transcription_config": {
      "language": "en"
    },
    "summarization_config": {}
  },
  "results": [...],
  "summary": {
    "content": "Laura Perez called to seek assistance in completing her booking through the mobile application..."
  }
}
```

`content` is plain text. Bullets and section headings arrive as text lines (`- ...`, `1. ...`), as the samples below show.

## Errors

The docs page has no error section. The API spec defines `metadata.summarization_errors`, an array of:

| Field | Values |
|---|---|
| `type` | `summarization_failed`, `unsupported_language` |
| `message` | Human-readable error message |

The other speech intelligence features complete the transcription and report feature errors in metadata. Check `metadata.summarization_errors` before reading `summary`.

## Sample outputs

Each sample shows `summary.content` for one combination of `content_type`, `summary_length`, and `summary_type`.

### Webinar (`informative`)

A summary of a Speechmatics release webinar.

`summary_length: brief`, `summary_type: bullets`:

```text
- Speechmatics introduced new speech recognition models named Ursa that are optimized for GPUs and are the most accurate ASR on the planet with a 35% improvement for standard and a 22% improvement for enhanced. The new models are also three times more efficient than CPU-based models.
  
- The company has released a new version of its speech recognition software that includes improvements to speaker diarization, batch processing, and readability. The new version also includes automatic language identification and translation capabilities for 34 languages to and from English, with the translation feature outperforming Google's translation service.
  
- The speaker demonstrates how to use Speechmatics' transcription and translation services through their portal or API, including real-time transcription that can be customized with speaker labels and custom words. The speaker also answers questions about the accuracy of the system, maximum file size for transcription, and support for multiple languages in real-time streams.
```

`summary_length: brief`, `summary_type: paragraphs`:

```text
Speechmatics has introduced new speech recognition software models named Ursa, optimized for GPUs, which are more powerful and efficient for processing. The new models have been benchmarked against competitors and found to be the most accurate ASR on the planet, with a 35% improvement for standard and 22% for enhanced. The company has also released a new version of its software that includes improvements to speaker diarization, batch processing, and readability, as well as automatic language identification and translation capabilities for 34 languages to and from English. The company claims to outcompete other alternatives in terms of accuracy, efficiency, and processing speed.
```

`summary_length: detailed`, `summary_type: bullets`:

```text
1. Speechmatics' ASR Revolution
  - Speechmatics introduced new models named Ursa that focus on accuracy, speed, and efficiency.
  - The new models are optimized for GPUs, which are more powerful and efficient for processing.
  - Ursa has been benchmarked against competitors and found to be the most accurate ASR on the planet, with a 35% improvement for standard and a 22% improvement for enhanced.
  - The models perform better with accents and noise and are three times more efficient than CPU-based models.
  - The latency for real-time transcription has also been improved, with the new models showing little difference in accuracy even at small latencies.
  - Beta customers have used the new models for live captioning at a major car racing event.

2. Improvements to Speech Recognition Software
  - Speechmatics released a new version of its speech recognition software that includes improvements to speaker diarization, batch processing, and readability.
  - The software also includes automatic language identification and translation capabilities, with a single API call allowing translation to and from 34 languages.
  - The company claims its transcription accuracy is the best available, and that its translation accuracy is ahead of Google's.
  - The new version is available to enterprise customers and will be rolled out to other languages later this year.

3. Using Speechmatics' Services
  - The speaker demonstrates how to use Speechmatics' transcription and translation services through their portal or API.
  - The user can select the language they want to translate their audio file to and choose between enhanced or standard translation speed.
  - The portal also allows users to view previous jobs and real-time transcription with the option to add custom words and reduce latency.
  - The speaker also addresses questions about the maximum file size for transcription, the accuracy of the system, and the support for speaker labels and multiple languages in real-time streams.
  - The speaker concludes by encouraging users to try out Speechmatics' services and visit their website for more information.
```

`summary_length: detailed`, `summary_type: paragraphs`:

```text
1. Introduction
Speechmatics, a speech recognition software company, held a live product update event titled "ASR Revolution" to introduce their new models that focus on accuracy, speed, and efficiency. The company has previously optimized their models for CPUs and recently launched a beta version for laptops. However, they have now shifted their focus to GPUs, which are more powerful and efficient for processing.

2. New Models
The new models, named Ursa, have been benchmarked against competitors and have been found to be the most accurate ASR on the planet, with a 35% improvement for standard and 22% for enhanced. The models also perform better with accents and noise. The company has also improved efficiency, with the new models being three times more efficient than CPU processing for standard and 1.7 times for enhanced. The new models also maintain accuracy even at small latencies, making them suitable for real-time transcription. The company has already had beta customers use the new models for live captioning at a major car racing event.

3. New Version
Speechmatics has released a new version of its speech recognition software that includes improvements to speaker diarization, batch processing, and readability. The new version also includes automatic language identification and translation capabilities for 34 languages to and from English. The translation feature is available in batch processing and will be available in real-time processing in Q2 2023. The company claims that its transcription accuracy is the best in the industry and that its translation feature outperforms Google's translation service. The new version is available to enterprise customers and will be rolled out to other languages later this year.

4. How to Use
The speaker demonstrates how to use Speechmatics' transcription and translation services through their portal or API. The user can select the language they want to translate their audio file to and choose between enhanced or standard speed. The portal also allows users to view previous jobs and real-time transcription with the option to add custom words and reduce latency. The speaker also addresses questions about the accuracy of the system, the maximum size of audio files, and the support for multiple languages in real-time streams.

5. Conclusion
The company claims to outcompete other alternatives in terms of accuracy, efficiency, and processing speed.
```

### Interview (`informative`)

A summary of the interview "Adding Value for Contact Center Solutions Using Speech to Text".

`summary_length: brief`, `summary_type: bullets`:

```text
- Prosodica uses Speechmatics' transcription engine to provide insights and predictions based on customer conversations in contact center analytics.
- The accuracy of transcription is crucial for machine learning algorithms to make accurate predictions, and having a diverse and inclusive voice model is important to avoid disparate impacts.
- The future of speech recognition in the contact center space is evolving towards a hybrid workforce, where businesses need to be remote-ready to support both customers and employees
```

`summary_length: brief`, `summary_type: paragraphs`:

```text
The use of speech-to-text technology in contact center analytics is discussed in a conversation between Ricardo Herreros-Symons and Mariano Tan. They highlight the importance of transcription accuracy for machine learning algorithms to make accurate predictions and the need for a diverse and inclusive voice model. The future of speech recognition in the contact center space is expected to involve a hybrid workforce, with both automation and improving people's lives being in demand. The use of prosodic data points can help detect sarcasm, which is a tricky problem for machine learning algorithms.
```

`summary_length: detailed`, `summary_type: bullets`:

```text
1. Importance of accurate transcription in contact center analytics
  - Speech-to-text technology used to provide insights and predictions based on customer conversations
  - Accuracy of transcription crucial for machine learning algorithms to make accurate predictions
  - Small improvements in transcription accuracy can have a significant impact on machine learning accuracy

2. Importance of diverse and inclusive voice model
  - Multinational corporations send voice traffic to call centers all over the world
  - More diverse set of voices used in training, wider the net for what's typical and same level of recognition accuracy can be achieved
  - Non-native English speaking voices, female voices, and younger voices are all areas where many transcription engines struggle

3. Disparate impact of transcription accuracy differences
  - If transcription is less accurate for a particular voice, then the prediction is less accurate for that voice, creating a disparate impact that businesses do not want

4. Future of speech recognition in contact center space
  - Evolving towards a hybrid workforce, where businesses need to be remote-ready to support both customers and employees
  - Automation is a trend, but there are certain interactions that people will not be comfortable dealing with an automated bot
  - Sarcasm is a tricky problem, but speech and voice analytics used as data point to detect it.
```

`summary_length: detailed`, `summary_type: paragraphs`:

```text
1. Introduction
In this transcript, Ricardo Herreros-Symons, VP of Sales Business Development at Speechmatics, and Mariano Tan, CEO and founder of Prosodica, discuss the use of speech-to-text technology in contact center analytics. Prosodica uses Speechmatics' transcription engine to provide insights and predictions based on customer conversations.

2. Importance of Transcription Accuracy
The accuracy of the transcription is crucial for machine learning algorithms to make accurate predictions, and even small improvements in transcription accuracy can have a significant impact on machine learning accuracy. The importance of having a diverse and inclusive voice model has also risen in recent years, as multinational corporations send voice traffic to call centers all over the world.

3. Disparate Impacts of Transcription Accuracy Differences
As speech recognition becomes more mainstream, businesses are becoming increasingly concerned about the potential disparate impacts of transcription accuracy differences when analyzing less typical voices. The more diverse the set of voices used in training, the more likely we are to have a wider net for what's typical and get the same level of recognition accuracy across that.

4. Future of Speech and Speech Recognition in Contact Center Space
In terms of the future of speech and speech recognition within the context center space, there is more prevalent use of speech analytics technology in the contact center space. The two approaches are to use speech recognition to fully automate interactions or to measure and improve the experience, the employee experience. The technology was easier to implement in a cloud-based format, and so we did see a lot of adoption for cloud providers. However, there are certain interactions that people will not get comfortable with dealing with an automated bot.

5. Detection of Sarcasm
Sarcasm is a tricky problem, but the reason why Prosodica uses as its data point, both speech and voice analytics, is to detect that.
```

### Technical support call (`conversational`)

A summary of a technical customer support call.

`summary_length: brief`, `summary_type: bullets`:

```text
- Laura Perez is having trouble completing bookings through the mobile app and has checked her internet connection and payment details.
- The issue is resolved by updating the Stay app on her iOS device.
- Laura agrees to receive articles on her email about the latest places and promos offered by Stay.
```

`summary_length: brief`, `summary_type: paragraphs`:

```text
Laura Perez contacts Miranda for help with completing her bookings through the mobile application. Despite refreshing the page and checking her internet connection and payment method, she is unable to complete the booking. Miranda suggests updating the Stay app on her phone, which Laura does, and is then able to successfully book a place. Miranda also offers to send Laura articles on the latest places and promos that Stay offers. Laura expresses gratitude and ends the call.
```

`summary_length: detailed`, `summary_type: bullets`:

```text
Key Topics:
- Technical issue with mobile app
- Updating software
- Sending promotional articles via email

Discussion:
- Laura Perez is unable to complete bookings through the mobile app despite refreshing the page and checking her internet connection and payment method
- The app keeps going back to the main page
- Miranda suggests updating the app as it was recently updated to remove bugs
- Laura has not updated the app yet and is using iOS 12.1
- Miranda instructs Laura to update the app through the app store
- Laura updates the app and is able to book a place
- Miranda offers to send promotional articles via email to Laura
```

`summary_length: detailed`, `summary_type: paragraphs`:

```text
Key Topics:
- Technical issue with mobile application
- Updating software
- Sending promotional articles via email

Discussion:
Laura Perez called the customer service of Stay to report that she was unable to complete her bookings through the mobile application. She had already refreshed the application several times, checked her internet connection, and payment method, but still encountered the same issue. She also mentioned that the application goes back to the main page every time she tries to browse. The customer service representative, Miranda, asked if the application showed any error message, but Laura said it did not. Miranda then asked if Laura had updated the software to its latest version, to which Laura replied that she was not aware of any update. Miranda advised Laura to update the Stay app on her phone by going to the app store and clicking the update button beside the Stay icon. After updating the app, Laura was able to book a place successfully.

Miranda also asked Laura if it was okay to send her articles on her email to keep her updated on the latest places and promos that Stay offers. Laura agreed and thanked Miranda for her help.
```

## More examples

Speechmatics Academy: https://github.com/speechmatics/speechmatics-academy/tree/main/basics/04-audio-intelligence
