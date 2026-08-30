# 02 — STT Deep Dive

How speech-to-text actually works, from "what's a phoneme classifier" to
"why does Whisper hallucinate, and how do I stop it."

---

## 2.1 The four eras of STT

```
1980s ─ HMM-GMM ────────────▶  hand-crafted acoustic + lang models, OK on phones
2010s ─ DNN-HMM ────────────▶  swap GMM for a deep net acoustic model
2015+ ─ End-to-end CTC/RNN-T▶  one neural net: audio → text, no phoneme stage
2022+ ─ Encoder-decoder LLMs▶  Whisper / OWSM — STT *is* a sequence task
```

You'll never touch HMM-GMM in production today, but knowing the trajectory
explains why modern models are so much better and why they fail differently
(hallucination, not phoneme misclassification).

---

## 2.2 Three end-to-end architectures you'll encounter

### A) CTC — Connectionist Temporal Classification

```
audio chunks (T frames)
   │
   ▼
┌─────────────┐
│   encoder   │   e.g. Conformer / Wav2Vec2
└─────────────┘
   │   per-frame logits over vocab + <blank>
   ▼
┌─────────────┐
│ CTC decoder │   collapses repeats, removes <blank>
└─────────────┘
   │
   ▼
"the quick brown fox"
```

- One forward pass per chunk. **Naturally streaming.**
- No language model built in — you bolt on an external LM for accuracy.
- **Example models**: Wav2Vec2, NVIDIA Citrinet, NeMo Conformer-CTC.

```python
# beginner — CTC with HuggingFace Wav2Vec2
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch, librosa

p = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
m = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

audio, _ = librosa.load("hello.wav", sr=16000)
inputs = p(audio, sampling_rate=16000, return_tensors="pt")
with torch.no_grad():
    logits = m(**inputs).logits
ids = torch.argmax(logits, dim=-1)
print(p.batch_decode(ids)[0])
```

### B) RNN-Transducer (RNN-T)

```
            ┌────────────────┐
audio ───▶  │ audio encoder  │ ──┐
            └────────────────┘   │
                                 ├──▶ joiner ──▶ next token
            ┌────────────────┐   │
prev text ▶ │ label encoder  │ ──┘
            └────────────────┘
```

- Audio encoder + label (text) encoder + small joint net.
- **The streaming gold standard for production** — Google, Apple, Amazon all
  use variants for on-device dictation.
- Better than CTC because it can condition on previously emitted text.

### C) Encoder-Decoder (Whisper-style)

```
audio (30s mel-spec)
   │
   ▼
┌───────────────┐
│ Transformer   │   (audio encoder, bidirectional)
│ encoder       │
└───────────────┘
   │  audio representation
   ▼
┌───────────────┐    <|en|> <|transcribe|> the quick ...
│ Transformer   │    │   ▲                ▲
│ decoder       │ ◀──┘   └─ autoregressive ┘
└───────────────┘
   │
   ▼
"the quick brown fox"
```

- Treats STT like translation: audio "language" → text "language."
- Massive multitask training: transcription, translation, language ID, VAD.
- **Not natively streaming** (fixed 30 s window) — but you can chunk + overlap.
- Hallucinates on silence/noise because the LM prior is so strong.
- **Example models**: OpenAI Whisper, Distil-Whisper, OWSM, Canary (NVIDIA),
  SeamlessM4T (Meta).

---

## 2.3 Whisper deeply — what nobody tells you in the readme

### Architecture sizes (memorize the trade-off)

| Model | Params | VRAM | Speed (RTF on M2) | Use when |
|-------|-------:|-----:|------------------:|----------|
| `tiny` | 39 M | ~1 GB | 0.05x | Hobby / low-power |
| `base` | 74 M | ~1 GB | 0.07x | Edge devices |
| `small` | 244 M | ~2 GB | 0.15x | Decent balance |
| `medium` | 769 M | ~5 GB | 0.4x | Production-ish |
| `large-v3` | 1.55 B | ~10 GB | 1.0x | Best accuracy |
| `large-v3-turbo` | 809 M | ~6 GB | 0.3x | **Default** for most servers |

RTF (Real-Time Factor) < 1.0 means faster than real-time on that hardware.

### The "best" practical Whisper today: `faster-whisper`

CTranslate2-based reimplementation. ~4× faster than the reference, same accuracy.

```python
# beginner — production-quality local STT in 10 lines
from faster_whisper import WhisperModel

model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
# CPU fallback: WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

segments, info = model.transcribe(
    "call.wav",
    beam_size=5,
    vad_filter=True,                       # cuts silence — kills hallucination
    vad_parameters=dict(min_silence_duration_ms=500),
    word_timestamps=True,                  # per-word timing
)
print(f"Detected language: {info.language} ({info.language_probability:.2f})")
for seg in segments:
    print(f"[{seg.start:.2f}-{seg.end:.2f}]  {seg.text}")
    for w in seg.words:
        print(f"   {w.word} ({w.start:.2f}-{w.end:.2f}, p={w.probability:.2f})")
```

