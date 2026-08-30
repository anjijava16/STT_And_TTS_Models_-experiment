# 02 · Architecture — The Sidecar Oracle

## The mental model

Human call centers solved this problem decades ago without retraining agents mid-shift:
a supervisor listens silently and slides a note across the desk. The agent keeps talking;
the note changes the call. Supafone Labs is that supervisor, in software.

## The architecture diagram

```text
Caller -> speaking agent -> tools and business systems
             |                         |
             +---- call events --------+
                          |
                          v
               canonical call state
                    |          |
                    v          v
              live supervision   call artifacts
                    |
          confidence + policy gate
                    |
              provider adapter
                    |
          silent bounded guidance
                    |
                    +------> speaking agent
```

**The call never waits for supervision.** If supervision is unavailable, late, or
uncertain, the gate emits no directive and the original agent continues.

## The five steps of the runtime

1. **Normalize** vendor events into canonical call events.
2. **Maintain deterministic runtime state** — stage, consent, tool state, caller intent,
   risk flags.
3. **Run the oracle** only when supervision is enabled.
4. **Emit** a silent directive or a provider-native action.
5. **Log** the decision, latency, provider, model, and billing metadata.

The caller never hears the directive directly. The live agent reads it as context, or
receives it through the provider's native control channel.

## The two silent-injection modes

| Mode | When | Mechanism |
| --- | --- | --- |
| **Mode A — native silent event** | Speech-to-speech models | A vendor event that adds context without triggering speech (e.g. Ultravox `inject_message`, OpenAI Realtime `conversation.item.create` with no `response.create`, ElevenLabs `contextual_update`, Gemini Live `clientContent`) |
| **Mode B — own the LLM** | STT→LLM→TTS pipelines | Supafone plugs in as the LLM and splices a `system`/`developer` message into the prompt (Retell, LiveKit custom-LLM loops; Vapi + Deepgram support both modes) |

Of the 14 audited runtimes: 12 have native or developer-owned guidance paths, **Bland is
observation-only**, and **Cartesia Line requires an explicit host hook**.

## The deterministic reducer + "truth state"

The harness defines a canonical event vocabulary and, per provider, an adapter supplying
two pure functions:

- `parse: Raw → E*` — raw vendor events into canonical events
- `compile: D × Σ → A` — an abstract decision `D` + state `Σ` into the provider's native actions `A`

A deterministic reducer folds events into runtime state **Σ**:

- the transcript with per-turn **language tags**
- tool history
- and — decisively — **truth sub-state**: whether a requested booking was ever verified
  by a tool result, whether a promised delivery actually sent.

> Σ contains no model call, is ground truth *by construction*, and is replayable from the
> event log.

This is why Supafone can catch "the agent about to confirm a booking whose API call
silently failed" — the runtime, not the model, holds the ground truth.

## Degrade-safety (the safety invariant)

The entire oracle runs behind a timeout with catch-all semantics:

> **Supervisor failure composes with the live call as the identity.**

A stalled model, dead STT socket, or failed TTS backend **cannot lengthen, alter, or end**
the call it shadows. The worst case is the status quo.

> "The supervisor rides beside the call. It does not drive, and it cannot crash the bike."

## The event loop in code

```python
brain = supafone_labs.SupafoneLabs(
    provider="ultravox",
    llm="hosted",
    agent_label="intake",
)

async def on_platform_event(raw_event):
    result = await brain.observe(raw_event)
    for action in result.actions:
        await deliver_to_voice_platform(action)
```

The deterministic runtime can still emit policy decisions even if the LLM oracle is
unavailable — that is the degrade-safe path.

## Why "off the hot path" matters

Perceived conversational quality collapses when response latency exceeds ~1 second, so
every serving stack optimizes the talking model for speed. Everything that determines
whether a call *succeeds* is deliberation the latency budget forbids:

- reading distress in a caller's phrasing
- noticing a mid-call language switch
- catching a false confirmation

By moving deliberation to a **separate, slower model beside the call**, Supafone gets the
reasoning without paying the latency.

---

*Next: [03_supafone_supervisor.md](03_supafone_supervisor.md)*
