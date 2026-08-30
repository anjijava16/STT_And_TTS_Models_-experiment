# 07 — Advanced Topics (Hero Level)

The 10 % of details that separate a working demo from a production voice
product. Each section is short and deep.

---

## 7.1 Endpointing — when to stop "listening"

Endpointing is the decision: "the user has finished their turn." Get it
wrong in either direction and the UX collapses.

- Too aggressive (cut off early) → "I'd like to ord—" agent already replying.
- Too lazy (waits too long) → 2-second awkward gap after every sentence.

Three layers, used together:

```
┌────────────────────────────────────────────────────────────────┐
│ Layer 1: VAD (does this 30 ms frame contain voice?)            │
│   Silero-VAD / WebRTC-VAD, frame-level boolean                 │
├────────────────────────────────────────────────────────────────┤
│ Layer 2: Silence timer (consecutive non-voice frames > N ms?)  │
│   Tunable: 250 ms (snappy) ↔ 800 ms (patient)                  │
├────────────────────────────────────────────────────────────────┤
│ Layer 3: Semantic endpointing                                  │
│   Did the transcript end on a sentence-ending pattern?         │
│   ("Yes." vs "And um..." — different finalization)             │
└────────────────────────────────────────────────────────────────┘
```

Recent providers (Deepgram, OpenAI Realtime, LiveKit) ship **smart
endpointing** — a small LM that predicts "is this utterance complete?" given
the partial transcript. ~50 % fewer false stops in our testing.

Tuning:
- Phone IVR menu (single intent): silence = 250 ms.
- Conversational assistant: silence = 500 ms + semantic check.
- Voice journaling / open-ended: silence = 1500 ms.

```python
# advanced — semantic endpointing on top of silence timer
COMPLETE_PATTERNS = [r"\.$", r"\?$", r"!$", r"\b(yes|no|okay)\b$"]

def is_complete(partial: str) -> bool:
    import re
    p = partial.strip()
    if len(p.split()) < 2: return False
    return any(re.search(pat, p, re.I) for pat in COMPLETE_PATTERNS)

# in your STT loop, when silence_ms > 250 AND is_complete(last_partial): finalize
```

---

## 7.2 Acoustic Echo Cancellation (AEC)

Your bot speaks. The mic hears the speaker. STT transcribes your bot's own
voice and the LLM responds to itself. Infinite loop.

```
mic input ──▶ [ AEC ]  ──▶ STT
                ▲
                │ reference
              speaker out
```

Options:
- **Twilio / Telephony**: usually handled by the carrier — verify on your
  test calls anyway.
- **WebRTC / Browser**: `getUserMedia({echoCancellation: true})` is on by
  default. Trust it.
- **PyAudio / native**: use `speexdsp` or a WebRTC binding (`pyrtcaudio`).
- **LiveKit Agents**: built-in.

If you can't run AEC, the fallback is "half-duplex" — mute the mic while the
bot is speaking. Cheap, kills barge-in.

---

## 7.3 Barge-in done right

Already introduced in `04_stt_llm_tts_pipeline.md`. The full discipline:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Always-on STT (never paused during bot speech)               │
│ 2. AEC removes bot voice from mic stream                        │
│ 3. VAD on cleaned signal triggers interrupt event               │
│ 4. Interrupt handler:                                           │
│      a. stop TTS playback (drop queued audio chunks)            │
│      b. cancel LLM streaming task                               │
│      c. truncate assistant message to "what was actually heard" │
│         (estimate from playback bytes consumed)                 │
│      d. set state back to TRANSCRIBING                          │
└─────────────────────────────────────────────────────────────────┘
```

Tracking *what the user actually heard* is the subtle part:

```python
# advanced — track how much of the reply got out before interrupt
bytes_played = 0           # incremented in playback loop
bytes_per_char = 200       # rough: at 24kHz 16-bit, ~2400 B per ms,
                           # ~80 chars per sec speech → 200 B/char
def truncate(text, bytes_played):
    chars = bytes_played // bytes_per_char
    return text[:max(0, chars)]
```

Better: use word timestamps from the TTS provider if exposed (ElevenLabs
returns alignment) and truncate at the last word actually emitted.

---

## 7.4 Streaming sentence chunking from LLM

Don't send raw token deltas to TTS — TTS WS APIs want phrase-sized pieces.
Don't wait for the full reply either — that's the latency you're trying to
avoid.

```python
# intermediate — buffer tokens, flush on sentence/clause boundaries
import re

class SentenceChunker:
    BOUNDARIES = re.compile(r"([.!?,;:]\s|[\n])")
    MIN_CHARS  = 40       # avoid micro-chunks; latency vs prosody trade-off

    def __init__(self):
        self.buf = ""

    def feed(self, tok: str):
        self.buf += tok
        out = []
        while True:
            m = self.BOUNDARIES.search(self.buf, self.MIN_CHARS)
            if not m: break
            cut = m.end()
            out.append(self.buf[:cut])
            self.buf = self.buf[cut:]
        return out

    def drain(self):
        if self.buf.strip():
            x, self.buf = self.buf, ""
            return [x]
        return []
```

Use:
```python
ch = SentenceChunker()
async for tok in llm_stream:
    for sent in ch.feed(tok):
        await tts_ws.send(sent)
for sent in ch.drain():
    await tts_ws.send(sent)
