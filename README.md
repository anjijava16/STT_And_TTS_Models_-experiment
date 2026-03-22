
# STT & TTS API — Deep Project Summary

## Overview

A production-ready **FastAPI** application providing a unified REST API for multiple Speech-to-Text (STT) and Text-to-Speech (TTS) providers, plus an AI pipeline layer powered by **Pipecat**. The API abstracts away provider-specific details behind a consistent interface, allowing callers to switch providers via a single query parameter.

- **Runtime:** Python 3.13+ with async/await throughout
- **Package Manager:** `uv` (lockfile: `uv.lock`)
- **Server:** Uvicorn on `0.0.0.0:8047`, hot-reload in debug mode
- **Docs:** Auto-generated at `/docs` (Swagger) and `/redoc`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│                         (main.py)                            │
│  CORS · OpenAPI · Uvicorn · Router Registration              │
├──────────┬──────────┬───────────────┬───────────────────────┤
│  Health  │   STT    │     TTS       │      Pipecat          │
│  Router  │  Router  │    Router     │      Router           │
├──────────┴──────────┴───────────────┴───────────────────────┤
│                      Service Layer                           │
│        STTService  ·  TTSService  ·  PipecatService          │
├─────────────────────────────────────────────────────────────┤
│                      Model Layer (ABC)                       │
│  ┌──────────┐ ┌────────────┐ ┌─────────┐                    │
│  │ Deepgram │ │ AssemblyAI │ │ Whisper │  ← STT providers   │
│  └──────────┘ └────────────┘ └─────────┘                    │
│  ┌────────────┐ ┌──────────┐                                 │
│  │ ElevenLabs │ │ Cartesia │              ← TTS providers   │
│  └────────────┘ └──────────┘                                 │
├─────────────────────────────────────────────────────────────┤
│  Schemas (Pydantic)  ·  Settings (pydantic-settings)         │
│  Custom Exceptions   ·  Enums & Validators                   │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Directory | Role |
|-------|-----------|------|
| **Routers** | `app/routers/` | HTTP endpoints, request validation, response formatting |
| **Services** | `app/services/` | Business logic, provider routing, pipeline orchestration |
| **Models** | `app/models/` | Provider-specific API integrations (httpx / pipecat) |
| **Schemas** | `app/schemas/` | Pydantic request/response contracts, enums |
| **Utils** | `app/utils/` | Centralized settings, custom HTTP exceptions |

---

## File Inventory (22 files)

### Entry Point
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app init, CORS, router registration, uvicorn runner |
| `pyproject.toml` | Dependencies & project metadata |

### Schemas (`app/schemas/`)
| File | Key Types |
|------|-----------|
| `stt.py` | `STTProvider` enum, `STTRequest`, `STTResponse` |
| `tts.py` | `TTSProvider` enum, `TTSRequest` (1–5000 chars), `TTSResponse` |
| `pipecat.py` | `PipecatSTTProvider`, `PipecatTTSProvider`, pipeline request/response models |

### Models — STT (`app/models/stt/`)
| File | Provider | Auth | Flow |
|------|----------|------|------|
| `base.py` | ABC | — | `transcribe(audio_data, language, model) → STTResponse` |
| `deepgram_model.py` | Deepgram Nova | `Token` header | Single POST to `/v1/listen` |
| `assemblyai_model.py` | AssemblyAI | `Authorization` header | 3-step: upload → create transcript → poll (2 s interval) |
| `whisper_model.py` | OpenAI Whisper | `Bearer` token | Multipart POST to `/v1/audio/transcriptions` |

### Models — TTS (`app/models/tts/`)
| File | Provider | Auth | Format Map |
|------|----------|------|------------|
| `base.py` | ABC | — | `synthesize(text, voice_id, …) → (bytes, content_type)` |
| `elevenlabs_model.py` | ElevenLabs v1 | `xi-api-key` header | mp3→mp3_44100_128, wav→pcm_44100 |
| `cartesia_model.py` | Cartesia | `X-API-Key` + `Cartesia-Version` | mp3/wav/pcm with PCM_F32LE encoding |

### Services (`app/services/`)
| File | Responsibility |
|------|----------------|
| `stt_service.py` | Provider routing via `_STT_MODELS` dict → model instances |
| `tts_service.py` | Provider routing via `_TTS_MODELS` dict → model instances |
| `pipecat_service.py` | Pipecat pipeline orchestration (STT, TTS, full STT→TTS), PCM↔WAV conversion |

