# 03 — TTS Deep Dive

How text becomes speech. The flip side of STT, but with very different
problems: prosody, voice identity, emotional expressivity, and latency to
*first audio chunk*.

---

## 3.1 The text-to-speech pipeline (canonical)

```
┌──────────┐   ┌────────────┐   ┌───────────────┐   ┌─────────┐   ┌─────────┐
│  Raw     │──▶│   Text     │──▶│   Acoustic    │──▶│ Vocoder │──▶│  Audio  │
│  text    │   │ normalize  │   │     model     │   │         │   │ output  │
└──────────┘   └────────────┘   └───────────────┘   └─────────┘   └─────────┘
  "I owe       "I owe him          mel-spectrogram      waveform
   him $5"     five dollars"       (80×T tensor)        @ 24kHz

  G2P → phonemes (optional but improves quality)
```

### Stage 1 — Text normalization (often underestimated)

Numbers, dates, currencies, acronyms, abbreviations all expand:

| Input | Expanded |
|-------|----------|
| `$5.25` | "five dollars and twenty-five cents" |
| `Dr. Lee` | "Doctor Lee" |
| `12/25/2025` | "December twenty-fifth, two thousand twenty-five" |
| `NASA` | "NASA" (acronym, say letters or as word) |
| `Wi-Fi` | "Wi Fi" / "wifi" |
| `https://x.io` | "h t t p s colon slash slash x dot i o" (or skip) |

Bad normalization = "I owe him dollar five point two five." Production TTS
SDKs (ElevenLabs, Azure) handle this server-side; if you self-host, use
`nemo-text-processing` or `tn-uk` libs.

### Stage 2 — Acoustic model

Predicts a mel-spectrogram (or discrete acoustic tokens) from phonemes/text.

**Architectures you'll see**:

| Model family | What it is | Streaming? |
|--------------|------------|------------|
| Tacotron 2 | RNN seq2seq + attention | No (autoregressive but slow) |
| FastSpeech 2 | Non-autoregressive transformer | Parallel, fast |
| Glow-TTS / Grad-TTS | Flow / diffusion | Parallel |
| VITS / VITS2 | End-to-end (skips vocoder) | Parallel |
| Bark / Tortoise | Text → audio tokens (GPT-style) | Slow but expressive |
| StyleTTS 2 | Diffusion + style encoder | Fast, very natural |
| **XTTS v2** (Coqui) | Voice clone from 6 sec sample | Near real-time |
| **Cartesia Sonic** | State-space, ~40 ms latency | True streaming |
| **ElevenLabs v3** | Closed model, best expressivity | Streaming |

### Stage 3 — Vocoder

Turns the spectrogram back into a 24 kHz waveform. The unsung hero.

```
mel-spec ──▶ HiFi-GAN / WaveGlow / BigVGAN / Vocos ──▶ waveform
```

Modern "neural codec" models (EnCodec, SoundStream, Mimi) replace the
spec→wave step with discrete tokens that an autoregressive transformer can
emit one at a time — same trick LLMs use for text.

---

## 3.2 The latency game — first byte vs full sentence

For voice agents, **time-to-first-audio (TTFA)** matters more than throughput.

```
Generation start             First chunk plays       Sentence done
      │                            │                       │
      ▼                            ▼                       ▼
──────●────────────────────────────●───────────────────────●──── time
      ←─── TTFA (latency) ─────────→
      ←──────── total generation time ──────────────────────→
                                   ←──────── playback ──────→
```

Good TTS systems start sending audio bytes within ~200 ms of receiving text
and keep the playback buffer fed faster than it drains.

```
┌───────────────────────────────────────────────────────────────────┐
│ STREAMING TTS                                                     │
│                                                                   │
│  LLM token ───┐                                                   │
│  LLM token ───┼──▶ sentence chunker ──▶ TTS ──▶ audio chunk ──┐   │
│  LLM token ───┤                                               │   │
│  LLM token ───┘                                               ▼   │
│                                                          speaker  │
│                                                                   │
│  Trick: don't wait for the full LLM reply. Chunk at the first     │
│  sentence-ending punctuation, send to TTS, start streaming audio  │
│  while the LLM keeps generating.                                  │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3.3 Working with ElevenLabs (you've used adjacent tools — this is the gold standard)

ElevenLabs gives best-in-class expressivity, multilingual voice cloning, and
WebSocket streaming with chunked audio.

### Synchronous (batch) — simplest path

```python
# beginner — basic ElevenLabs synthesis
import os
from elevenlabs.client import ElevenLabs

