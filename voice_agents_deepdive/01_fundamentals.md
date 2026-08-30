# 01 — Audio & Speech Fundamentals

Before STT/TTS models make any sense, you need a working mental model of the
**audio signal** itself. Skip nothing here — every concept comes back later.

---

## 1.1 What is "audio" to a computer?

Sound is a continuous pressure wave. A microphone samples that wave thousands
of times per second and turns each sample into a number.

```
Continuous waveform (analog):

   amplitude
      │     ___           ___
      │    /   \         /   \
      │   /     \       /     \         ___
   0──┼──/───────\─────/───────\───────/───\────▶ time
      │ /         \___/         \_____/     \___
      │                                          \
      │
                  (a pressure wave over time)

Sampling (digital) at 16 kHz means: take 16,000 measurements per second.

   amplitude
      │   • •
      │  •   •         • •
      │ •     •       •   •          • •
   0──┼•───────•─────•─────•────────•───•────▶ time
      │         • • •       • • • •     • •
      │
            (each dot = one sample, stored as e.g. int16)
```

### Key numbers you MUST internalize

| Parameter | Common values | Why it matters |
|-----------|---------------|----------------|
| Sample rate | 8 kHz (phone), 16 kHz (STT default), 24 kHz (TTS), 44.1 kHz (CD), 48 kHz (studio) | Higher = more detail, but more data. STT models are usually trained at 16 kHz. |
| Bit depth | 16-bit PCM is standard | 16 bits = 65,536 amplitude steps. Enough for speech. |
| Channels | mono (1) vs stereo (2) | STT wants **mono**. Always downmix. |
| Encoding | PCM, μ-law (telephony), Opus (WebRTC), MP3, FLAC | Determines compression vs quality |

**Memorize**: a 1-second mono 16 kHz 16-bit PCM clip = 16,000 × 2 bytes = **32 KB**.
This is why streaming STT can run cheaply.

---

## 1.2 The frequency view — why we use spectrograms

The raw waveform is hard for ML models. Speech is much more learnable in the
**frequency domain** — what frequencies are present, and how loud, over time.

```
Waveform  ──FFT (sliding window)──▶  Spectrogram  ──mel scale──▶  Mel-spectrogram
                                                                       │
                                                                       ▼
                                                              fed to STT model
```

A **spectrogram** is an image: x = time, y = frequency, color = energy.

```
freq (Hz)
8000 │░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ← high freq (fricatives like "s", "f")
4000 │██░░░░██████░░░██░░░░████░░░
2000 │████░░██████████████████████  ← formants (vowel character)
1000 │██████████░░████████████████  ← fundamental + harmonics
 500 │████████████████░░░░████████  ← pitch (voice fundamental)
   0 └────────────────────────────────▶ time
      "h"  "e"   "l"   "l"   "o"
```

A **mel-spectrogram** rescales the y-axis to match human hearing (we're more
sensitive to differences in low frequencies than high). This is what almost
every modern STT/TTS model consumes or produces.

```python
# beginner — see your own voice as a spectrogram
import librosa, librosa.display
import matplotlib.pyplot as plt
import numpy as np

y, sr = librosa.load("hello.wav", sr=16000)        # load + resample
S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80)
S_db = librosa.power_to_db(S, ref=np.max)

librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="mel")
plt.colorbar(format="%+2.0f dB"); plt.title("Mel-spectrogram")
plt.tight_layout(); plt.show()
```

---

## 1.3 Phonemes, graphemes, and why STT/TTS are different problems

```
GRAPHEMES (what you write)      PHONEMES (what you say)
──────────────────────          ──────────────────────
"phone"               ◀────────▶  /f oʊ n/
"tough"               ◀────────▶  /t ʌ f/
"though"              ◀────────▶  /ð oʊ/
"through"             ◀────────▶  /θ r uː/

  ↑ STT goes this way            ↑ TTS goes this way
  audio → phonemes → text         text → phonemes → audio
```

This asymmetry is why:
- **STT** must handle accents, noise, disfluencies ("uh", "um"), and pick the
  right word for ambiguous sounds (e.g., "their" vs "there").
