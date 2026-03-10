# STT_And_TTS_Models_-experiment

Here’s a **clear list of Speech-to-Text (STT)** and **Text-to-Speech (TTS)** models, divided into **Open-Source** and **Paid/API** ones (commonly used in voice-AI pipelines like the one you showed).

---

# 1️⃣ Speech-to-Text (STT)

## 🟢 Open-Source STT Models

You can run these locally or self-host.

| Model                          | Company / Org     | Notes                                                                                           |
| ------------------------------ | ----------------- | ----------------------------------------------------------------------------------------------- |
| **Whisper / Whisper Large v3** | OpenAI            | Very popular multilingual transcription model trained on ~680k hours of audio. ([Wikipedia][1]) |
| **Distil-Whisper**             | HuggingFace       | Faster, smaller Whisper variant                                                                 |
| **Wav2Vec 2.0**                | Meta              | Self-supervised speech representation model widely used in research. ([asrbench.github.io][2])  |
| **Kaldi**                      | Kaldi ASR Toolkit | Classic research toolkit for building ASR systems. ([Wikipedia][3])                             |
| **Vosk**                       | Alpha Cephei      | Lightweight offline STT for mobile/edge                                                         |
| **Parakeet TDT**               | NVIDIA            | Very fast open STT model with high throughput. ([Modal][4])                                     |
| **Canary Qwen 2.5B**           | NVIDIA            | One of the top open ASR models with ~5.6% WER. ([Modal][4])                                     |
| **Granite Speech 3.3**         | IBM               | Large ASR model with strong accuracy. ([Modal][4])                                              |
| **Moonshine**                  | Various           | Lightweight edge STT                                                                            |
| **SenseVoice**                 | Alibaba           | Multilingual speech model (newer OSS projects)                                                  |

---

## 💰 Paid / API STT Models

| Model                        | Provider     | Notes                            |
| ---------------------------- | ------------ | -------------------------------- |
| **Nova-3**                   | Deepgram     | Very fast streaming STT          |
| **Universal-Streaming**      | AssemblyAI   | Real-time transcription          |
| **Azure Speech-to-Text**     | Microsoft    | Enterprise speech service        |
| **Google Speech-to-Text**    | Google Cloud | High-accuracy multilingual       |
| **Speechmatics**             | Speechmatics | Enterprise STT                   |
| **Gladia**                   | Gladia AI    | Real-time voice API              |
| **OpenAI GPT-4o Transcribe** | OpenAI       | Modern streaming transcription   |
| **Groq Whisper API**         | Groq         | Extremely fast Whisper inference |

---

# 2️⃣ Text-to-Speech (TTS)

## 🟢 Open-Source TTS Models

| Model                    | Org              | Notes                                                               |
| ------------------------ | ---------------- | ------------------------------------------------------------------- |
| **Coqui TTS / XTTS**     | Coqui AI         | Popular open TTS with voice cloning                                 |
| **Piper TTS**            | Rhasspy          | Lightweight local TTS                                               |
| **Bark**                 | Suno             | Neural voice + sound generation                                     |
| **StyleTTS / StyleTTS2** | Research project | Emotional speech synthesis                                          |
| **Tortoise TTS**         | Open source      | High-quality but slower                                             |
| **ESPnet-TTS**           | ESPnet           | Research toolkit supporting Tacotron2, FastSpeech etc. ([arXiv][5]) |
| **ChatTTS**              | Open community   | Expressive conversational TTS                                       |
| **Fish-Speech**          | Fish Audio       | Multilingual voice generation                                       |
| **eSpeak / eSpeak-NG**   | Open source      | Lightweight formant-based speech synthesizer. ([Wikipedia][6])      |

---

## 💰 Paid / API TTS Models

| Model                          | Provider   | Notes                        |
| ------------------------------ | ---------- | ---------------------------- |
| **ElevenLabs**                 | ElevenLabs | Very realistic voice cloning |
| **Cartesia Sonic**             | Cartesia   | Low-latency real-time voices |
| **OpenAI gpt-4o-mini-tts**     | OpenAI     | expressive voices            |
| **Amazon Polly**               | AWS        | enterprise TTS               |
| **Google Cloud TTS / WaveNet** | Google     | natural sounding             |
| **Azure Neural TTS**           | Microsoft  | many languages               |
| **PlayHT**                     | PlayHT     | voice cloning + streaming    |
| **Resemble AI**                | Resemble   | emotional voices             |

