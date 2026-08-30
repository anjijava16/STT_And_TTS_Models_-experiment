# 05 — Provider Comparison & Benchmarking

A practitioner's view of which provider to pick when, with code to compare
them apples-to-apples on **your** audio.

> Prices and feature flags shift constantly. Treat the numbers as *order of
> magnitude*, not gospel — always verify on the provider's pricing page when
> committing.

---

## 5.1 STT providers

| Provider | Model(s) | Streaming | Diarization | $ / minute (approx) | Best for |
|----------|----------|-----------|-------------|---------------------|----------|
| **Deepgram** | Nova-3, Nova-2, Whisper Cloud | ✅ <300 ms | ✅ | ~$0.0043 (Nova-3) | Real-time voice agents |
| **AssemblyAI** | Universal-Streaming, Best | ✅ | ✅ | ~$0.0037 | Meeting/podcast analytics |
| **OpenAI** | whisper-1, gpt-4o-transcribe | partial | ❌ | $0.006 (whisper), $0.006 (gpt-4o-tx) | Quick batch jobs |
| **Azure** | Speech SDK | ✅ | ✅ | ~$1/hour | Enterprise / compliance |
| **Google** | Chirp 2, Latest_Long | ✅ | ✅ | ~$0.024 (premium) | Multilingual reach |
| **AWS Transcribe** | Standard, Call Analytics | ✅ | ✅ | ~$0.024 | AWS-native stacks |
| **Speechmatics** | Ursa | ✅ | ✅ | ~$0.30/hour | Broadcast quality, on-prem |
| **Rev.ai** | Reverb | ✅ | ✅ | ~$0.02/min | Captions, accuracy-first |
| **Local Whisper** (self-host) | large-v3-turbo / distil | ❌ (with hacks) | via pyannote | GPU cost only | Privacy, batch volume |
| **NVIDIA Riva Parakeet** | RNN-T 1.1B | ✅ true | ✅ | self-host | On-prem real-time |

### Pick-by-need cheat sheet

```
Voice agent, low latency, EN/ES         →  Deepgram Nova-3
Long-form analytics + topics + sentiment →  AssemblyAI
Big multilingual coverage                →  Azure or Google Chirp 2
On-prem / HIPAA / SOC2 / EU              →  Speechmatics or Riva or self-host Whisper
Cheap batch, accuracy good enough        →  Self-host faster-whisper
Demo today                               →  OpenAI (whisper-1 or gpt-4o-transcribe)
```

---

## 5.2 TTS providers

| Provider | Model | Streaming TTFB | Voice clone | $ / 1M chars (approx) | Best for |
|----------|-------|----------------|-------------|------------------------|----------|
| **ElevenLabs** | Turbo v2.5, v3, Multilingual v2 | ~150 ms | ✅ instant + pro | ~$0.30 (Turbo) | Highest expressivity |
| **Cartesia** | Sonic, Sonic Turbo | ~40-90 ms | ✅ | ~$0.06 | Ultra-low latency agents |
| **OpenAI** | gpt-4o-mini-tts, tts-1-hd | ~250 ms | ❌ | ~$0.015 (tts-1) | One-shot synthesis |
| **Azure** | Neural TTS | ~200 ms | ✅ (custom voice) | ~$0.016 (neural) | Enterprise, SSML |
| **Google** | Chirp 3 HD voices | ~250 ms | ✅ | ~$0.016 | Multilingual reach |
| **AWS Polly** | Neural / Generative | ~300 ms | ✅ | ~$0.016 | AWS-native |
| **PlayHT** | Play 3.0 mini | ~250 ms | ✅ | ~$0.04 | Voice clone bank |
| **Resemble.ai** | Localize | ~300 ms | ✅ | varies | Multilingual clone |
| **Coqui XTTS** (self-host) | v2 | ~chunked 400 ms | ✅ from 6s | GPU cost only | Free/open clone POCs |
| **Piper** (self-host) | onnx voices | ~100 ms on CPU | ❌ | $0 | Edge, robots, kiosks |
| **Kokoro 82M** (self-host) | onnx | ~150 ms on CPU | ❌ | $0 | Tiny but solid |

### Pick-by-need cheat sheet