```

---

## 7.5 Latency optimization checklist

Order of impact (highest first):

```
☐  Use streaming everywhere (STT, LLM, TTS) — never batch
☐  Co-locate servers (LLM region == TTS region == STT region)
☐  Pre-warm WS connections (open at session start, not on first turn)
☐  Use smaller, faster models on hot path (gpt-4o-mini, Sonic, Nova-3)
☐  Sentence-boundary flush from LLM into TTS (do NOT wait for full reply)
☐  Tighten endpointing silence threshold (semantic-EOS if available)
☐  Cache filler audio ("um, one moment...") for tool calls
☐  Speculative pre-execution of likely tool calls (account lookup at
    first utterance — discard if not asked)
☐  Use HTTP/2 or gRPC keepalive — TCP slow-start kills first turn
☐  Avoid intermediate buffering (no jitter buffer > 60 ms)
☐  Set TTS output format = native sample rate of telephony (8 kHz μ-law
    for Twilio) to skip a resample stage
```

---

## 7.6 Cost optimization

A streaming voice agent burns:
- STT minutes (per-min metered)
- LLM tokens (input + output, per request)
- TTS characters (per response, per char)
- WS / compute (mostly negligible)

Quick wins:
- Stop transcribing during long silences (gate STT by VAD).
- Use a small router LLM to decide if a big LLM is needed.
- Cache TTS for repeated phrases (greetings, holds, confirmations).
- Compress conversation history aggressively (drop turn N-10 verbatim,
  summarize older).
- For high-volume non-realtime work, self-host Whisper + Llama + Piper.

```python
# intermediate — TTS cache for common phrases
import hashlib, os
CACHE_DIR = "tts_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(text, voice):
    h = hashlib.sha1(f"{voice}|{text}".encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{h}.pcm")

async def speak_cached(text, voice):
    p = cache_path(text, voice)
    if os.path.exists(p):
        return open(p, "rb").read()
    pcm = await synthesize(text, voice)
    open(p, "wb").write(pcm)
    return pcm
```

Greetings, holds, intent confirmations — cache them all.

---

## 7.7 Multi-modal & function-aware voice agents

Modern voice agents do more than chat. They:
- See screen content (multimodal LLM): "I'm looking at the invoice."
- Read DTMF input ("press 2 for…").
- Hand off to a human with full call context.
- Send SMS / email mid-call ("I just texted you the link").

```python
# intermediate — pass DTMF events to the LLM
@app.websocket("/media")
async def media(ws):
    ...
    async for raw in ws.iter_text():
        ev = json.loads(raw)
        if ev["event"] == "dtmf":
            digit = ev["dtmf"]["digit"]
            history.append({"role": "user", "content": f"<DTMF:{digit}>"})
            # let the LLM decide what the digit means in context
```

---

## 7.8 Reliability — handling failures gracefully

The five things that will go wrong:

| Failure | Detection | Recovery |
|---------|-----------|----------|
| STT WS drops | `on_close` + heartbeat timeout | Reconnect, replay last 2 s of buffered audio |
| LLM timeout | `asyncio.wait_for` | Speak filler, retry with shorter prompt |
| TTS WS drops mid-utterance | playback queue empty + connection error | Resynthesize remaining text on a backup provider |
| Twilio media stream stalls | no frames for 1 s | Hang up, schedule callback |
| LLM produces JSON garbage for tool call | parse exception | Retry with `response_format=json`, then degrade to text |

Always have a *second* TTS provider warmed and ready. Voice is the one
modality where falling back to text isn't an option.

---

## 7.9 Evaluation — how do you know it's working?

Three layers:

1. **Component metrics** (per-leg)
   - STT: WER, partial-to-final latency, false-final rate
   - LLM: time-to-first-token, tool-call success, hallucination rate
   - TTS: TTFA, MOS, alignment WER

2. **Conversation metrics**
   - Turn latency (p50, p95, p99)
   - Barge-in success rate
   - Average turns to resolution
   - User talk-time fraction

3. **Business metrics**
   - Containment rate (% of calls resolved without human)
   - CSAT post-call
   - Cost per resolution

Set up a regression test set of 50 recorded conversations. Replay them
nightly. Alert on WER regression > 1 %, latency regression > 50 ms p95.

---

## 7.10 The frontier — direct audio-to-audio models

You skip STT and TTS entirely. The LLM consumes audio and emits audio.

```
mic ──audio tokens──▶ [ Multimodal LLM ] ──audio tokens──▶ speaker
                          (gpt-4o-realtime,
                           Gemini Live,
                           Moshi, Kyutai)
```

Pros:
- Lowest latency (~300 ms end-to-end).
- Preserves paralinguistic info (tone, hesitation) the model can reason about.

Cons:
- Less control (can't swap voice / language as easily).
- Provider lock-in.
- Harder to debug (no intermediate transcript).

In 2026, the smart pattern is hybrid: use direct audio for casual chat,
fall back to STT-LLM-TTS for anything needing strict tool-calling
guardrails or compliance transcripts.

---

## 7.11 Open research vectors (if you want to publish or push frontier)

- **Token-level interruption**: model emits "I'll stop talking" naturally
  rather than the system cutting playback.
- **On-device end-to-end**: Whisper-small + Phi-3 + Piper, all on a phone.
- **Personalized acoustic adaptation**: 30 s of user audio improves STT WER
  10–20 % for that user.
- **Emotion-aware TTS**: condition on detected user sentiment from STT
  prosody features.
- **Diarization-aware streaming**: tag speakers in real-time, not as a
  post-process.

Onwards → `08_poc_starter_kits.md` for full runnable scaffolds.
