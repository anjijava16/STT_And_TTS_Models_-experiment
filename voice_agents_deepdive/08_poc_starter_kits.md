# 08 — POC Starter Kits

Three complete, copy-pasteable mini-projects with explicit setup steps,
`requirements.txt`, and a clear path to extension. Each one is < 250 lines.

---

## Kit A — Offline transcription CLI (Whisper + diarization)

**Goal**: drop in any `.mp3` / `.mp4` / `.wav`, get back a Markdown
transcript with speakers, timestamps, and a 3-sentence summary.

**Stack**: faster-whisper + pyannote + Claude (or OpenAI) + ffmpeg.
**Cost**: $0 (Whisper local). Claude pay-per-summary.
**Hardware**: 8 GB RAM CPU works (slow). 8 GB+ GPU recommended.

### Files

```
kit_a_offline_transcribe/
├── requirements.txt
├── transcribe.py
└── README.md
```

### `requirements.txt`

```
faster-whisper>=1.0.3
pyannote.audio>=3.3.1
anthropic>=0.40.0
typer>=0.12.0
rich>=13.7.0
```

### `transcribe.py`

```python
"""
Usage:
    export HF_TOKEN=...           # huggingface token w/ pyannote access
    export ANTHROPIC_API_KEY=...
    python transcribe.py path/to/audio.mp3 --device cuda
"""
import json, os, subprocess, tempfile
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import track
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
import anthropic

cli = typer.Typer(no_args_is_help=True)
con = Console()

def to_wav(src: Path, sr: int = 16000) -> Path:
    out = Path(tempfile.gettempdir()) / f"{src.stem}.wav"
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", str(src), "-ac", "1", "-ar", str(sr), str(out)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return out

def transcribe(wav: Path, model: str, device: str) -> list[dict]:
    m = WhisperModel(model, device=device, compute_type="float16" if device=="cuda" else "int8")
    segs, info = m.transcribe(str(wav), word_timestamps=True, vad_filter=True,
                              beam_size=5, condition_on_previous_text=False)
    con.print(f"[dim]language: {info.language} ({info.language_probability:.2f})")
    return [{"start": s.start, "end": s.end, "text": s.text.strip()}
            for s in segs if s.text.strip()]

def diarize(wav: Path) -> list[tuple[float, float, str]]:
    pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                                    use_auth_token=os.environ["HF_TOKEN"])
    diar = pipe(str(wav))
    return [(t.start, t.end, lbl) for t, _, lbl in diar.itertracks(yield_label=True)]

def speaker_at(turns, t):
    for s, e, lbl in turns:
        if s <= t <= e: return lbl
    return "S?"

def render_md(segments, turns) -> str:
    lines = ["# Transcript\n"]
    last_spk = None
    for seg in segments:
        spk = speaker_at(turns, (seg["start"] + seg["end"]) / 2)
        if spk != last_spk:
            lines.append(f"\n**{spk}** [{seg['start']:.1f}s]")
            last_spk = spk
        lines.append(f"> {seg['text']}")
    return "\n".join(lines)

def summarize(transcript: str) -> str:
    c = anthropic.Anthropic()
    r = c.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content":
            f"Summarize this transcript in 3 sentences, then list "
            f"action items as bullets. Transcript:\n\n{transcript[:60000]}"}])
    return r.content[0].text

@cli.command()
def run(src: Path, model: str = "large-v3-turbo", device: str = "cuda",
        out: Path = Path("transcript.md")):
    con.rule(f"[bold]Processing {src.name}")

    wav = to_wav(src)
    con.print("[green]✓[/] converted to 16 kHz mono WAV")

    segs = transcribe(wav, model, device)
    con.print(f"[green]✓[/] transcribed {len(segs)} segments")

    turns = diarize(wav)
    speakers = {lbl for _, _, lbl in turns}
    con.print(f"[green]✓[/] diarized — {len(speakers)} speaker(s): {speakers}")

    md = render_md(segs, turns)
    summary = summarize("\n".join(s["text"] for s in segs))
    out.write_text(md + "\n\n---\n\n# Summary\n\n" + summary)

    con.print(f"[bold green]done → {out}")

if __name__ == "__main__":
    cli()
```

### Extend it
- Swap `claude-haiku-4-5` for GPT-4o if you don't have an Anthropic key.
- Pipe `transcribe()` into `vtt` / `srt` builders for caption export.
- Add `--language` flag to force STT language.
- Wrap in FastAPI to expose as `/transcribe` POST.