```
Production voice agent, latency-critical →  Cartesia Sonic, or ElevenLabs Turbo
Expressive narration / audiobook         →  ElevenLabs v3
Multilingual + SSML                      →  Azure Neural TTS
On-device / offline                      →  Piper or Kokoro
Voice clone POC, OSS                     →  Coqui XTTS v2 or OpenVoice v2
Big audiobook batch, cheap               →  ElevenLabs Turbo or Azure
```

---

## 5.3 Benchmark harness — same audio across providers (STT)

```python
"""
bench_stt.py — transcribe one file with N providers; compare WER + latency.
"""
# advanced
import asyncio, os, time
from dataclasses import dataclass
from pathlib import Path
from jiwer import wer

REF      = Path("ref_transcript.txt").read_text().strip()
WAV_PATH = "sample.wav"

@dataclass
class Result:
    provider: str
    text: str
    latency_ms: float
    wer: float

# --- Deepgram --------------------------------------------------------------
async def via_deepgram() -> Result:
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
    dg = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
    with open(WAV_PATH, "rb") as f:
        src: FileSource = {"buffer": f.read()}
    t0 = time.perf_counter()
    r = await dg.listen.asyncrest.v("1").transcribe_file(
        src, PrerecordedOptions(model="nova-3", smart_format=True))
    txt = r.results.channels[0].alternatives[0].transcript
    return Result("deepgram", txt, (time.perf_counter()-t0)*1000, wer(REF, txt))

# --- AssemblyAI ------------------------------------------------------------
async def via_assemblyai() -> Result:
    import assemblyai as aai
    aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]
    t0 = time.perf_counter()
    tx = aai.Transcriber().transcribe(WAV_PATH)
    return Result("assemblyai", tx.text, (time.perf_counter()-t0)*1000, wer(REF, tx.text))

# --- OpenAI Whisper API ----------------------------------------------------
async def via_openai() -> Result:
    from openai import AsyncOpenAI
    cli = AsyncOpenAI()
    t0 = time.perf_counter()
    with open(WAV_PATH, "rb") as f:
        r = await cli.audio.transcriptions.create(model="whisper-1", file=f)
    return Result("openai_whisper", r.text, (time.perf_counter()-t0)*1000, wer(REF, r.text))

# --- Local faster-whisper --------------------------------------------------
async def via_local_whisper() -> Result:
    from faster_whisper import WhisperModel
    m = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    t0 = time.perf_counter()
    segs, _ = m.transcribe(WAV_PATH, beam_size=5, vad_filter=True)
    txt = " ".join(s.text for s in segs).strip()
    return Result("local_whisper", txt, (time.perf_counter()-t0)*1000, wer(REF, txt))

async def main():
    results = await asyncio.gather(via_deepgram(), via_assemblyai(),
                                   via_openai(), via_local_whisper(),
                                   return_exceptions=True)
    for r in results:
        if isinstance(r, Exception): print("ERROR:", r); continue
        print(f"{r.provider:20s}  WER={r.wer*100:5.2f}%   {r.latency_ms:7.0f} ms")

asyncio.run(main())
```

Expected output shape:

```
deepgram              WER= 3.41%      1247 ms
assemblyai            WER= 2.98%      4231 ms
openai_whisper        WER= 4.85%      3104 ms
local_whisper         WER= 3.12%      2890 ms
```

Always benchmark on **your domain audio**, not LibriSpeech. Domain shifts
results by 2–5×.

---

## 5.4 Benchmark harness — same text across providers (TTS)

