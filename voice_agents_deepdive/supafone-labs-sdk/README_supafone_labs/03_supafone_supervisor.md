# 03 · Supafone Supervisor

The Supervisor runs beside an agent, off the realtime hot path. It observes the call,
returns a silent directive **only when the live agent needs help**, and can score/QA the
call after it ends.

## First principle: a speaking model cannot fully supervise itself

Realtime voice models are optimized to answer quickly. A production supervisor has a
different job. Putting both jobs in one prompt creates a structural conflict — more
reasoning adds latency; less reasoning misses the moment. Supafone separates the roles:

```text
speaking model                         supervisor model
--------------                        ----------------
fast, natural response                slower cross-turn reasoning
owns the customer audio               never speaks to the customer
uses tools and follows stages         checks tool truth and stage progress
continues if supervisor is absent     emits a bounded silent directive or no-op
```

The supervisor is **not** a replacement agent and **not** a transcript summarizer. It is a
second control loop beside the call.

## The "secret sauce": empathy as observable patterns

"Empathy" is not a personality adjective in the runtime. It is a changing set of
observable patterns that affect what the agent should do next:

- **intent** — what outcome the caller is actually trying to reach
- **urgency** — whether waiting, escalation, or a shorter path matters
- **emotion** — confusion, frustration, fear, confidence, relief across turns
- **language** — an explicit request or clear utterance in an approved language
- **trust** — whether the agent acknowledged, verified, and followed through
- **progress** — whether the current workflow stage is advancing or looping
- **truth** — whether a booking, transfer, send, or CRM action really succeeded

> The Supervisor maintains that belief state over time. It does **not** route from a name,
> accent, nationality, or presumed demographic. It waits for evidence.

## The supervisor loop

```text
provider event
  -> normalize into one call contract
  -> update intent / emotion / language / stage / tool truth
  -> compare with objective, policy, and standing directive
  -> guard on evidence, tenant, provider, cooldown, and timeout
  -> compile one silent native instruction—or do nothing
  -> observe the next turn and verify whether it helped
  -> grade the completed call and improve the standing directive
```

## What Supafone monitors

- caller intent, urgency, language, and emotion
- transcript contradictions
- tool result failures
- unverified booking, sending, pricing, or policy claims
- compliance rules (e.g. *no fee quotes*, *no legal/medical advice*)
- whether the agent is following the current standing directive

## Enabling supervision

Supervision, QA, and call scoring are **on by default** for hosted agents.

```python
from supafone_labs import Supafone
supafone = Supafone(api_key="sl_live_...")
```

```typescript
import { Supafone } from "supafone-labs";
const supafone = new Supafone({ apiKey: process.env.SUPAFONE_TOKEN! });
```

Use the optional `supervisor` boolean to disable/re-enable the default.

### Enable on hosted agents (JSON contract)

```json
{ "labs": { "enabled": true, "model": "gemma" } }
```

Legacy equivalent: `{ "voice_watcher": true, "voice_watcher_model": "gemma" }`.

### Bring-your-stack supervision

```python
from supafone_labs import SupafoneLabs

brain = SupafoneLabs(provider="vapi", llm="hosted", agent_label="intake")
result = await brain.observe(raw_event)
for action in result.actions:
    await deliver_to_voice_platform(action)
```

## The outcome loop (post-call improvement)

Report the finished call:

```typescript
await supafone.reportCall({
  session_id: "call-123",
  agent: "intake",
  score: 0.82,
  outcome: "clean",
  summary: "Caller scheduled a follow-up without unsupported claims.",
  nudges: 2,
  turns: 14,
  language: "en"
});
```

Classify a transcript against an objective:

```bash
curl https://api.labs.supafone.ai/v1/calls/classify \
  -X POST -H "Authorization: Bearer $SUPAFONE_LABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"call-123","agent":"intake",
       "transcript":"caller: what do you charge?\nagent: I cannot quote fees here.",
       "nudges":1}'
```

Improve the **standing directive** (OPRO-style offline optimization):

```typescript
const improved = await supafone.optimizer.improve("intake");
console.log(improved.version, improved.text);
```

Read the current standing directive:

```bash
curl "https://api.labs.supafone.ai/v1/optimizer/standing?agent=intake" \
  -H "Authorization: Bearer $SUPAFONE_LABS_API_KEY"
```

## Model-agnostic by construction

The contract is between **call events and supervisor directives**, not between Supafone and
one model vendor. The speaking model, supervisor model, carrier, STT, and TTS can each be
selected independently when the provider exposes the required control surface.

## Degrade safety

The supervisor is timeout-bounded and off the hot path. If the oracle fails, times out,
hits a balance/cap error, or decides no intervention is needed, it returns **no directive**
and the call continues normally.

---

*Next: [04_provider_agnostic_framework.md](04_provider_agnostic_framework.md)*