### Whisper failure modes (and how to fight them)

| Failure | Cause | Fix |
|---------|-------|-----|
| Repeats: "thanks for watching thanks for watching..." | Trained on YouTube; silence + LM prior collapse | `vad_filter=True`, `condition_on_previous_text=False`, `no_repeat_ngram_size=3` |
| Wrong language / random translation | Multilingual model + ambiguous accent | Force `language="en"` |
| Misses domain words ("Dograh", "VAPI") | Vocabulary bias | Use `initial_prompt="Discussion about Dograh, VAPI, Deepgram..."` |
| Strips punctuation | Old config | Use `large-v3` / `turbo`; `without_timestamps=False` |
| Slow on long files | No chunking | Use `faster-whisper` segments, parallelize, or use `pywhispercpp` |

### Streaming Whisper (it doesn't natively, but you can fake it)

```python
# intermediate — pseudo-streaming with overlapping windows
import numpy as np
from faster_whisper import WhisperModel

model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")

WINDOW = 30 * 16000          # 30 s
STRIDE = 5  * 16000          # 5 s overlap
buf: list[float] = []

def push(chunk: np.ndarray) -> str | None:
    """Call with each ~1s chunk of 16kHz float32 audio."""
    buf.extend(chunk.tolist())
    if len(buf) < WINDOW:
        return None
    audio = np.asarray(buf[-WINDOW:], dtype=np.float32)
    segs, _ = model.transcribe(audio, beam_size=1, vad_filter=True)
    text = " ".join(s.text for s in segs)
    # slide window forward
    del buf[:STRIDE]
    return text
```

For truly low-latency streaming, use a *real* streaming model (Deepgram Nova-3,
AssemblyAI Universal-Streaming, NVIDIA Riva Parakeet). See section 2.6.

---

## 2.4 Word-level confidence, diarization, timestamps

For business applications (call centers, compliance, transcription QA), these
secondary outputs matter as much as the text itself.

```
{
  "text": "Yes I'd like to cancel my subscription",
  "words": [
    {"w": "Yes",          "start": 0.10, "end": 0.32, "p": 0.99, "spk": "agent"},
    {"w": "I'd",          "start": 0.40, "end": 0.55, "p": 0.94, "spk": "agent"},
    {"w": "like",         "start": 0.56, "end": 0.72, "p": 0.98, "spk": "agent"},
    {"w": "to",           "start": 0.73, "end": 0.80, "p": 0.99, "spk": "agent"},
    {"w": "cancel",       "start": 0.81, "end": 1.10, "p": 0.71, "spk": "agent"},
    {"w": "my",           "start": 1.11, "end": 1.18, "p": 0.99, "spk": "agent"},
    {"w": "subscription", "start": 1.19, "end": 1.85, "p": 0.88, "spk": "agent"}
  ],
  "language": "en",
  "duration": 1.92,
  "speakers": ["agent", "caller"]
}
```

### Diarization (who said what)

```python
# advanced — Whisper transcript + pyannote diarization
from pyannote.audio import Pipeline
from faster_whisper import WhisperModel

stt = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
diar = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.environ["HF_TOKEN"],
)

segments, _ = stt.transcribe("call.wav", word_timestamps=True)
diarization = diar("call.wav")

def speaker_at(t: float) -> str:
    for turn, _, spk in diarization.itertracks(yield_label=True):
        if turn.start <= t <= turn.end:
            return spk
    return "unknown"

for seg in segments:
    for w in seg.words:
        mid = (w.start + w.end) / 2
        print(f"{speaker_at(mid)}: {w.word}")
```

---

## 2.5 The accuracy metric: WER

**Word Error Rate** = (Substitutions + Insertions + Deletions) / total reference words.

```
reference :  the quick brown fox jumps
hypothesis:  the quick brown dog jumps         ← 1 substitution
                                  WER = 1/5 = 20%

reference :  the quick brown fox jumps
hypothesis:  the quick fox jumps               ← 1 deletion  ("brown")
                                  WER = 1/5 = 20%

reference :  the quick brown fox jumps
hypothesis:  the very quick brown fox jumps    ← 1 insertion ("very")
                                  WER = 1/5 = 20%
```

```python
# beginner — evaluate WER
from jiwer import wer, Compose, ToLowerCase, RemovePunctuation, Strip

transform = Compose([ToLowerCase(), RemovePunctuation(), Strip()])
print(wer(reference, hypothesis,
          reference_transform=transform, hypothesis_transform=transform))
```