```python
"""
bench_tts.py — synthesize one prompt with N providers; measure TTFB + total.
"""
# advanced
import asyncio, os, time, json, base64, websockets, aiofiles
from openai import AsyncOpenAI

PROMPT = "Hello, this is a benchmark of text to speech latency and quality."

async def measure(name, coro_factory):
    t0 = time.perf_counter()
    first_byte = None
    total = 0
    async with aiofiles.open(f"out_{name}.pcm", "wb") as f:
        async for chunk in coro_factory():
            if first_byte is None:
                first_byte = (time.perf_counter() - t0) * 1000
            total += len(chunk)
            await f.write(chunk)
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"{name:14s}  TTFB={first_byte:6.0f} ms  total={elapsed:6.0f} ms  bytes={total}")

# --- ElevenLabs ------------------------------------------------------------
async def el_stream():
    VOICE = "JBFqnCBsd6RMkjVDRZzb"
    URI = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE}/stream-input"
           f"?model_id=eleven_turbo_v2_5&output_format=pcm_16000")
    async with websockets.connect(URI) as ws:
        await ws.send(json.dumps({"text": " ",
                                  "xi_api_key": os.environ["ELEVEN_API_KEY"]}))
        await ws.send(json.dumps({"text": PROMPT, "try_trigger_generation": True}))
        await ws.send(json.dumps({"text": ""}))
        async for m in ws:
            d = json.loads(m)
            if d.get("audio"): yield base64.b64decode(d["audio"])
            if d.get("isFinal"): return

# --- OpenAI tts-1 ----------------------------------------------------------
async def oai_stream():
    cli = AsyncOpenAI()
    async with cli.audio.speech.with_streaming_response.create(
        model="tts-1", voice="alloy", input=PROMPT, response_format="pcm",
    ) as r:
        async for chunk in r.iter_bytes(chunk_size=4096):
            yield chunk

# --- Cartesia --------------------------------------------------------------
async def cartesia_stream():
    import cartesia
    cli = cartesia.AsyncCartesia(api_key=os.environ["CARTESIA_API_KEY"])
    async for chunk in cli.tts.sse(
        model_id="sonic-2",
        transcript=PROMPT,
        voice={"mode": "id", "id": "a0e99841-438c-4a64-b679-ae501e7d6091"},
        output_format={"container":"raw","encoding":"pcm_s16le","sample_rate":24000},
    ):
        if hasattr(chunk, "audio") and chunk.audio:
            yield chunk.audio

async def main():
    await measure("elevenlabs", el_stream)
    await measure("openai_tts", oai_stream)
    await measure("cartesia",   cartesia_stream)

asyncio.run(main())
```

Expected:

```
elevenlabs    TTFB=  142 ms  total= 2150 ms  bytes=287000
openai_tts    TTFB=  490 ms  total= 1740 ms  bytes=312000
cartesia      TTFB=   58 ms  total= 1620 ms  bytes=298000
```

Cartesia and ElevenLabs Turbo dominate TTFB; OpenAI is fine for non-realtime.

---

## 5.5 Multilingual coverage matrix

| Lang | Whisper | Deepgram | AssemblyAI | Azure | Google | ElevenLabs |
|------|:-------:|:--------:|:----------:|:-----:|:------:|:----------:|
| English (US/UK/IN) | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ |
| Spanish | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ |
| Hindi | ★★ | ★★ | ★★ | ★★★ | ★★★ | ★★ |
| Mandarin | ★★ | ★★ | ★★ | ★★★ | ★★★ | ★★ |
| Arabic | ★★ | ★ | ★★ | ★★★ | ★★★ | ★★ |
| Telugu/Tamil | ★ | — | — | ★★ | ★★★ | ★ |
| Code-switched | ★★ | ★★ | ★★ | ★★ | ★★ | ★★ |

For Indic languages, prefer Google Chirp 2 or Sarvam.ai (specialized) over
Whisper unless you're going to fine-tune.

---

## 5.6 Decision tree — which provider for your POC

```
What are you building?

├── Customer support voice agent (English, US numbers)
│       STT: Deepgram Nova-3
│       LLM: GPT-4o-mini or Claude 4.5 Haiku
│       TTS: ElevenLabs Turbo v2.5 or Cartesia Sonic
│       Orchestration: VAPI (fast) or LiveKit Agents (custom)
│
├── Multilingual call center (10+ langs)
│       STT: Azure Speech or Google Chirp 2
│       LLM: Claude Opus or GPT-4o
│       TTS: Azure Neural TTS (matches STT lang coverage)
│
├── Healthcare on-prem (HIPAA, no cloud)
│       STT: Self-hosted faster-whisper large-v3 + Silero VAD
│       LLM: Self-hosted Llama 3.3 70B or Qwen 2.5
│       TTS: Piper or self-hosted Coqui XTTS
│
├── Audiobook / narration generator
│       TTS: ElevenLabs v3 (or PlayHT)
│       Use SSML / inline tags for prosody
│
├── Meeting summarizer / transcription SaaS
│       STT: AssemblyAI (best speakers/topics out-of-box)
│       LLM: Claude (best long-context summary)
│       TTS: not needed
│
└── Real-time translation kiosk
        STT: Whisper large-v3 (translate task)
        OR  OpenAI Realtime (audio in, audio out, translate prompt)
        TTS: Azure Neural TTS for target lang
```

Onwards → `06_business_use_cases.md` for full POC scaffolds.
