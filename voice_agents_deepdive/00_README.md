# STT + TTS Deep Dive — Zero to Hero

A practical, code-first deep dive into Speech-to-Text (STT), Text-to-Speech (TTS),
and the full conversational AI pipeline (STT → LLM → TTS).

**Audience:** Expert Python developer with prior hands-on experience using
VAPI, Deepgram, and Dograh. Goal: build deeper foundations and POCs.

---

## How to read this

These notes are designed as a progression. Each file is self-contained, but they
build on each other. Treat it like a textbook + cookbook.

| # | File | What you'll learn | Level |
|---|------|-------------------|-------|
| 01 | [`01_fundamentals.md`](01_fundamentals.md) | Audio signal basics, sampling, codecs, why ML cares | Beginner |
| 02 | [`02_stt_deep_dive.md`](02_stt_deep_dive.md) | STT architectures (CTC, RNN-T, Whisper), Python examples | Beg → Adv |
| 03 | [`03_tts_deep_dive.md`](03_tts_deep_dive.md) | TTS architectures (Tacotron, VITS, neural codec), Python examples | Beg → Adv |
| 04 | [`04_stt_llm_tts_pipeline.md`](04_stt_llm_tts_pipeline.md) | End-to-end voice agent pipeline, latency math, interruption | Intermediate |
| 05 | [`05_provider_comparison.md`](05_provider_comparison.md) | Whisper, Deepgram, AssemblyAI, ElevenLabs, Cartesia, Azure, Google | Reference |
| 06 | [`06_business_use_cases.md`](06_business_use_cases.md) | 10 POCs with Python — call center, meeting bot, IVR, etc. | Practitioner |
| 07 | [`07_advanced_topics.md`](07_advanced_topics.md) | Streaming, VAD, endpointing, barge-in, fine-tuning | Hero |
| 08 | [`08_poc_starter_kits.md`](08_poc_starter_kits.md) | Copy-paste starter projects you can extend | Hero |

---

## The big picture

```
                ┌──────────────────────────────────────────────────────┐
                │              VOICE AI APPLICATION                    │
                └──────────────────────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
 ┌─────────────┐              ┌───────────────┐              ┌─────────────┐
 │   INPUT     │              │   REASONING   │              │   OUTPUT    │
 │             │              │               │              │             │
 │   Mic /     │  ──audio──▶  │  STT  ─text─▶ │  ──text──▶   │   Speaker   │
 │   Phone /   │              │  LLM ─reply─▶ │              │   Phone /   │
 │   Stream    │              │  TTS ─audio─▶ │              │   Stream    │
 └─────────────┘              └───────────────┘              └─────────────┘
        │                              │                              │
        │  WebRTC / Twilio /           │  OpenAI / Anthropic /        │
        │  LiveKit / PyAudio           │  Local LLM (Ollama)          │
        ▼                              ▼                              ▼
   Capture stage                 Brains stage                  Playback stage
```

The three stages all matter, but **latency is dominated by the round trip**:
how fast you can detect end-of-speech, hand the text to the LLM, and stream
the TTS audio back. Anything > 800 ms feels unnatural. Aim < 500 ms.

---

## What you'll be able to build after these notes

1. A streaming microphone → Whisper → console transcriber (offline)
2. A real-time voice chatbot over WebSockets (STT + LLM + TTS)
3. A meeting summarizer that ingests `.wav` / `.mp4`
4. A phone IVR that handles intent classification
5. A multilingual voice clone POC with ElevenLabs / Coqui
6. A latency benchmark harness that compares 4+ providers
7. A hybrid local-first agent (Whisper local + Llama local + Piper TTS)

---

## Conventions used in these notes

- **Python ≥ 3.10**, type hints where helpful.
- All examples use `asyncio` where streaming is involved.
- Secrets via `os.getenv()`. Never hard-coded.
- Diagrams are ASCII (so they survive any markdown renderer / git diff).
- `# beginner`, `# intermediate`, `# advanced` tags inline.

---

Start with `01_fundamentals.md` if you want the full mental model. Skip to
`05_provider_comparison.md` if you just want to pick a stack for a POC today.