### Routers (`app/routers/`)
| File | Prefix | Endpoints |
|------|--------|-----------|
| `health.py` | `/api/v1/health` | `GET /health`, `GET /health/providers` |
| `speech_to_text.py` | `/api/v1/stt` | `POST /stt/transcribe` |
| `text_to_speech.py` | `/api/v1/tts` | `POST /tts/synthesize`, `POST /tts/synthesize/metadata` |
| `pipecat.py` | `/api/v1/pipecat` | `POST /pipecat/stt`, `/tts`, `/tts/metadata`, `/pipeline`, `/pipeline/metadata` |

### Utils (`app/utils/`)
| File | Responsibility |
|------|----------------|
| `settings.py` | `Settings(BaseSettings)` — all config centralized here (API keys, URLs, models, voices, thresholds) |
| `exceptions.py` | `STTProviderError` (502), `TTSProviderError` (502), `UnsupportedProviderError` (400), `AudioFileError` (422), `MissingAPIKeyError` (500) |

---

## Configuration (Settings)

All hardcoded values live in `app/utils/settings.py`. API keys are loaded from environment variables via `os.getenv("KEY_NAME", "")` — sourced from `~/.zprofile` locally and TFE variables in DEV/UAT/PROD.

| Category | Settings |
|----------|----------|
| **App** | `app_name`, `app_version`, `debug`, `max_upload_size_mb` (25 MB) |
| **API Keys** | `deepgram_api_key`, `assemblyai_api_key`, `openai_api_key`, `elevenlabs_api_key`, `cartesia_api_key` |
| **Base URLs** | Deepgram, AssemblyAI, OpenAI STT, ElevenLabs, Cartesia |
| **Models** | `deepgram_model` (nova-3), `assemblyai_model` (best), `whisper_model` (whisper-1), `elevenlabs_model` (eleven_multilingual_v2), `cartesia_model` (sonic-2) |
| **Voices** | `elevenlabs_default_voice_id`, `cartesia_default_voice_id` |
| **TTS Tuning** | `elevenlabs_stability` (0.5), `elevenlabs_similarity_boost` (0.75) |
| **Cartesia** | `cartesia_api_version` (2024-06-10), `cartesia_sample_rate` (44100) |
| **Defaults** | `default_stt_provider` (deepgram), `default_tts_provider` (elevenlabs) |

---

## API Endpoints

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Status, app name, version |
| GET | `/api/v1/health/providers` | STT/TTS provider config + API key presence |

### Speech-to-Text
| Method | Path | Input | Output |
|--------|------|-------|--------|
| POST | `/api/v1/stt/transcribe` | `multipart/form-data` — audio file, provider, language, model | `STTResponse` (transcript, confidence, language, duration) |

Accepted audio types: `wav, mpeg, mp3, mp4, ogg, flac, webm, m4a` — max 25 MB.

### Text-to-Speech
| Method | Path | Input | Output |
|--------|------|-------|--------|
| POST | `/api/v1/tts/synthesize` | `TTSRequest` JSON (text, provider, voice_id, language, output_format) | Raw audio bytes (Content-Disposition attachment) |
| POST | `/api/v1/tts/synthesize/metadata` | Same | JSON metadata (provider, format, size_bytes) |

### Pipecat Pipeline
| Method | Path | Input | Output |
|--------|------|-------|--------|
| POST | `/api/v1/pipecat/stt` | Audio file + provider/language/model | `PipecatSTTResponse` |
| POST | `/api/v1/pipecat/tts` | `PipecatTTSRequest` (text, voice, speed 0.25–4.0) | WAV audio |
| POST | `/api/v1/pipecat/tts/metadata` | Same | JSON metadata |
| POST | `/api/v1/pipecat/pipeline` | Audio + STT/TTS config | Processed WAV (speech→text→speech) |
| POST | `/api/v1/pipecat/pipeline/metadata` | Same | JSON metadata |

---

## Key Design Patterns

