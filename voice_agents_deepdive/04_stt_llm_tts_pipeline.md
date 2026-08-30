# 04 — STT → LLM → TTS Pipeline

The full conversational AI loop. This is where the engineering lives. Models
are commodities; the **orchestration** is the product.

---

## 4.1 The canonical voice-agent state machine

```
                  ┌─────────────────────────────────────┐
                  │           IDLE / LISTENING          │
                  └─────────────────────────────────────┘
                                    │ user speech detected (VAD)
                                    ▼
                  ┌─────────────────────────────────────┐
                  │            TRANSCRIBING             │ ◀────┐
                  │  partials stream to STT, UI updates │      │ more audio
                  └─────────────────────────────────────┘ ─────┘
                                    │ silence > endpointing_ms
                                    ▼
                  ┌─────────────────────────────────────┐
                  │            FINALIZING               │
                  │  STT emits final transcript          │
                  └─────────────────────────────────────┘
                                    │ final text
                                    ▼
                  ┌─────────────────────────────────────┐
                  │           THINKING (LLM)            │
                  │  stream tokens, parse tool calls    │
                  └─────────────────────────────────────┘
                                    │ first sentence
                                    ▼
                  ┌─────────────────────────────────────┐
                  │           SPEAKING (TTS)            │ ◀────┐
                  │  audio chunks → playback            │      │ more LLM
                  └─────────────────────────────────────┘ ─────┘
                            │                  │
                  user interrupts?         agent finished
                  (barge-in)                    │
                            │                  │
                            └─────────┬────────┘
                                      ▼
                                back to IDLE
```

Every voice agent (VAPI, Dograh, LiveKit, Pipecat, Vocode) implements some
flavor of this. Knowing each transition and its failure modes is what
separates "demo" from "production."

---

## 4.2 The minimum viable voice loop — single-file Python

This is the "hello world" of voice agents. ~100 lines, no framework.

```python
"""
mini_voice_agent.py — Deepgram STT  +  OpenAI LLM  +  ElevenLabs TTS
"""
# intermediate
import asyncio, os, json, base64, signal
import pyaudio, websockets
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
from openai import AsyncOpenAI

SAMPLE_RATE = 16_000
CHUNK       = 1600                                       # 100 ms frames

dg     = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
oai    = AsyncOpenAI()
EL_KEY = os.environ["ELEVEN_API_KEY"]
VOICE  = "JBFqnCBsd6RMkjVDRZzb"
EL_URI = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE}/stream-input"
          f"?model_id=eleven_turbo_v2_5&output_format=pcm_16000")

pa = pyaudio.PyAudio()
mic     = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                  input=True, frames_per_buffer=CHUNK)
speaker = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                  output=True)

history = [{"role": "system",
            "content": "You are a concise voice assistant. Answer in <2 sentences."}]
final_q: asyncio.Queue[str] = asyncio.Queue()


async def stt_task():
    """Mic → Deepgram → push final transcripts to a queue."""
    conn = dg.listen.asynclive.v("1")

    async def on_tx(_, result, **__):
        if result.is_final and result.channel.alternatives[0].transcript.strip():
            await final_q.put(result.channel.alternatives[0].transcript)

    conn.on(LiveTranscriptionEvents.Transcript, on_tx)
    await conn.start(LiveOptions(
        model="nova-3", language="en-US", encoding="linear16",
        sample_rate=SAMPLE_RATE, punctuate=True, smart_format=True,
        interim_results=True, endpointing=400,
    ))
    while True:
        await conn.send(mic.read(CHUNK, exception_on_overflow=False))


async def speak(text_stream):
    """Stream sentences from LLM into ElevenLabs WS, play audio."""
    async with websockets.connect(EL_URI) as ws:
        await ws.send(json.dumps({
            "text": " ",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
            "xi_api_key": EL_KEY,
        }))

        async def sender():
            async for piece in text_stream:
                await ws.send(json.dumps({"text": piece,
                                          "try_trigger_generation": True}))
            await ws.send(json.dumps({"text": ""}))

        send = asyncio.create_task(sender())
        try:
            async for msg in ws:
                data = json.loads(msg)
                if data.get("audio"):
                    speaker.write(base64.b64decode(data["audio"]))
                if data.get("isFinal"):
                    return
        finally:
            send.cancel()


async def think_and_speak(user_text: str):
    history.append({"role": "user", "content": user_text})
    print(f"USER: {user_text}")

    full = ""

    async def llm_stream():
        nonlocal full
        stream = await oai.chat.completions.create(
            model="gpt-4o-mini", messages=history, stream=True, temperature=0.4,
        )
        buffer = ""
        async for chunk in stream:
            tok = chunk.choices[0].delta.content or ""
            buffer += tok; full += tok
            # flush on sentence boundary for lower TTS latency
            if any(p in tok for p in ".!?"):
                yield buffer; buffer = ""
        if buffer:
            yield buffer

    await speak(llm_stream())
    history.append({"role": "assistant", "content": full})
    print(f"BOT : {full}")


async def main():
    stt = asyncio.create_task(stt_task())
    try:
        while True:
            text = await final_q.get()
            await think_and_speak(text)
    finally:
        stt.cancel()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)
    asyncio.run(main())
```