- **TTS** must handle expansion (`$5.25` → "five dollars and twenty-five cents"),
  prosody (where to put stress, where to pause), and emotional tone.

---

## 1.4 Streaming vs batch — the single most important architectural axis

```
┌──────────────────────────────────────────────────────────────────┐
│                        BATCH STT                                 │
│                                                                  │
│  whole audio file ───▶ [   model   ] ───▶ full transcript        │
│                                                                  │
│  pros: highest accuracy, simpler code                            │
│  cons: must wait for end of utterance — bad UX for voice         │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       STREAMING STT                              │
│                                                                  │
│   audio chunk ──┐                                                │
│   audio chunk ──┼──▶ [ streaming  ] ──▶ partial: "the qu..."     │
│   audio chunk ──┤    [   model    ] ──▶ partial: "the quick br.."│
│   audio chunk ──┤                   ──▶ partial: "the quick br.."│
│   audio chunk ──┘                   ──▶ FINAL  : "the quick      │
│                                                  brown fox"      │
│                                                                  │
│  pros: low latency, real-time UX, partials drive UI              │
│  cons: needs WebSocket plumbing, partials may revise             │
└──────────────────────────────────────────────────────────────────┘
```

Two outputs from a streaming STT:
- **Interim / partial**: best guess so far, may change.
- **Final**: model is confident this segment is done. Locked in.

You drive your LLM/agent off **finals** (or "end-of-utterance" events),
but you display **partials** to the user so they see they're being heard.

---

## 1.5 VAD — Voice Activity Detection

Speech ≠ everything in the mic stream. VAD is the gate.

```
                  ┌───────┐
   mic stream ──▶ │  VAD  │ ──┬──▶ speech frames ──▶ STT
                  └───────┘   │
                              └──▶ silence frames ──▶ discard / endpoint signal
```

VAD is what tells your system "the user stopped talking — flush to the LLM."

Common choices:
- **WebRTC VAD** — fast, lightweight, frame-level. Works but noisy.
- **Silero VAD** — small neural net, much more robust. Default for serious work.
- **Provider built-in** — Deepgram's `endpointing`, OpenAI Realtime's
  `server_vad`, ElevenLabs Convo VAD.

```python
# intermediate — Silero VAD in 10 lines
import torch, torchaudio

model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
(get_speech_timestamps, _, read_audio, *_) = utils

wav = read_audio("call.wav", sampling_rate=16000)
speech = get_speech_timestamps(wav, model, sampling_rate=16000)
# speech = [{'start': 4800, 'end': 39200}, ...]  ← sample indices of speech
```

---

## 1.6 The three big audio "gotchas" that bite new POCs

1. **Sample rate mismatch.** Mic gives 48 kHz, model wants 16 kHz. Always
   resample with `librosa.load(..., sr=16000)` or `soxr`. Wrong SR = garbage
   transcript that *looks* like the model is broken.

2. **Stereo vs mono.** Phone audio is often two channels (agent + caller).
   Either downmix (`np.mean(audio, axis=1)`) or treat each channel as a
   separate STT stream — which gives you free speaker diarization.

3. **Endianness / dtype.** Twilio gives μ-law 8 kHz. Browsers give float32
   48 kHz Opus. PyAudio defaults to int16 44.1 kHz. Convert explicitly:

```python
import numpy as np

def pcm16_to_float32(pcm: bytes) -> np.ndarray:
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

def float32_to_pcm16(arr: np.ndarray) -> bytes:
    return (arr * 32768.0).clip(-32768, 32767).astype(np.int16).tobytes()
```

---

## 1.7 Mental model checkpoint

You should now be able to answer:

- Why does Whisper want 16 kHz mono? *(That's its training SR. Anything else gets resampled internally and may lose info.)*
- Why is a phone call 8 kHz? *(Telephony bandwidth is ~300–3400 Hz. 8 kHz Nyquist suffices.)*
- Why do streaming STTs emit "partials"? *(They run continuously; the final decoded path may change as more audio arrives.)*
- Why do TTS models output mel-spectrograms, not waveforms directly? *(Most do both — an acoustic model produces mels, a vocoder turns mels into waveforms. Separating the two is easier to train and modular.)*

Onwards to STT internals → `02_stt_deep_dive.md`.