1. **Strategy Pattern** — `BaseSTTModel` / `BaseTTSModel` ABCs let services swap providers at runtime via dictionary lookup
2. **Singleton Services** — `stt_service`, `tts_service`, `pipecat_service` module-level instances
3. **Centralized Config** — All provider URLs, model IDs, voice IDs, and tuning params in one `Settings` class (`@lru_cache`)
4. **Async-First** — Every I/O call uses `httpx.AsyncClient` or pipecat's async runner
5. **Frame Processing** — Pipecat uses `Pipeline` → `PipelineTask` → `PipelineRunner` with a custom `ResultCollector(FrameProcessor)` to intercept `TranscriptionFrame` and `TTSAudioRawFrame`
6. **Dual Endpoints** — TTS and pipeline routers expose both raw-audio and metadata-only variants
7. **Custom Exceptions** — Typed HTTP exceptions (`STTProviderError`, `TTSProviderError`, etc.) with consistent error formatting

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.115.0 | Web framework |
| `uvicorn[standard]` | ≥0.34.0 | ASGI server |
| `pydantic` | ≥2.0.0 | Data validation |
| `pydantic-settings` | ≥2.0.0 | Environment-aware settings |
| `httpx` | ≥0.28.0 | Async HTTP client |
| `python-multipart` | ≥0.0.18 | File upload parsing |
| `pipecat-ai` | ≥0.0.106 | AI pipeline framework |

---

## Provider Comparison (from test outputs below)

| Metric | Deepgram (nova-3) | Whisper (whisper-1) |
|--------|-------------------|---------------------|
| Transcript accuracy | High — proper punctuation, paragraph-level | High — slightly different word choices |
| Confidence score | 0.9916 | Not provided (null) |
| Duration reported | 228.36 s | 228.36 s |
| Language detection | `en` (ISO code) | `english` (full name) |

---

---

# API Test Outputs

---

# STT model info :

## Deepgram Output


### Input
```
curl -X 'POST' \
  'http://localhost:8047/api/v1/stt/transcribe' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'audio=@Arthur.mp3;type=audio/mpeg' \
  -F 'provider=deepgram' \
  -F 'language=en' \
  -F 'model=nova-3'
```

### Output
```
{
  "provider": "deepgram",
  "transcript": "The story of Arthur the rat. Once upon a time, there was a young rat who couldn't make up his mind. Whenever the other rat said to him if he would like to come out hunting with them, he would answer in a hoarse voice, I don't know. And when they said, Would you rather stay inside? He would say yes or no, either. He'd always shake making a choice. One fine day, his aunt Josephine said to him, now look here, no one will ever care for you if you carry on like this. You have no more mind of your own than a greasy old blade of grass. The young rat coughed and looked quiet as usual but said nothing. Don't you think so, said his aunt, stamping her foot, for she couldn't bear to see the young rat so cold blooded. I don't know was all he ever answered. And then he walked off to think for an hour or more whether he would stay in his hole in the ground or go out into the loft. One night the rats heard a loud noise in the loft. It was a very dreary old place. The roof let the rain come down, come washing in. The beams and the rafters had all rotted through, so the whole thing was quite unsafe. At last, one of the joists gave way, and the beams fell with one edge on the floor. The wall shook, the cupola fell off, and all the rats' hairs stooped on in with fear and horror. This won't do, city leaders. We we can't stay cooped up here any longer. So it's sent out the scouts to search for a new home. A little later on that evening, scouts come back and said they had found an old fashioned horse barn where there would be room and board for all of them. The leader gave the order at once, company falling in, and the rats crawled out of the hole right away and stood on the floor in a long line. Just then the old rat caught sight of young Arthur, that was the name of the shaker. He wasn't in the line, and he wasn't exactly outside it. He stood just by it. Come on. Get in line, growled the old rat coarsely. Of course, you're coming too. I don't know, said Arthur calmly. Why the idea of it. You don't think it's safe here anymore, do you? I'm not certain, said Arthur undaunted. Your roof may not fall down yet. Well, said the old rat, you can't wait for us to for you to join us. Then he turned to the other and shouted, right about face, march. And the long wind marched out the barn while the young rat watched him. I think I'll go tomorrow, he said to himself, but then again perhaps I won't. It's so nice and snug here. I guess I'll go back to my hole under the log for a while just to make up my mind. But during the night there was a big crash. Down came beams, rafters, joists, the whole business. Next morning, it was a foggy day, some men came to look over the damage. It seemed odd to them that the old building was not haunted by rats. But at last one of them happened to move aboard and he caught sight of a young rat, quite dead, half in and half out of his hole. Thus, the shirker got his due and there was no mourning for him.",
  "confidence": 0.9916353,
  "language": "en",
  "duration": 228.36244
}

```


# whisper:

### Input
```
curl -X 'POST' \
  'http://localhost:8047/api/v1/stt/transcribe' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'audio=@Arthur.mp3;type=audio/mpeg' \
  -F 'provider=whisper' \
  -F 'language=en' \
  -F 'model=whisper-1'
```

