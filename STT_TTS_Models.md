Here’s a **clear, practical overview of STT (Speech-to-Text) and TTS (Text-to-Speech) models**, grouped by category and common real-world usage.

---

## 🔊 Speech-to-Text (STT) Models

(Convert audio → text)

### 🔹 Open-source

* **Whisper (OpenAI)**

  * Multilingual, very accurate
  * Works well for noisy audio
  * Popular sizes: `tiny → large`
  * Used heavily in Python pipelines & FastAPI
* **Vosk**

  * Offline, lightweight
  * Good for embedded systems
* **DeepSpeech (Mozilla – legacy)**

  * Mostly deprecated but still seen

### 🔹 Cloud / Managed APIs

* **OpenAI Whisper API**
* **Google Speech-to-Text**
* **AWS Transcribe**
* **Azure Speech to Text**
* **AssemblyAI**
* **Deepgram** (very fast, streaming-friendly)

### 🔹 Typical Use Cases

* Call center transcription
* Meeting notes
* Voice assistants
* Podcast / video subtitles
* Real-time streaming STT (WebSocket)

---

## 🗣️ Text-to-Speech (TTS) Models

(Convert text → audio)

### 🔹 Open-source

* **Coqui TTS**

  * High-quality neural voices
  * Voice cloning supported
* **ESPnet TTS**

  * Research-grade, very flexible
* **Festival / eSpeak**

  * Lightweight, robotic voices

### 🔹 Cloud / Managed APIs

* **OpenAI TTS (e.g., `gpt-4o-mini-tts`)**
* **Google Text-to-Speech**
* **AWS Polly**
* **Azure Neural TTS**
* **ElevenLabs** (very natural voices, cloning)
* **Play.ht**

### 🔹 Typical Use Cases

* Voice assistants
* Audiobooks
* Accessibility (screen readers)
* IVR systems
* AI avatars & chatbots

---

## ⚡ Real-Time / Streaming Combos (STT + TTS)

Used in **voice bots & conversational AI**:

* **OpenAI Realtime API** (STT + TTS + reasoning)
* **Deepgram STT + TTS**
* **Azure Speech SDK**
* **Google Dialogflow + TTS**

---

## 🧠 Model Selection Cheat Sheet

| Need                | Best Choice             |
| ------------------- | ----------------------- |
| Offline STT         | Whisper / Vosk          |
| High accuracy STT   | Whisper / Deepgram      |
| Real-time streaming | Deepgram / Azure        |
| Natural human voice | ElevenLabs / OpenAI TTS |
| Cheap & scalable    | AWS Polly               |
| Voice cloning       | Coqui / ElevenLabs      |