---

## Kit B — Real-time voice agent over WebSocket (browser ↔ agent)

**Goal**: open a browser, click "talk," speak, hear the agent reply with
sub-700-ms latency.

**Stack**: FastAPI + Deepgram STT + GPT-4o-mini + ElevenLabs TTS.
**Browser**: plain `getUserMedia` + `AudioWorklet` + `WebSocket`.

### Files

```
kit_b_realtime_agent/
├── requirements.txt
├── server.py
└── static/
    ├── index.html
    └── client.js
```

### `requirements.txt`

```
fastapi>=0.115
uvicorn[standard]>=0.30
deepgram-sdk>=3.7
openai>=1.50
websockets>=12
python-dotenv>=1.0
```

### `server.py`

```python
import asyncio, base64, json, os
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
from openai import AsyncOpenAI
import websockets

load_dotenv()
app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

dg     = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
oai    = AsyncOpenAI()
EL_KEY = os.environ["ELEVEN_API_KEY"]
VOICE  = "JBFqnCBsd6RMkjVDRZzb"
EL_URI = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE}/stream-input"
          f"?model_id=eleven_turbo_v2_5&output_format=pcm_16000")
SYSTEM = "You are a brisk voice assistant. Answer in at most two sentences."

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    history = [{"role": "system", "content": SYSTEM}]
    user_finals: asyncio.Queue[str] = asyncio.Queue()
    interrupt = asyncio.Event()

    # ─── STT ───────────────────────────────────────────────────────────
    dg_conn = dg.listen.asynclive.v("1")
    async def on_tx(_, result, **__):
        alt = result.channel.alternatives[0]
        if result.is_final and alt.transcript.strip():
            await user_finals.put(alt.transcript)
        if result.speech_final:
            await ws.send_json({"type": "user_done"})
        elif alt.transcript:
            await ws.send_json({"type": "partial", "text": alt.transcript})

    async def on_speech_started(_, **__):
        interrupt.set()                              # barge-in
        await ws.send_json({"type": "interrupt"})

    dg_conn.on(LiveTranscriptionEvents.Transcript, on_tx)
    dg_conn.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
    await dg_conn.start(LiveOptions(
        model="nova-3", language="en-US", encoding="linear16",
        sample_rate=16000, punctuate=True, smart_format=True,
        interim_results=True, endpointing=400, vad_events=True,
    ))

    # ─── TTS ───────────────────────────────────────────────────────────
    async def speak(text_iter):
        interrupt.clear()
        async with websockets.connect(EL_URI) as el:
            await el.send(json.dumps({"text": " ",
                                      "xi_api_key": EL_KEY,
                                      "voice_settings": {"stability": 0.5,
                                                         "similarity_boost": 0.8}}))
            async def feed():
                async for piece in text_iter:
                    if interrupt.is_set(): return
                    await el.send(json.dumps({"text": piece,
                                              "try_trigger_generation": True}))
                await el.send(json.dumps({"text": ""}))

            send = asyncio.create_task(feed())
            try:
                async for msg in el:
                    if interrupt.is_set(): break
                    d = json.loads(msg)
                    if d.get("audio"):
                        await ws.send_json({"type": "audio", "data": d["audio"]})
                    if d.get("isFinal"): break
            finally:
                send.cancel()

    # ─── Turn loop ─────────────────────────────────────────────────────
    async def think():
        while True:
            user_text = await user_finals.get()
            history.append({"role": "user", "content": user_text})
            full = ""

            async def llm():
                nonlocal full
                stream = await oai.chat.completions.create(
                    model="gpt-4o-mini", messages=history, stream=True,
                    temperature=0.4)
                buf = ""
                async for chunk in stream:
                    if interrupt.is_set(): return
                    tok = chunk.choices[0].delta.content or ""
                    buf += tok; full += tok
                    if any(p in tok for p in ".!?"):
                        yield buf; buf = ""
                if buf: yield buf

            await speak(llm())
            history.append({"role": "assistant", "content": full})

    think_task = asyncio.create_task(think())

    try:
        async for raw in ws.iter_text():
            ev = json.loads(raw)
            if ev["type"] == "audio":
                pcm = base64.b64decode(ev["data"])
                await dg_conn.send(pcm)
    finally:
        think_task.cancel()
        await dg_conn.finish()
```