### Output
```
{
  "provider": "whisper",
  "transcript": "The story of Arthur the Rat. Once upon a time, there was a young rat who couldn't make up his mind. Whenever the other rats asked him if he would like to come out hunting with them, he would answer in a hoarse voice, I don't know. And when they said, would you rather stay inside, he would say yes or no either. He'd always shake making a choice. One fine day, his Aunt Josephine said to him, now look here, no one will ever care for you if you carry on like this. You have no more mind of your own than a greasy old blade of grass. The young rat coughed and looked quiet as usual, but said nothing. Don't you think so, said his aunt, stamping her foot, for she couldn't bear to see the young rat so cold-blooded. I don't know, was all he ever answered. And then he walked off to think for an hour or more, whether he would stay in his hole in the ground or go out into the loft. One night the rats heard a loud noise in the loft. It was a very dreary old place. The roof let the rain come down, come washing in. The beams and the rafters had all rotted through. So the whole thing was quite unsafe. At last one of the joists gave way, and the beams fell with one edge on the floor. The walls shook, the cupola fell off, and all the rats' hair stood on end with fear and horror. This won't do, city leader. We can't stay cooped up here any longer. So they sent out scouts to search for a new home. A little later on that evening, the scouts came back and said they'd find an old-fashioned art farm where there would be room for all of them. The leader gave the order at once. Come new fallen in. And the rats crawled out of the hole right away and stood on the floor in a long line. Just then the old rat caught sight of young Arthur. That was the name of the shaker. He wasn't in the line, and he wasn't exactly outside it. He stood just by it. Come on, get in line. Growled the old rat coarsely. Of course you're coming too. I don't know, said Arthur calmly. Why, the idea of it. You don't think it's safe here anymore, do you? I'm not certain, said Arthur undaunted. The roof may not fall down yet. Well, said the old rat, you can't wait for you to join us. Then he turned to the other and shot it right about the face. Marked. And the long line marched out of the barn while the young rat watched him. I think I'll go tomorrow, he said to himself. But then again, perhaps I won't. It's so nice and snug here. I guess I'll go back to my hole under the log for a while just to make up my mind. But during the night there was a big crash. Down came beams, rafters, joists, the whole business. Next morning, it was a foggy day, some men came to look over the damage. It seemed odd to them that the old building was not haunted by rats. But at last one of them happened to move aboard, and he caught sight of a young rat, quite dead, half in and half out of his hole. Thus the shirker got his due and there was no mourning for him.",
  "confidence": null,
  "language": "english",
  "duration": 228.36000061035156
}
```



# TTS Model Info 

## ElevnLabs

### Input
```

curl -X 'POST' \
  'http://localhost:8047/api/v1/tts/synthesize' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "The story of Arthur the rat. Once upon a time, there was a young rat who couldn'\''t make up his mind. Whenever the other rat said to him if he would like to come out hunting with them, he would answer in a hoarse voice, I don'\''t know. And when they said, Would you rather stay inside? He would say yes or no, either. He'\''d always shake making a choice. One fine day, his aunt Josephine said to him, now look here, no one will ever care for you if you carry on like this. You have no more mind of your own than a greasy old blade of grass. The young rat coughed and looked quiet as usual but said nothing. Don'\''t you think so, said his aunt, stamping her foot, for she couldn'\''t bear to see the young rat so cold blooded. I don'\''t know was all he ever answered. And then he walked off to think for an hour or more whether he would stay in his hole in the ground or go out into the loft. One night the rats heard a loud noise in the loft. It was a very dreary old place. The roof let the rain come down, come washing in. The beams and the rafters had all rotted through, so the whole thing was quite unsafe. At last, one of the joists gave way, and the beams fell with one edge on the floor. The wall shook, the cupola fell off, and all the rats'\'' hairs stooped on in with fear and horror. This won'\''t do, city leaders. We we can'\''t stay cooped up here any longer. So it'\''s sent out the scouts to search for a new home. A little later on that evening, scouts come back and said they had found an old fashioned horse barn where there would be room and board for all of them. The leader gave the order at once, company falling in, and the rats crawled out of the hole right away and stood on the floor in a long line. Just then the old rat caught sight of young Arthur, that was the name of the shaker. He wasn'\''t in the line, and he wasn'\''t exactly outside it. He stood just by it. Come on. Get in line, growled the old rat coarsely. Of course, you'\''re coming too. I don'\''t know, said Arthur calmly. Why the idea of it. You don'\''t think it'\''s safe here anymore, do you? I'\''m not certain, said Arthur undaunted. Your roof may not fall down yet. Well, said the old rat, you can'\''t wait for us to for you to join us. Then he turned to the other and shouted, right about face, march. And the long wind marched out the barn while the young rat watched him. I think I'\''ll go tomorrow, he said to himself, but then again perhaps I won'\''t. It'\''s so nice and snug here. I guess I'\''ll go back to my hole under the log for a while just to make up my mind. But during the night there was a big crash. Down came beams, rafters, joists, the whole business. Next morning, it was a foggy day, some men came to look over the damage. It seemed odd to them that the old building was not haunted by rats. But at last one of them happened to move aboard and he caught sight of a young rat, quite dead, half in and half out of his hole. Thus, the shirker got his due and there was no mourning for him.",
  "provider": "elevenlabs",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb",
  "language": "en",
  "output_format": "mp3"
}'

```