---

# 3️⃣ Typical Voice-Agent Pipeline (what you showed)

```
User Speech
   ↓
STT (Whisper / Deepgram / AssemblyAI)
   ↓
LLM (GPT / Claude / Gemini / Llama)
   ↓
TTS (ElevenLabs / Cartesia / Piper)
   ↓
User hears response
```

---

✅ **Common stacks developers use**

**Open-source stack**

```
Whisper / Vosk
↓
Llama / Mistral
↓
Piper / Coqui TTS
```

**Production stack**

```
Deepgram / AssemblyAI
↓
GPT-4o / Claude
↓
ElevenLabs / Cartesia
```

---

💡 If you want, I can also give:

* **Best STT + TTS for real-time voice agents (lowest latency)**
* **Best open-source voice stack (fully local)**
* **Best models for building a ChatGPT-like voice assistant**

Just tell me.

[1]: https://en.wikipedia.org/wiki/Whisper_%28speech_recognition_system%29?utm_source=chatgpt.com "Whisper (speech recognition system)"
[2]: https://asrbench.github.io/asrbench/cli/transcribers/?utm_source=chatgpt.com "Transcribers - ASRBench"
[3]: https://en.wikipedia.org/wiki/Kaldi_%28software%29?utm_source=chatgpt.com "Kaldi (software)"
[4]: https://modal.com/blog/open-source-stt?utm_source=chatgpt.com "The Top Open Source Speech-to-Text (STT) Models in 2025"
[5]: https://arxiv.org/abs/1910.10909?utm_source=chatgpt.com "ESPnet-TTS: Unified, Reproducible, and Integratable Open Source End-to-End Text-to-Speech Toolkit"
[6]: https://en.wikipedia.org/wiki/ESpeak?utm_source=chatgpt.com "ESpeak"



Yes — **that summary is mostly correct**, with a bit of nuance. Here’s a **clear evaluation**:

---

## 📌 Core Specializations (Simple)

| Provider       | Best At                               | STT         | TTS             | Notes                                             |
| -------------- | ------------------------------------- | ----------- | --------------- | ------------------------------------------------- |
| **ElevenLabs** | **TTS (best‑in‑class voice quality)** | Good        | ⭐ Excellent     | Known for realistic voices & voice cloning        |
| **Deepgram**   | **STT (real‑time & scalable)**        | ⭐ Excellent | Good            | Strong for live streaming & production voice apps |
| **AssemblyAI** | **STT + audio intelligence**          | ⭐ Excellent | ❌ No native TTS | Best for transcription + insights                 |

---

## 🎙️ **ElevenLabs – Best for TTS**

✔️ Extremely natural/smooth voices
✔️ Multiple languages & emotional control
✔️ Voice cloning
✔️ Easy to integrate in voice apps & content generation

➡️ If your main goal is **top‑tier TTS → lifelike speech**, ElevenLabs is one of the best in 2026.

---

## 🗣️ **Deepgram – Best for STT**

✔️ Highly optimized for **real‑time streaming**
✔️ Low latency (great for voice assistants)
✔️ Flexible deployment & scaling
✔️ Supports both **STT & TTS**

➡️ **Best for production voice applications**, especially where **speed and streaming** are required.

---

## 🔍 **AssemblyAI – Best for Transcription + Insights**

✔️ High transcription accuracy
✔️ Built‑in **audio intelligence features**:

* Summarization
* Topic detection
* Sentiment
* Content moderation
* Entity extraction
  ✔️ Great for analytics workflows

❌ **No native TTS**, so usually paired with a TTS provider.

➡️ Ideal for **call centers, large batch audio processing, meeting insights, podcast ingestion, compliance**.

---

## 🧠 Quick Guide for Decision

### If you want **voice output quality** (TTS)…