el = ElevenLabs(api_key=os.environ["ELEVEN_API_KEY"])

audio = el.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",        # "George" voice
    model_id="eleven_turbo_v2_5",
    text="Hello, this is a quick test of streaming TTS.",
    output_format="mp3_44100_128",
)

with open("out.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

### Streaming (production)

```python
# intermediate — ElevenLabs WebSocket streaming
import asyncio, json, base64, os, websockets

VOICE = "JBFqnCBsd6RMkjVDRZzb"
MODEL = "eleven_turbo_v2_5"
URI   = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE}/stream-input"
         f"?model_id={MODEL}&output_format=pcm_16000")

async def tts_stream(text_iter):
    """Yield 16kHz PCM audio chunks as text streams in."""
    async with websockets.connect(URI) as ws:
        await ws.send(json.dumps({
            "text": " ",                               # init
            "voice_settings": {"stability": 0.5,
                               "similarity_boost": 0.8,
                               "use_speaker_boost": True},
            "xi_api_key": os.environ["ELEVEN_API_KEY"],
        }))

        async def sender():
            async for piece in text_iter:
                await ws.send(json.dumps({"text": piece, "try_trigger_generation": True}))
            await ws.send(json.dumps({"text": ""}))    # end

        send_task = asyncio.create_task(sender())
        try:
            async for msg in ws:
                data = json.loads(msg)
                if data.get("audio"):
                    yield base64.b64decode(data["audio"])
                if data.get("isFinal"):
                    break
        finally:
            send_task.cancel()
```

### Voice cloning

```python
# intermediate — clone a voice from a 60-second sample
from elevenlabs.client import ElevenLabs
el = ElevenLabs(api_key=os.environ["ELEVEN_API_KEY"])

voice = el.voices.add(
    name="My Sales Agent",
    description="Warm, energetic, US English",
    files=[open("sample.mp3", "rb")],      # 30–120s of clean audio
)
print("voice_id:", voice.voice_id)
```

Then use that `voice_id` exactly like a stock voice. **Important:** check the
terms of use — voice cloning requires consent from the speaker.

---

## 3.4 Open-source TTS — the practical landscape

| Model | License | Voice clone | Streaming | Best for |
|-------|---------|-------------|-----------|----------|
| **Piper** | MIT | ❌ | ❌ | Edge / embedded / Raspberry Pi |
| **Coqui XTTS v2** | CPML (non-commercial reference) | ✅ from 6 s | ❌ (chunked yes) | POCs, multilingual |
| **OpenVoice v2** | MIT | ✅ | partial | Free commercial use |
| **StyleTTS 2** | MIT | ✅ | ❌ | Highest quality OSS |
| **Bark** | MIT | partial | ❌ | Nonverbal sounds, music |
| **MeloTTS** | MIT | ❌ | yes | Real-time CPU TTS |
| **F5-TTS / E2-TTS** | CC-BY-NC | ✅ | yes | 2025-era reference quality |
| **Kokoro-82M** | Apache 2.0 | ❌ | yes | Tiny model, surprising quality |

### Piper — lightweight server TTS

```python
# beginner — Piper local TTS in pure Python
# pip install piper-tts
import wave, subprocess, sys
from piper import PiperVoice

voice = PiperVoice.load("en_US-amy-medium.onnx",
                        config_path="en_US-amy-medium.onnx.json")

with wave.open("out.wav", "wb") as wf:
    voice.synthesize("Hello from Piper, running on CPU.", wf)
```

Runs at ~10× real-time on a laptop CPU. Good for Raspberry Pi, robots,
embedded kiosks.

### XTTS v2 — open-source voice clone

```python
# intermediate — Coqui XTTS v2 voice clone
from TTS.api import TTS
import torch

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
          gpu=torch.cuda.is_available())

tts.tts_to_file(
    text="Welcome back. Your appointment is confirmed for tomorrow.",
    speaker_wav="my_voice_sample.wav",     # 6+ seconds, clean
    language="en",
    file_path="out.wav",
)
```

### Kokoro — tiny but punchy

```python
# beginner — Kokoro 82M on CPU
from kokoro_onnx import Kokoro
kk = Kokoro("kokoro-v0_19.onnx", "voices.json")
samples, sr = kk.create("Hello there!", voice="af_sarah", speed=1.0, lang="en-us")
import soundfile as sf
sf.write("out.wav", samples, sr)
```

---

## 3.5 Prosody — making it not sound robotic

Three lever categories:

1. **SSML** (Speech Synthesis Markup Language) — supported by Azure, Google,
   AWS Polly. Not by ElevenLabs (it uses inline cues).

```xml
<speak>
  <prosody rate="medium" pitch="+2st">
    Good morning! <break time="300ms"/>
    Your balance is <say-as interpret-as="currency">$1,234.56</say-as>.
  </prosody>
  <emphasis level="strong">Please</emphasis> verify your identity.
</speak>
```

2. **Inline tags** (ElevenLabs v3):

```
"That was incredible! [laughs] I can't believe it actually worked.
[whispers] Don't tell anyone I said that."
```

3. **Voice settings** sliders — stability vs similarity vs style. Lower
   stability = more emotional variance but more outliers.

---

## 3.6 Choosing a TTS for your use case

```
                    Need voice clone?
                    │
              ┌─────┴─────┐
              yes         no
              │           │
        Commercial use?   │
        │                 │
    ┌───┴───┐             │
    yes     no            │
    │       │             │
    ▼       ▼             ▼
  Eleven  XTTS/      ┌────────────────────────────┐
  Cartesia OpenVoice │  Latency-critical (<200ms)? │
                    └────────────────────────────┘
                              │
                       ┌──────┴──────┐
                       yes           no
                       │             │
                       ▼             ▼
                  Cartesia      Quality-first?
                  Eleven        │
                  Turbo     ┌───┴───┐
                            yes     no
                            │       │
                            ▼       ▼
                       Eleven    Piper /
                       v3        Kokoro /
                                 Azure
```

---

## 3.7 Latency budget math (you should be able to do this in your head)

Typical voice agent target: **end-of-user-speech → first audio byte ≤ 700 ms**.

```
Component                          Typical          Aggressive
────────────────────────────────────────────────────────────────
Endpointing (VAD silence wait)     300 ms           150 ms
STT final emit                     150 ms            80 ms
LLM TTFT (first token)             400 ms           200 ms
Sentence accumulation              100 ms            50 ms
TTS time-to-first-byte             250 ms           120 ms
Network jitter / playback prefill  100 ms            50 ms
────────────────────────────────────────────────────────────────
TOTAL                             1300 ms           650 ms
```

Tricks that cut the budget:
- **Stream LLM tokens directly into TTS** as soon as first sentence punctuation arrives.
- **Pre-warm** TTS WS connection.
- **Speculative TTS** — start synthesizing the most likely continuation before LLM finishes.
- **Smaller VAD silence threshold** with a confirmation pass (risky — may cut user off).

See `07_advanced_topics.md` for full pipelining.

---

## 3.8 Quality evaluation: MOS, WER, similarity

- **MOS** (Mean Opinion Score) — humans rate 1–5. Still the gold standard,
  expensive.
- **UTMOS / NISQA** — neural MOS predictors. Free, ~0.7 correlation with humans.
- **WER on TTS output** — synthesize → STT → compare. Catches mispronunciations.
- **Speaker similarity** (for clones) — cosine sim of speaker embeddings
  (Resemblyzer, ECAPA-TDNN).

```python
# advanced — automatic TTS regression check
from resemblyzer import VoiceEncoder, preprocess_wav

enc = VoiceEncoder()
ref_emb  = enc.embed_utterance(preprocess_wav("reference_voice.wav"))
gen_emb  = enc.embed_utterance(preprocess_wav("generated.wav"))
sim = (ref_emb @ gen_emb) / ((ref_emb @ ref_emb)**0.5 * (gen_emb @ gen_emb)**0.5)
print(f"speaker similarity: {sim:.3f}")        # > 0.85 = "same voice"
```

---

## 3.9 What to remember

- Two-stage (acoustic + vocoder) is the canonical architecture; end-to-end
  (VITS, neural codec) is the modern frontier.
- For voice agents, **time-to-first-audio** is the metric — not WER.
- Use ElevenLabs/Cartesia for production quality, XTTS/Piper for self-hosted.
- Text normalization is half the engineering problem.
- Stream from LLM directly into TTS — never wait for the full LLM reply.

Next → `04_stt_llm_tts_pipeline.md` — full conversational pipeline.