### Output :
```
 access-control-allow-credentials: true 
 access-control-allow-origin: http://localhost:8047 
 content-disposition: attachment; filename=speech.mp3 
 content-length: 2911547 
 content-type: audio/mpeg 
 date: Sun,22 Mar 2026 03:16:23 GMT 
 server: uvicorn 
 vary: Origin 

File Generated 
```


## Cartesia

### Input
```
curl -X 'POST' \
  'http://localhost:8047/api/v1/tts/synthesize' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Welcome to new world jai hanuman",
  "provider": "cartesia",
  "voice_id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
  "language": "en",
  "output_format": "mp3"
}'

```

### Output

```
 access-control-allow-credentials: true 
 access-control-allow-origin: http://localhost:8047 
 content-disposition: attachment; filename=speech.mp3 
 content-length: 43093 
 content-type: audio/mpeg 
 date: Sun,22 Mar 2026 03:52:46 GMT 
 server: uvicorn 
 vary: Origin 
```

# Pipecat Operations

## Input

curl -X 'POST' \
  'http://localhost:8047/api/v1/pipecat/stt' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'audio=@Arthur.mp3;type=audio/mpeg' \
  -F 'provider=openai' \
  -F 'language=en' \
  -F 'model=whisper-1'

## Output

```
	
Response body
Download
{
  "provider": "openai",
  "transcript": "The story of Arthur the Rat. Once upon a time, there was a young rat who couldn't make up his mind. Whenever the other rats asked him if he would like to come out hunting with them, he would answer in a hoarse voice, I don't know. And when they said, would you rather stay inside, he would say yes or no either. He'd always shake making a choice. One fine day, his Aunt Josephine said to him, now look here, no one will ever care for you if you carry on like this. You have no more mind of your own than a greasy old blade of grass. The young rat coughed and looked quiet as usual, but said nothing. Don't you think so, said his aunt, stamping her foot, for she couldn't bear to see the young rat so cold-blooded. I don't know, was all he ever answered. And then he walked off to think for an hour or more, whether he would stay in his hole in the ground or go out into the loft. One night the rats heard a loud noise in the loft. It was a very dreary old place. The roof let the rain come down, come washing in. The beams and the rafters had all rotted through. So the whole thing was quite unsafe. At last one of the joists gave way, and the beams fell with one edge on the floor. The walls shook, the cupola fell off, and all the rats' hair stood on end with fear and horror. This won't do, city leader. We can't stay cooped up here any longer. So they sent out scouts to search for a new home. A little later on that evening, the scouts came back and said they'd find an old-fashioned art farm where there would be room for all of them. The leader gave the order at once. Come new fallen in. And the rats crawled out of the hole right away and stood on the floor in a long line. Just then the old rat caught sight of young Arthur. That was the name of the shaker. He wasn't in the line, and he wasn't exactly outside it. He stood just by it. Come on, get in line. Growled the old rat coarsely. Of course you're coming too. I don't know, said Arthur calmly. Why, the idea of it. You don't think it's safe here anymore, do you? I'm not certain, said Arthur undaunted. The roof may not fall down yet. Well, said the old rat, you can't wait for you to join us. Then he turned to the other and shouted right about the face. Marked. And the long line marched out the barn while the young rat watched him. I think I'll go tomorrow, he said to himself. But then again, perhaps I won't. It's so nice and snug here. I guess I'll go back to my hole under the log for a while just to make up my mind. But during the night there was a big crash. Down came beams, rafters, joists, the whole business. Next morning, it was a foggy day. Some men came to look over the damage. It seemed odd to them that the old building was not haunted by rats. But at last one of them happened to move aboard, and he caught sight of a young rat, quite dead, half in and half out of his hole. Thus the shirker got his due and there was no mourning for him.",
  "language": "en"
}
```

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