What this does well:
- True streaming end-to-end (no waiting for full LLM reply).
- Sentence-boundary flushing → TTS starts speaking by 600 ms.

What's still missing (covered in 07):
- Barge-in (user interrupts the agent mid-sentence).
- Endpointing tuning per user (faster talkers vs slower).
- Reconnect / error recovery.
- Tool calls / function calling.

---

## 4.3 Latency budget walkthrough — instrument every leg

```python
# advanced — wrap each stage with a timer; log to a single span tree
import time, contextvars
from contextlib import asynccontextmanager

_TURN = contextvars.ContextVar("turn", default={})

@asynccontextmanager
async def stage(name: str):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dur = (time.perf_counter() - t0) * 1000
        _TURN.get().setdefault("stages", []).append((name, dur))

def start_turn():
    _TURN.set({"t0": time.perf_counter(), "stages": []})

def end_turn():
    t = _TURN.get()
    total = (time.perf_counter() - t["t0"]) * 1000
    parts = "  ".join(f"{n}={d:.0f}ms" for n, d in t["stages"])
    print(f"TURN {total:.0f}ms  ::  {parts}")
```

Wrap the legs:

```python
async with stage("stt_final"):
    user_text = await final_q.get()
async with stage("llm_ttft"):
    stream = await oai.chat.completions.create(...)
async with stage("tts_ttfb"):
    first_audio = await anext(audio_stream)
```

Production target log line:

```
TURN 612ms  ::  stt_final=152ms  llm_ttft=287ms  tts_ttfb=141ms  playback=32ms
```

If any leg blows up, you know exactly where.

---

## 4.4 Barge-in (the hardest small problem)

When the agent is speaking and the user starts talking, you must:
1. Detect the user's voice while audio is playing back.
2. Stop the TTS playback **immediately**.
3. Cancel the LLM generation if still streaming.
4. Roll back any state that assumed the bot's reply was delivered.

```
[BOT TALKING] ────────────────────────────────────────────►
                                ▲
                                │ VAD says "speech detected" (high energy + neural)
                                │
   STOP TTS playback ◀──────────┤
   CANCEL LLM stream ◀──────────┤
   TRUNCATE assistant turn ◀────┘
   ──────────────────────────────►  [TRANSCRIBING USER]
```