### `static/index.html`

```html
<!doctype html>
<meta charset="utf-8">
<title>Voice Agent</title>
<style>
  body { font: 16px system-ui; margin: 2em; max-width: 640px; }
  #log { white-space: pre-wrap; padding: 1em; background: #f4f4f4; border-radius: 8px; min-height: 8em; }
  button { padding: .7em 1.5em; font-size: 1em; }
</style>
<button id="start">🎙 Start talking</button>
<div id="log"></div>
<script src="client.js"></script>
```

### `static/client.js`

```javascript
const log = document.getElementById("log");
const btn = document.getElementById("start");
let ws, ctx, mic, worklet, playQueue = [], playing = false;

btn.onclick = async () => {
  ws = new WebSocket((location.protocol === "https:" ? "wss" : "ws") + "://" + location.host + "/ws");
  ws.binaryType = "arraybuffer";

  ws.onmessage = async (ev) => {
    const m = JSON.parse(ev.data);
    if (m.type === "partial")     log.textContent = "you: " + m.text;
    if (m.type === "user_done")   log.textContent += "\n";
    if (m.type === "interrupt")   { playQueue = []; playing = false; }
    if (m.type === "audio") {
      const pcm = Uint8Array.from(atob(m.data), c => c.charCodeAt(0));
      playQueue.push(pcm);
      if (!playing) playLoop();
    }
  };

  ctx = new AudioContext({ sampleRate: 16000 });
  await ctx.audioWorklet.addModule(URL.createObjectURL(new Blob([`
    class CaptureProcessor extends AudioWorkletProcessor {
      process(inputs) {
        const ch = inputs[0][0]; if (!ch) return true;
        const i16 = new Int16Array(ch.length);
        for (let i = 0; i < ch.length; i++)
          i16[i] = Math.max(-1, Math.min(1, ch[i])) * 0x7fff;
        this.port.postMessage(i16.buffer, [i16.buffer]);
        return true;
      }
    }
    registerProcessor('cap', CaptureProcessor);
  `], { type: "text/javascript" })));

  const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
  mic = ctx.createMediaStreamSource(stream);
  worklet = new AudioWorkletNode(ctx, "cap");
  worklet.port.onmessage = (e) => {
    const b64 = btoa(String.fromCharCode(...new Uint8Array(e.data)));
    ws.readyState === 1 && ws.send(JSON.stringify({ type: "audio", data: b64 }));
  };
  mic.connect(worklet);
  btn.disabled = true; btn.textContent = "🔴 Listening...";
};

async function playLoop() {
  playing = true;
  while (playQueue.length) {
    const pcm = playQueue.shift();
    const view = new DataView(pcm.buffer);
    const f32 = new Float32Array(pcm.length / 2);
    for (let i = 0; i < f32.length; i++)
      f32[i] = view.getInt16(i*2, true) / 0x7fff;
    const buf = ctx.createBuffer(1, f32.length, 16000);
    buf.copyToChannel(f32, 0);
    const src = ctx.createBufferSource();
    src.buffer = buf; src.connect(ctx.destination);
    await new Promise(res => { src.onended = res; src.start(); });
  }
  playing = false;
}
```

### Run

```bash
pip install -r requirements.txt
echo "DEEPGRAM_API_KEY=..." > .env
echo "OPENAI_API_KEY=..." >> .env
echo "ELEVEN_API_KEY=..." >> .env
uvicorn server:app --reload --port 8000
# open http://localhost:8000
```

### Extend
- Add a system-prompt selector to the UI.
- Persist sessions to SQLite for resumable conversations.
- Swap ElevenLabs for Cartesia by changing `EL_URI` and SDK calls.
- Add tool calling for a real use case (calendar, CRM).

---

## Kit C — Fully local voice agent (privacy / no-cloud)

**Goal**: same UX as Kit B, but nothing leaves your laptop. For HIPAA POCs,
on-prem demos, robotics, kiosks.

**Stack**: faster-whisper + Ollama (Llama 3.1 / Qwen 2.5) + Piper TTS.

### `requirements.txt`

```
faster-whisper>=1.0.3
sounddevice>=0.4.7
silero-vad>=5.1
piper-tts>=1.2.0
ollama>=0.4
numpy>=1.26
```

### `local_agent.py`

