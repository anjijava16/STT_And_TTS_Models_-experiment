# 06 · STT & TTS in Supafone

This is the file that ties Supafone Labs back to the rest of this workspace's STT/TTS
notes. Supafone's stance on speech is deliberately **provider-agnostic** — it does not
force one STT or one TTS on you.

## Transcript authority: exactly one per call

Supafone Supervisor does **not** force every provider through one speech-to-text model. It
selects **exactly one** transcript source per call:

| When | Transcript source | STT model / control |
| --- | --- | --- |
| Provider emits usable transcript events | The provider's own transcript stream | The provider controls its STT model |
| Supafone Labs multilingual audio tap | Deepgram streaming STT | `nova-3`, `language=multi` |
| Host-integrated narrowband phone tap | The host's configured Deepgram consumer | Host-controlled; Twilio reference defaults to `nova-2-phonecall` |

### Why the narrowband default is deliberate

Twilio PSTN audio arrives as **8 kHz mu-law**. The narrowband tap therefore defaults to a
phone-tuned model (`nova-2-phonecall`). The multilingual SDK tap uses **Nova-3** when
language tagging and live code-switching are required.

> Set `DEEPGRAM_MODEL` in a host deployment to change its telephony-tap model.

**Important cost rule:** do **not** run the Deepgram tap when the selected agent provider
already supplies the required transcript and language metadata — that duplicates turns and
transcription cost. This maps directly to the "exactly one transcript authority" rule.

## STT in the BYOK contract

```json
{
  "labs": {
    "mode": "byok",
    "stt": { "provider": "deepgram", "model": "nova-3" }
  }
}
```

STT lane options: **Deepgram** or **provider-native transcript streams**. The runtime
records per-turn language tags in the deterministic state Σ (see
[02_architecture_sidecar_oracle.md](02_architecture_sidecar_oracle.md)), which is what makes
mid-call language switches detectable.

## TTS providers

Voice rendering can be managed or customer-owned. Supported TTS lanes:

- **Cartesia**
- **ElevenLabs**
- **Inworld**
- **Deepgram**
- **custom TTS**

BYOK TTS example:

```json
{ "labs": { "mode": "byok", "tts": { "provider": "elevenlabs" } } }
```

Managed voice selection at agent creation:

```typescript
voice: { provider: "cartesia", voiceId: "Jacqueline" }
```

## Voice catalog & discovery

Rather than hard-coding voice inventory, query it live:

```typescript
const voices = await supafone.labs.voices.list({ provider: "cartesia" });
```

The platform advertises a **normalized voice catalog** with compatibility metadata across
supported speech providers, plus **voice previews** and a **dynamic voice catalog** with
selection. Language routing lets you opt into language-specific voice profiles **while
preserving the same call state and workflow** — you don't rewrite the agent graph to add a
language.

## How STT/TTS relate to the supervisor

Key architectural point relevant to the STT→LLM→TTS pipeline notes in the parent folder:

- The **speaking** path (STT → LLM → TTS) stays fast and owns the audio.
- The **supervisor** consumes the *same* transcript + tool events but runs a **separate,
  slower LLM** off the hot path.
- STT feeds *both* — the speaking agent and the supervisor's belief state (intent, emotion,
  language, truth).
- TTS is never touched by the supervisor; directives are injected as **context**, not
  spoken. A failed TTS backend cannot be worsened by the supervisor (degrade-safety).

```text
        STT (one authority per call)
          |
   +------+-------------------+
   |                          |
   v                          v
speaking LLM --> TTS      supervisor LLM (off hot path)
   |                          |
   v                          v
customer audio           silent directive (context only)
```

## Practical takeaways for a POC

1. If your provider already emits transcripts (e.g. Vapi, Retell), **don't** add the
   Deepgram tap — reuse the native stream.
2. For raw Twilio media streams, expect `nova-2-phonecall` on 8 kHz mu-law; switch to
   `nova-3 language=multi` only if you need multilingual/code-switch handling.
3. TTS choice is independent of STT choice and independent of the supervisor LLM — mix
   freely (e.g. Deepgram STT + ElevenLabs TTS + Anthropic supervisor).

---

*Next: [07_sdk_api_quickstart.md](07_sdk_api_quickstart.md)*