Practical implementation tips:
- Use **acoustic echo cancellation** so the bot's own audio doesn't trigger VAD
  (WebRTC AEC, `speexdsp`, or LiveKit's built-in).
- Keep an `interrupt_event = asyncio.Event()` shared across STT/LLM/TTS tasks.
- On interrupt, append a synthetic message: `{"role":"assistant","content":<spoken so far>+" [interrupted]"}`. Otherwise the LLM thinks it said the whole reply.

```python
# advanced — barge-in skeleton
interrupt = asyncio.Event()

async def on_user_speech_start():
    interrupt.set()
    speaker_stream.stop()                # stop playback immediately
    if llm_task and not llm_task.done():
        llm_task.cancel()

async def tts_with_interrupt(stream):
    async for audio in stream:
        if interrupt.is_set():
            return
        speaker_stream.write(audio)
```

---

## 4.5 Framework choice — when to write it yourself vs use a stack

| Stack | What it is | Sweet spot |
|-------|------------|------------|
| **Raw asyncio + websockets** | This file's example | Custom needs, learning, max control |
| **LiveKit Agents** | Python framework, WebRTC pipeline | Telephony + browser, multi-user, mature |
| **Pipecat (Daily)** | Pipeline of "frame processors" | Modular voice agents, multimodal |
| **VAPI** (you used) | Hosted SaaS voice agent | Twilio integration, fastest demo |
| **Dograh** (you used) | Open-source workflow voice agent | Multi-step business calls |
| **Vocode** | Telephony-focused | Outbound dialer-style apps |
| **OpenAI Realtime API** | Single bidirectional WS, model handles STT+LLM+TTS | Lowest latency, lock-in |
| **Google Gemini Live** | Same, Google side | Gemini ecosystem |

The trend is **monolithic models** (OpenAI Realtime, Gemini Live, Moshi) that
skip the STT-LLM-TTS pipeline entirely — the model consumes audio and emits
audio. Lower latency, less customization.

### OpenAI Realtime API — the new shape of this problem

```
                        ┌──────────────────────────────┐
  mic audio  ──audio──▶ │                              │ ──audio──▶  speaker
                        │   gpt-4o-realtime over WS    │
  function call ◀─tool─ │  (handles STT+reasoning+TTS) │
                        └──────────────────────────────┘
```

```python
# intermediate — OpenAI Realtime API skeleton (audio in / audio out)
import asyncio, base64, json, os, websockets, pyaudio

URI = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
HDR = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
       "OpenAI-Beta": "realtime=v1"}

async def main():
    pa = pyaudio.PyAudio()
    mic     = pa.open(format=pyaudio.paInt16, channels=1, rate=24000,
                      input=True, frames_per_buffer=2400)
    speaker = pa.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)

    async with websockets.connect(URI, additional_headers=HDR) as ws:
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "voice": "shimmer",
                "input_audio_format":  "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {"type": "server_vad",
                                   "threshold": 0.5,
                                   "silence_duration_ms": 400},
                "instructions": "You are a friendly assistant. Reply briefly."
            }}))

        async def send_mic():
            while True:
                chunk = mic.read(2400, exception_on_overflow=False)
                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": base64.b64encode(chunk).decode(),
                }))

        async def recv_audio():
            async for msg in ws:
                ev = json.loads(msg)
                if ev["type"] == "response.audio.delta":
                    speaker.write(base64.b64decode(ev["delta"]))
                elif ev["type"] == "response.audio_transcript.delta":
                    print(ev["delta"], end="", flush=True)

        await asyncio.gather(send_mic(), recv_audio())

asyncio.run(main())
```

Notice: no Deepgram, no ElevenLabs, no PyAudio output buffering tricks.
Single connection. ~300 ms perceived latency end-to-end.

---

## 4.6 Tool calling inside a voice agent

The LLM emits a function call mid-conversation; you execute it, return result,
continue speaking.

```
USER:  "Book me a meeting with Sai tomorrow at 3"
       │
       ▼
LLM stream ─▶ tool_call: book_meeting(person="Sai", time="2026-05-29T15:00")
       │
       ▼
       [pause TTS — say "one moment..."]
       execute(book_meeting)  →  {"status":"booked","id":"M-123"}
       │
       ▼
LLM continues ─▶ "Got it. Meeting with Sai is booked for tomorrow at 3 PM."
       │
       ▼
       TTS streams the confirmation
```

Two latency-sensitive tricks:
- Say a filler phrase ("Let me check…", "One moment…") while the tool runs.
  Pre-render and cache these so the speaker is never silent > 500 ms.
- Pre-fetch likely follow-ups (calendar lookup, account info) on first
  utterance, before the LLM even asks.

---

## 4.7 Memory & context across turns

Voice conversations need:
- **Short-term**: the running `messages` list — keep ≤ 20 recent turns.
- **Long-term**: prior calls, user profile, account state. Pull from a DB,
  not the context window.
- **Working**: intermediate variables across tool calls (booking ID, captured
  email). Use a dict per session, not the chat history.

```python
# intermediate — session object skeleton
@dataclass
class Session:
    id: str
    user_id: str
    messages: list[dict] = field(default_factory=list)
    working:  dict       = field(default_factory=dict)   # mid-call scratchpad
    started_at: float    = field(default_factory=time.time)

    def trim(self, max_turns: int = 20):
        # always keep system + last N turns
        sys = [m for m in self.messages if m["role"] == "system"]
        rest = [m for m in self.messages if m["role"] != "system"][-max_turns*2:]
        self.messages = sys + rest
```

---

## 4.8 What to remember

- The state machine is universal. Every framework implements it.
- Stream LLM into TTS sentence-by-sentence — never wait for the full reply.
- Always instrument leg latencies; debug with the budget breakdown.
- Barge-in is non-negotiable for production; design for it from turn 1.
- Realtime API skips the pipeline at the cost of flexibility — know both shapes.

Next → `05_provider_comparison.md`.