```python
"""
Local voice loop: mic → Whisper → Ollama → Piper → speaker.
Run Ollama in another terminal: `ollama serve` then `ollama pull llama3.1`.
"""
import asyncio, queue, time, wave, io
import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel
from piper import PiperVoice
import ollama

SR = 16000
FRAME = 512                                     # 32 ms @ 16 kHz
SILENCE_HANGOVER_MS = 600

# ── Models ────────────────────────────────────────────────────────────
print("loading models...")
stt = WhisperModel("small.en", device="cpu", compute_type="int8")
vad_model, utils = torch.hub.load("snakers4/silero-vad", "silero_vad", trust_repo=True)
piper = PiperVoice.load("en_US-amy-medium.onnx")

# ── State ─────────────────────────────────────────────────────────────
mic_q: queue.Queue = queue.Queue()
history = [{"role": "system",
            "content": "You are a concise local assistant. Answer in one sentence."}]

def mic_cb(indata, frames, t, status):
    mic_q.put(indata.copy())

def is_speech(frame: np.ndarray) -> bool:
    tens = torch.from_numpy(frame.astype(np.float32)).unsqueeze(0)
    return vad_model(tens, SR).item() > 0.5

# ── Capture one utterance (VAD-gated) ─────────────────────────────────
def capture():
    buf, in_speech, silence_ms = [], False, 0
    while True:
        chunk = mic_q.get().flatten()
        speech = is_speech(chunk)
        if speech:
            in_speech, silence_ms = True, 0
            buf.append(chunk)
        elif in_speech:
            silence_ms += len(chunk) / SR * 1000
            buf.append(chunk)
            if silence_ms > SILENCE_HANGOVER_MS:
                return np.concatenate(buf)

def transcribe(audio):
    segs, _ = stt.transcribe(audio, beam_size=1, vad_filter=False)
    return " ".join(s.text for s in segs).strip()

def llm(user_text):
    history.append({"role": "user", "content": user_text})
    out = ""
    for chunk in ollama.chat(model="llama3.1", messages=history, stream=True):
        tok = chunk["message"]["content"]
        out += tok
        print(tok, end="", flush=True)
        yield tok
    print()
    history.append({"role": "assistant", "content": out})

def speak(text):
    pcm = io.BytesIO()
    with wave.open(pcm, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(piper.config.sample_rate)
        piper.synthesize(text, wf)
    pcm.seek(0)
    import soundfile as sf
    audio, sr = sf.read(pcm); sd.play(audio, sr); sd.wait()

def main():
    print("listening. Ctrl-C to quit.")
    with sd.InputStream(samplerate=SR, channels=1, dtype="float32",
                        blocksize=FRAME, callback=mic_cb):
        while True:
            audio = capture()
            user_text = transcribe(audio)
            if not user_text: continue
            print(f"\nUSER: {user_text}")
            sentence = ""
            for tok in llm(user_text):
                sentence += tok
                if any(p in tok for p in ".!?"):
                    speak(sentence); sentence = ""
            if sentence.strip(): speak(sentence)

if __name__ == "__main__":
    main()
```

### Run

```bash
pip install -r requirements.txt
ollama serve &
ollama pull llama3.1
# download a Piper voice .onnx + .json from https://github.com/rhasspy/piper
python local_agent.py
```

### Limitations
- No barge-in (single-threaded VAD/playback loop). Adding it = move playback
  to its own thread + share an interrupt flag.
- Whisper isn't streaming — utterance must complete before transcription.
  Acceptable for ~2 s utterances; not great for long monologues.

### Extend
- Add a wake word ("hey assistant") via `openWakeWord` to gate the VAD loop.
- Swap Llama for Phi-3.5 or Qwen 2.5 for lower latency.
- Use Kokoro-82M instead of Piper for more natural prosody.
- Run on a Raspberry Pi 5 — works with `tiny.en` + `phi-3.5-mini` + Piper.

---

## What to build next, in order

1. **Kit A** — single file, no live audio, builds confidence with the
   transcription pipeline.
2. **Kit B** — your first real voice agent end-to-end. Iterate by swapping
   providers using `05_provider_comparison.md`.
3. **Kit C** — once you understand the cloud pipeline, build the local
   equivalent. Cements your understanding of every layer.
4. Pick one **Business POC** from `06_business_use_cases.md` and ship it.
   Pick by the *user* (do you actually have one?), not by the tech.

That's the path from zero to hero. The rest is reps.