Rule of thumb: < 5 % WER on clean speech is "good", < 10 % on noisy/phone
audio is "production-acceptable" for most chatbots. Below ~ 3 % is approaching
human-level on the same data.

---

## 2.6 Cloud STT — when not to run Whisper yourself

You'd run a cloud STT (Deepgram, AssemblyAI, Azure, Google) when you need
*any* of:

- True real-time streaming (< 300 ms partials).
- Diarization, sentiment, topic detection out-of-box.
- Phone-grade 8 kHz μ-law handling without you writing it.
- Multi-language without managing big models.
- 99.95 % SLA without you operating GPUs.

You'd run Whisper yourself when you need:

- Data residency / on-prem (HIPAA, banking, EU privacy).
- Long-form batch (podcasts, hours-long meetings) at low $/hour.
- Custom domain fine-tuning.
- No per-minute bill.

Side-by-side benchmark code is in `05_provider_comparison.md`.

### Deepgram streaming in 30 lines (you've used this — recap)

```python
# intermediate — Deepgram streaming via SDK
import asyncio, os, pyaudio
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

dg = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])

async def main():
    conn = dg.listen.asynclive.v("1")

    async def on_transcript(_, result, **__):
        alt = result.channel.alternatives[0]
        if result.is_final:
            print(f"FINAL: {alt.transcript}")
        else:
            print(f"  ... {alt.transcript}", end="\r")

    conn.on(LiveTranscriptionEvents.Transcript, on_transcript)

    await conn.start(LiveOptions(
        model="nova-3",
        language="en-US",
        encoding="linear16",
        sample_rate=16000,
        punctuate=True,
        smart_format=True,
        interim_results=True,
        endpointing=300,                     # ms of silence = utterance end
        vad_events=True,
        diarize=True,
    ))

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                    input=True, frames_per_buffer=8000)
    try:
        while True:
            await conn.send(stream.read(8000, exception_on_overflow=False))
    finally:
        await conn.finish()

asyncio.run(main())
```

---

## 2.7 Fine-tuning Whisper (when off-the-shelf isn't enough)

If you have domain audio with consistent vocabulary (medical, legal, accented
support calls), fine-tuning often beats throwing a bigger model at it.

```python
# advanced — fine-tune Whisper-small on your data
from datasets import Audio, load_dataset
from transformers import (WhisperFeatureExtractor, WhisperTokenizer,
                          WhisperForConditionalGeneration, Seq2SeqTrainer,
                          Seq2SeqTrainingArguments)

ds = load_dataset("json", data_files={"train": "train.jsonl",
                                       "val":   "val.jsonl"})
ds = ds.cast_column("audio", Audio(sampling_rate=16000))

fe  = WhisperFeatureExtractor.from_pretrained("openai/whisper-small")
tok = WhisperTokenizer.from_pretrained("openai/whisper-small",
                                       language="en", task="transcribe")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")

def prep(batch):
    audio = batch["audio"]
    batch["input_features"] = fe(audio["array"], sampling_rate=16000).input_features[0]
    batch["labels"] = tok(batch["text"]).input_ids
    return batch

ds = ds.map(prep, remove_columns=ds["train"].column_names, num_proc=4)

args = Seq2SeqTrainingArguments(
    output_dir="./whisper-domain",
    per_device_train_batch_size=16,
    learning_rate=1e-5,
    warmup_steps=500,
    max_steps=4000,
    gradient_checkpointing=True,
    fp16=True,
    evaluation_strategy="steps",
    eval_steps=500,
    save_steps=1000,
    predict_with_generate=True,
)

Seq2SeqTrainer(model=model, args=args,
               train_dataset=ds["train"], eval_dataset=ds["val"],
               tokenizer=fe).train()
```

Dataset format (jsonl):
```json
{"audio": "data/clip_00001.wav", "text": "patient reports chest pain since Monday"}
{"audio": "data/clip_00002.wav", "text": "BP one twenty over eighty, HR seventy two"}
```

Even 5–10 hours of in-domain audio measurably moves WER.

---

## 2.8 What to remember

- Streaming requires CTC / RNN-T or chunking around an encoder-decoder.
- Whisper is the strongest open-weight baseline; faster-whisper is the
  pragmatic deployment.
- Always enable VAD with Whisper to kill hallucinations on silence.
- For real-time voice agents, cloud streaming STT (Deepgram, AssemblyAI) wins
  on latency; local Whisper wins on $/hour and privacy.
- Word-level timestamps + diarization unlock most business value above raw
  transcripts.

Next → `03_tts_deep_dive.md`.