➡️ **ElevenLabs** wins
(Great for storytelling, media, voice apps needing natural voices)

### If you want **fast, real‑time transcription** (STT)…

➡️ **Deepgram** wins
(Great for interactive voice assistants & streaming)

### If you want **rich insights from audio**…

➡️ **AssemblyAI** wins
(Great for analytics, summarization, topic/speaker insights)

---

## 📊 Short Verdict (1‑line)

* **ElevenLabs:** Best TTS quality
* **Deepgram:** Best STT + strong overall speech platform
* **AssemblyAI:** Best STT with deep audio intelligence

---



## 🧩 Available services

| Category            | Services                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Speech-to-Text      | [AssemblyAI](https://docs.pipecat.ai/server/services/stt/assemblyai), [AWS](https://docs.pipecat.ai/server/services/stt/aws), [Azure](https://docs.pipecat.ai/server/services/stt/azure), [Cartesia](https://docs.pipecat.ai/server/services/stt/cartesia), [Deepgram](https://docs.pipecat.ai/server/services/stt/deepgram), [ElevenLabs](https://docs.pipecat.ai/server/services/stt/elevenlabs), [Fal Wizper](https://docs.pipecat.ai/server/services/stt/fal), [Gladia](https://docs.pipecat.ai/server/services/stt/gladia), [Google](https://docs.pipecat.ai/server/services/stt/google), [Gradium](https://docs.pipecat.ai/server/services/stt/gradium), [Groq (Whisper)](https://docs.pipecat.ai/server/services/stt/groq), [NVIDIA Riva](https://docs.pipecat.ai/server/services/stt/riva), [OpenAI (Whisper)](https://docs.pipecat.ai/server/services/stt/openai), [SambaNova (Whisper)](https://docs.pipecat.ai/server/services/stt/sambanova), [Sarvam](https://docs.pipecat.ai/server/services/stt/sarvam), [Soniox](https://docs.pipecat.ai/server/services/stt/soniox), [Speechmatics](https://docs.pipecat.ai/server/services/stt/speechmatics), [Whisper](https://docs.pipecat.ai/server/services/stt/whisper)                                                                                                                                                                                                                                                                                                                             |
| LLMs                | [Anthropic](https://docs.pipecat.ai/server/services/llm/anthropic), [AWS](https://docs.pipecat.ai/server/services/llm/aws), [Azure](https://docs.pipecat.ai/server/services/llm/azure), [Cerebras](https://docs.pipecat.ai/server/services/llm/cerebras), [DeepSeek](https://docs.pipecat.ai/server/services/llm/deepseek), [Fireworks AI](https://docs.pipecat.ai/server/services/llm/fireworks), [Gemini](https://docs.pipecat.ai/server/services/llm/gemini), [Grok](https://docs.pipecat.ai/server/services/llm/grok), [Groq](https://docs.pipecat.ai/server/services/llm/groq), [Mistral](https://docs.pipecat.ai/server/services/llm/mistral), [NVIDIA NIM](https://docs.pipecat.ai/server/services/llm/nim), [Ollama](https://docs.pipecat.ai/server/services/llm/ollama), [OpenAI](https://docs.pipecat.ai/server/services/llm/openai), [OpenRouter](https://docs.pipecat.ai/server/services/llm/openrouter), [Perplexity](https://docs.pipecat.ai/server/services/llm/perplexity), [Qwen](https://docs.pipecat.ai/server/services/llm/qwen), [SambaNova](https://docs.pipecat.ai/server/services/llm/sambanova) [Together AI](https://docs.pipecat.ai/server/services/llm/together)                                                                                                                                                                                                                                                                                                                                                               |
| Text-to-Speech      | [Async](https://docs.pipecat.ai/server/services/tts/asyncai), [AWS](https://docs.pipecat.ai/server/services/tts/aws), [Azure](https://docs.pipecat.ai/server/services/tts/azure), [Camb AI](https://docs.pipecat.ai/server/services/tts/camb), [Cartesia](https://docs.pipecat.ai/server/services/tts/cartesia), [Deepgram](https://docs.pipecat.ai/server/services/tts/deepgram), [ElevenLabs](https://docs.pipecat.ai/server/services/tts/elevenlabs), [Fish](https://docs.pipecat.ai/server/services/tts/fish), [Google](https://docs.pipecat.ai/server/services/tts/google), [Gradium](https://docs.pipecat.ai/server/services/tts/gradium), [Groq](https://docs.pipecat.ai/server/services/tts/groq), [Hume](https://docs.pipecat.ai/server/services/tts/hume), [Inworld](https://docs.pipecat.ai/server/services/tts/inworld), [LMNT](https://docs.pipecat.ai/server/services/tts/lmnt), [MiniMax](https://docs.pipecat.ai/server/services/tts/minimax), [Neuphonic](https://docs.pipecat.ai/server/services/tts/neuphonic), [NVIDIA Riva](https://docs.pipecat.ai/server/services/tts/riva), [OpenAI](https://docs.pipecat.ai/server/services/tts/openai), [Piper](https://docs.pipecat.ai/server/services/tts/piper), [Resemble](https://docs.pipecat.ai/server/services/tts/resemble), [Rime](https://docs.pipecat.ai/server/services/tts/rime), [Sarvam](https://docs.pipecat.ai/server/services/tts/sarvam), [Speechmatics](https://docs.pipecat.ai/server/services/tts/speechmatics), [XTTS](https://docs.pipecat.ai/server/services/tts/xtts) |
| Speech-to-Speech    | [AWS Nova Sonic](https://docs.pipecat.ai/server/services/s2s/aws), [Gemini Multimodal Live](https://docs.pipecat.ai/server/services/s2s/gemini), [Grok Voice Agent](https://docs.pipecat.ai/server/services/s2s/grok), [OpenAI Realtime](https://docs.pipecat.ai/server/services/s2s/openai), [Ultravox](https://docs.pipecat.ai/server/services/s2s/ultravox),                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Transport           | [Daily (WebRTC)](https://docs.pipecat.ai/server/services/transport/daily), [FastAPI Websocket](https://docs.pipecat.ai/server/services/transport/fastapi-websocket), [SmallWebRTCTransport](https://docs.pipecat.ai/server/services/transport/small-webrtc), [WebSocket Server](https://docs.pipecat.ai/server/services/transport/websocket-server), Local                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Serializers         | [Exotel](https://docs.pipecat.ai/server/utilities/serializers/exotel), [Plivo](https://docs.pipecat.ai/server/utilities/serializers/plivo), [Twilio](https://docs.pipecat.ai/server/utilities/serializers/twilio), [Telnyx](https://docs.pipecat.ai/server/utilities/serializers/telnyx), [Vonage](https://docs.pipecat.ai/server/utilities/serializers/vonage)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Video               | [HeyGen](https://docs.pipecat.ai/server/services/video/heygen), [LemonSlice](https://docs.pipecat.ai/server/services/video/lemonslice), [Tavus](https://docs.pipecat.ai/server/services/video/tavus), [Simli](https://docs.pipecat.ai/server/services/video/simli)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| Memory              | [mem0](https://docs.pipecat.ai/server/services/memory/mem0)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Vision & Image      | [fal](https://docs.pipecat.ai/server/services/image-generation/fal), [Google Imagen](https://docs.pipecat.ai/server/services/image-generation/google-imagen), [Moondream](https://docs.pipecat.ai/server/services/vision/moondream)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Audio Processing    | [Silero VAD](https://docs.pipecat.ai/server/utilities/audio/silero-vad-analyzer), [Krisp](https://docs.pipecat.ai/server/utilities/audio/krisp-filter), [Koala](https://docs.pipecat.ai/server/utilities/audio/koala-filter), [ai-coustics](https://docs.pipecat.ai/server/utilities/audio/aic-filter)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Analytics & Metrics | [OpenTelemetry](https://docs.pipecat.ai/server/utilities/opentelemetry), [Sentry](https://docs.pipecat.ai/server/services/analytics/sentry)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |

📚 [View full services documentation →](https://docs.pipecat.ai/server/services/supported-services)
