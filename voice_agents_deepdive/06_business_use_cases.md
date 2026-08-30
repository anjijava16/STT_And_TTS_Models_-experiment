# 06 — Business POCs with Python

Ten real, monetizable use cases. Each one has: a flow diagram, the stack
choice, and a runnable Python skeleton you can extend.

---

## Index

1. [Inbound customer-support voice agent](#1-inbound-customer-support-voice-agent)
2. [Outbound appointment-reminder dialer](#2-outbound-appointment-reminder-dialer)
3. [Meeting recorder → summary + action items](#3-meeting-recorder--summary--action-items)
4. [Call center QA & compliance scoring](#4-call-center-qa--compliance-scoring)
5. [Real-time meeting translator](#5-real-time-meeting-translator)
6. [Voice-first IVR with intent routing](#6-voice-first-ivr-with-intent-routing)
7. [Voice clone for personalized outreach](#7-voice-clone-for-personalized-outreach)
8. [Sales-call coach (post-call analysis)](#8-sales-call-coach-post-call-analysis)
9. [Voice-enabled RAG over internal docs](#9-voice-enabled-rag-over-internal-docs)
10. [Multilingual voice support (Indic languages)](#10-multilingual-voice-support-indic-languages)

---

## 1. Inbound customer-support voice agent

**Value**: 24/7 first-line support, deflects 30–60 % of tier-1 tickets.

```
Customer phone ──Twilio──▶  WebSocket  ──▶  ┌──────────────┐
                                            │  Voice Agent │
                                            │ Deepgram STT │
                                            │ GPT-4o LLM   │
                                            │ Eleven TTS   │
                                            └──────┬───────┘
                                                   │
                              ┌────────────────────┼──────────────────┐
                              ▼                    ▼                  ▼
                       Order lookup           CRM update         Escalate to
                       (PostgreSQL)           (HubSpot API)      human agent
                                                                 (warm transfer)
```

**Stack**: Twilio + Deepgram + GPT-4o-mini + ElevenLabs Turbo, FastAPI server.

```python
# intermediate — Twilio Media Streams → Deepgram → OpenAI → ElevenLabs
# fastapi twilio_voice_agent.py
import asyncio, base64, json, os
import audioop
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
from openai import AsyncOpenAI
import websockets

app = FastAPI()
dg = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])
oai = AsyncOpenAI()

SYSTEM = ("You are Acme Co's support agent. Greet briefly. Ask one question "
          "at a time. If user asks about an order, call get_order tool. "
          "Keep replies under 2 sentences.")

@app.post("/twiml")
def twiml(request):                                  # Twilio webhook
    return Response("""<Response><Connect><Stream url="wss://your-host/media"/></Connect></Response>""",
                    media_type="application/xml")

@app.websocket("/media")
async def media(ws: WebSocket):
    await ws.accept()
    stream_sid = None
    history = [{"role": "system", "content": SYSTEM}]
    final_q: asyncio.Queue[str] = asyncio.Queue()

    # ---- Deepgram setup (8 kHz μ-law from Twilio)
    conn = dg.listen.asynclive.v("1")
    async def on_tx(_, result, **__):
        if result.is_final:
            t = result.channel.alternatives[0].transcript.strip()
            if t: await final_q.put(t)
    conn.on(LiveTranscriptionEvents.Transcript, on_tx)
    await conn.start(LiveOptions(
        model="nova-3", language="en-US",
        encoding="mulaw", sample_rate=8000,
        punctuate=True, smart_format=True, interim_results=True,
        endpointing=400,
    ))

    async def send_audio_to_twilio(pcm_8k: bytes):
        # PCM16 8k → mulaw 8k → b64 → Twilio media frame
        mu = audioop.lin2ulaw(pcm_8k, 2)
        await ws.send_text(json.dumps({
            "event": "media",
            "streamSid": stream_sid,
            "media": {"payload": base64.b64encode(mu).decode()},
        }))

    async def speak(text):
        # ElevenLabs WS → PCM 8k → Twilio
        VOICE = "JBFqnCBsd6RMkjVDRZzb"
        URI = (f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE}/stream-input"
               f"?model_id=eleven_turbo_v2_5&output_format=pcm_8000")
        async with websockets.connect(URI) as el:
            await el.send(json.dumps({"text": " ",
                                      "xi_api_key": os.environ["ELEVEN_API_KEY"]}))
            await el.send(json.dumps({"text": text, "try_trigger_generation": True}))
            await el.send(json.dumps({"text": ""}))
            async for msg in el:
                d = json.loads(msg)
                if d.get("audio"):
                    await send_audio_to_twilio(base64.b64decode(d["audio"]))
                if d.get("isFinal"): return

    async def think():
        while True:
            user_text = await final_q.get()
            history.append({"role": "user", "content": user_text})
            r = await oai.chat.completions.create(
                model="gpt-4o-mini", messages=history, temperature=0.4)
            reply = r.choices[0].message.content
            history.append({"role": "assistant", "content": reply})
            await speak(reply)

    think_task = asyncio.create_task(think())

    try:
        # Greet first
        await speak("Hi, you've reached Acme support. How can I help?")
        async for raw in ws.iter_text():
            ev = json.loads(raw)
            if ev["event"] == "start":
                stream_sid = ev["start"]["streamSid"]
            elif ev["event"] == "media":
                pcm_mu = base64.b64decode(ev["media"]["payload"])
                await conn.send(pcm_mu)                     # μ-law direct
            elif ev["event"] == "stop":
                break
    finally:
        think_task.cancel()
        await conn.finish()
```

Wire `/twiml` to your Twilio number. Done.

---

## 2. Outbound appointment-reminder dialer

**Value**: medical/dental practice cuts no-shows ~30 %.

```
CRON ──┐
       │   ┌────────────────────────────┐
       └──▶│ Worker pulls "due reminders"│
           └────────┬───────────────────┘
                    │ for each appt
                    ▼
        ┌────────────────────────────┐
        │ Twilio.calls.create()      │
        │   url=https://.../twiml    │
        └────────┬───────────────────┘
                 ▼
        Voice agent confirms / reschedules / records DTMF
                 │
                 ▼
        Webhook → DB update appt.status
```

```python
# intermediate — schedule outbound calls
from twilio.rest import Client
from sqlalchemy import select
import datetime as dt

tw = Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"])

def run_reminder_batch():
    soon = dt.datetime.utcnow() + dt.timedelta(hours=24)
    with Session() as s:
        rows = s.execute(select(Appointment).where(
            Appointment.starts_at < soon,
            Appointment.reminded == False)).scalars().all()
        for appt in rows:
            tw.calls.create(
                to=appt.patient.phone,
                from_=TWILIO_NUMBER,
                url=f"https://your-host/twiml?appt_id={appt.id}",
                status_callback="https://your-host/twilio_status",
                status_callback_event=["completed"],
            )
            appt.reminded = True
        s.commit()
```

The TwiML endpoint loads patient + appointment, opens a `<Stream>` to the
same voice-agent server from POC #1, but with a personalized system prompt.

---

## 3. Meeting recorder → summary + action items

**Value**: 5 min of human work per meeting saved × every meeting.

```
.mp4 / .wav input
        │
        ▼
┌───────────────────┐
│ ffmpeg → 16k mono │
└────────┬──────────┘
         ▼
┌───────────────────┐    ┌───────────────────┐
│ pyannote diarize  │ ──▶│ faster-whisper    │
│ (who & when)      │    │ word timestamps   │
└────────┬──────────┘    └────────┬──────────┘
         └──────────┬───────────────┘
                    ▼ merged transcript w/ speakers
         ┌───────────────────┐
         │  Claude / GPT-4   │
         │  - summary        │
         │  - decisions      │
         │  - action items   │
         │  - sentiment      │
         └────────┬──────────┘
                  ▼
         JSON to Notion/Slack
```

```python
# advanced — full meeting pipeline
import subprocess, json, os
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from openai import OpenAI

def to_wav(src: str, dst: str = "meeting.wav"):
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", "16000", dst],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dst

def transcribe(wav):
    m = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
    segs, _ = m.transcribe(wav, word_timestamps=True, vad_filter=True)
    return [{"start": s.start, "end": s.end, "text": s.text,
             "words": [{"w": w.word, "s": w.start, "e": w.end} for w in s.words]}
            for s in segs]

def diarize(wav):
    diar = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                                    use_auth_token=os.environ["HF_TOKEN"])(wav)
    return [(t.start, t.end, lbl) for t, _, lbl in diar.itertracks(yield_label=True)]

def speaker_at(turns, t):
    for s, e, lbl in turns:
        if s <= t <= e: return lbl
    return "UNK"

def assemble(segments, turns):
    out = []
    for seg in segments:
        spk = speaker_at(turns, (seg["start"] + seg["end"]) / 2)
        out.append(f"[{seg['start']:.1f}] {spk}: {seg['text'].strip()}")
    return "\n".join(out)

def summarize(transcript: str) -> dict:
    cli = OpenAI()
    r = cli.chat.completions.create(
        model="gpt-4o", response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content":
              "You produce meeting notes as strict JSON with keys: "
              "summary (3 sentences), decisions (list), action_items "
              "(list of {who, what, due}), sentiment (1-5)."},
            {"role": "user", "content": transcript[:120_000]},
        ])
    return json.loads(r.choices[0].message.content)

def run(src_path):
    wav = to_wav(src_path)
    transcript = assemble(transcribe(wav), diarize(wav))
    notes = summarize(transcript)
    print(json.dumps(notes, indent=2))
    return transcript, notes
```

---

## 4. Call center QA & compliance scoring

**Value**: replace manual call audits ($30/call) with automated scoring.

```
Call recording ──▶ STT + diarize ──▶  ┌─────────────────────┐
                                      │  LLM grader         │
                                      │  - disclosed name?  │ ──▶  Score 0-100
                                      │  - mini-Miranda?    │
                                      │  - did NOT promise? │
                                      │  - empathy phrase?  │
                                      └─────────────────────┘
                                                ▼
                                      Flag for review if < 70
```

Compliance rubric is the prompt. Each rule maps to a JSON field. Auditors
spot-check the LLM scoring on 1 % of flagged calls.

```python
# intermediate — score a call against a rubric
RUBRIC = """
Score the AGENT against these rules. 0 = absent, 1 = present.
- disclosed_name (agent stated their name in first 20s)
- disclosed_recording (agent mentioned the call is recorded)
- empathy_used (agent acknowledged customer emotion when complaint raised)
- avoided_promises (agent did NOT promise specific outcomes/dates)
- offered_supervisor (if customer angry, offered escalation)
Return strict JSON.
"""

def score(transcript_with_speakers: str) -> dict:
    r = OpenAI().chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": transcript_with_speakers},
        ])
    return json.loads(r.choices[0].message.content)
```

---

## 5. Real-time meeting translator

**Value**: cross-border meetings with sub-second translation.

```
Speaker A (Hindi) ──▶ Whisper (translate task) ──▶ English text
                                                       │
                                                       ▼
                                                ElevenLabs voice
                                                (Spanish)         ──▶ Speaker B
```

Whisper `task="translate"` always emits English. To go to other languages,
chain: Whisper transcribe → GPT translate → TTS in target lang.

```python
# advanced — live translation tap on a mic
import asyncio, queue
from faster_whisper import WhisperModel
import sounddevice as sd
from openai import OpenAI

m = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
oai = OpenAI()
audio_q: queue.Queue = queue.Queue()

def callback(indata, frames, time_, status):
    audio_q.put(indata.copy())

def translate(text, target="es"):
    return oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system",
                   "content": f"Translate to {target}. Reply with translation only."},
                  {"role": "user", "content": text}]
    ).choices[0].message.content

with sd.InputStream(samplerate=16000, channels=1, dtype="float32",
                    blocksize=16000, callback=callback):
    buf = []
    while True:
        buf.append(audio_q.get().flatten())
        if len(buf) >= 5:                                   # ~5 s
            import numpy as np
            audio = np.concatenate(buf); buf = []
            segs, info = m.transcribe(audio, language="hi", task="transcribe",
                                      vad_filter=True, beam_size=1)
            src = " ".join(s.text for s in segs).strip()
            if src:
                print(f"HI: {src}")
                print(f"ES: {translate(src, 'es')}")
```

---

## 6. Voice-first IVR with intent routing

**Value**: replace press-1-for-X with natural language; route to right team.

```
"I need help with billing"   ──▶ STT ──▶ ┌─────────────────────┐
                                         │ Intent classifier   │
                                         │ (LLM or fine-tuned) │
                                         └──────┬──────────────┘
                                                ▼
                          ┌───────────┬─────────┴────────┬───────────┐
                          ▼           ▼                  ▼           ▼
                      Billing     Tech Support      Sales        Fallback
                      queue       queue             queue        agent
```

Use embeddings or an LLM with a closed enum:

```python
# beginner — intent classification
INTENTS = ["billing", "tech_support", "sales", "cancel", "other"]

def classify(text: str) -> str:
    r = OpenAI().chat.completions.create(
        model="gpt-4o-mini", temperature=0,
        messages=[{"role": "system",
                   "content": f"Reply ONLY with one of: {INTENTS}"},
                  {"role": "user", "content": text}])
    out = r.choices[0].message.content.strip().lower()
    return out if out in INTENTS else "other"
```

Then `<Dial>` to the corresponding Twilio queue.

---

## 7. Voice clone for personalized outreach

**Value**: sales team sends 1000 personalized voice messages in their own voice.

```
Sales rep records 60s sample (one-time)
        │
        ▼
ElevenLabs voice add → voice_id stored per rep
        │
   For each prospect:
        ▼
Template + variables ──▶ ElevenLabs TTS (voice_id, message_text) ──▶ mp3
        │
        ▼
WhatsApp / email / call back URL
```

```python
# intermediate — personalized voice mp3 per lead
from elevenlabs.client import ElevenLabs
el = ElevenLabs(api_key=os.environ["ELEVEN_API_KEY"])

TEMPLATE = ("Hey {name}, this is {rep} from Acme. I saw {company} is hiring "
            "engineers — wanted to share how we cut onboarding by half. "
            "Mind a 15-minute chat?")

def render(lead, rep):
    text = TEMPLATE.format(**lead, rep=rep.name)
    audio = el.text_to_speech.convert(
        voice_id=rep.voice_id, model_id="eleven_turbo_v2_5",
        text=text, output_format="mp3_44100_128")
    with open(f"out/{lead['id']}.mp3", "wb") as f:
        for c in audio: f.write(c)
```

> **Ethics**: must obtain consent from the rep being cloned. Disclose
> AI-generated voice if jurisdiction (EU AI Act, CA SB-1001) requires it.

---

## 8. Sales-call coach (post-call analysis)

**Value**: rep gets feedback within 5 min of hanging up.

```
Recording → STT+diarize → ┌────────────────────────────┐
                          │ Metrics                    │
                          │  - talk:listen ratio       │
                          │  - longest monologue       │
                          │  - filler word count       │
                          │  - questions asked         │
                          │  - objections handled      │
                          └────────────────────────────┘
                                       ▼
                          LLM coach: "Next time, ask
                          discovery questions earlier."
```

```python
# intermediate — talk:listen ratio + filler counts
import re
FILLERS = re.compile(r"\b(um|uh|like|you know|basically|sort of)\b", re.I)

def metrics(segments_with_speaker):
    times = {"rep": 0.0, "prospect": 0.0}
    fillers = 0; questions = 0
    for seg in segments_with_speaker:
        times[seg["speaker"]] += seg["end"] - seg["start"]
        if seg["speaker"] == "rep":
            fillers += len(FILLERS.findall(seg["text"]))
            questions += seg["text"].count("?")
    return {
        "talk_listen": times["rep"] / max(times["prospect"], 0.01),
        "fillers":     fillers,
        "questions":   questions,
    }
```

---

## 9. Voice-enabled RAG over internal docs

**Value**: field tech says "what's the torque spec for the X-200?" — gets it.

```
"What's the torque spec for the X-200?"
        │
        ▼ STT
"What's the torque spec for the X-200?"
        │
        ▼ embed → search Pinecone/pgvector
[doc chunks about X-200]
        │
        ▼ LLM with context
"The X-200 fastener torque spec is 25 Nm dry."
        │
        ▼ TTS
🔊 to tech's earpiece
```

```python
# intermediate — voice → RAG → voice (skeleton)
from openai import OpenAI
import pgvector  # via psycopg

oai = OpenAI()

def retrieve(query, k=5):
    emb = oai.embeddings.create(model="text-embedding-3-small",
                                input=query).data[0].embedding
    return db.query("SELECT chunk FROM docs ORDER BY embedding <-> %s LIMIT %s",
                    (emb, k))

def answer(query):
    ctx = "\n\n".join(retrieve(query))
    r = oai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system",
                   "content": "Answer ONLY from CONTEXT. If unknown, say so."},
                  {"role": "user", "content": f"CONTEXT:\n{ctx}\n\nQ: {query}"}])
    return r.choices[0].message.content
```

Plug into the mini voice agent from `04_stt_llm_tts_pipeline.md` — replace
the LLM call with `answer(user_text)`.

---

## 10. Multilingual voice support (Indic languages)

**Value**: serve Tier-2/3 customers in their language at scale.

```
Customer speaks Telugu ──▶ Sarvam / Google Chirp 2 STT
                                   │
                                   ▼
                          GPT-4o (multilingual)
                                   │
                                   ▼
                          ElevenLabs Multilingual v2 / Sarvam TTS
                                   │
                                   ▼
                          Telugu reply back to customer
```

Two practical notes:
- **Code-switching**: real Indian users mix Hindi + English mid-sentence.
  Whisper handles this OK; Sarvam handles it natively. Always test on
  code-switched samples, not isolated language samples.
- **Tokenization in LLM**: Indic scripts use more tokens per word. Budget
  bigger context.

```python
# advanced — Sarvam STT + GPT-4o + Sarvam TTS (Telugu loop sketch)
import requests, os, base64

SARVAM = "https://api.sarvam.ai"
HDR = {"api-subscription-key": os.environ["SARVAM_KEY"]}

def stt(wav_bytes):
    r = requests.post(f"{SARVAM}/speech-to-text",
                      headers=HDR,
                      files={"file": ("a.wav", wav_bytes, "audio/wav")},
                      data={"language_code": "te-IN", "model": "saarika:v2"})
    return r.json()["transcript"]

def tts(text, lang="te-IN"):
    r = requests.post(f"{SARVAM}/text-to-speech",
                      headers=HDR,
                      json={"inputs": [text], "target_language_code": lang,
                            "speaker": "meera", "model": "bulbul:v2"})
    return base64.b64decode(r.json()["audios"][0])
```

---

## Picking your first POC

If you're starting from your existing VAPI / Deepgram / Dograh experience,
the highest-leverage next builds are:

1. **#3 Meeting summarizer** — single-file, no telephony, no realtime; great
   way to learn Whisper + pyannote + LLM JSON output.
2. **#4 Call QA scorer** — same pipeline, monetizable, easy demo.
3. **#1 Inbound agent** — your VAPI experience translates 1:1; building it
   in raw FastAPI teaches you what VAPI abstracts away.

Next → `07_advanced_topics.md`.
