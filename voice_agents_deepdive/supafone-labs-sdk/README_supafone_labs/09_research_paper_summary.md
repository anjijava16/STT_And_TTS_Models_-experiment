# 09 · Research Paper — "The Sidecar Oracle"

**A Provider-Agnostic Supervisor Harness for Real-Time Voice Agents**
Sam Savage · Supafone Labs · July 2026 · v1.1
[PDF](https://labs.supafone.ai/whitepaper.pdf) · [GitHub](https://github.com/samthedataman/supafone-labs)

This is the academic backbone that justifies the whole product. Worth reading if you want
the *why*, not just the *how*.

## Abstract (paraphrased)

Production voice agents operate under a hard latency budget: to sound human they must
respond in well under a second, which **structurally prevents the model that talks from
also being the model that deliberates**. The paper surveys 24 published results across five
research threads and finds they converge on a single architecture: a second, slower model
running beside the conversation, off the latency path, injecting silent corrections through
whatever control channel the serving platform natively exposes.

**Primary contribution:** a runtime harness that makes supervision provider-, LLM-,
speech-to-speech-, and TTS-agnostic:

- a canonical event algebra with per-provider adapters
- a deterministic state reducer carrying ground-truth outcome signals
- capability-aware compilation of one abstract correction decision into 13 platforms' native controls
- degrade-safety semantics: supervisor failure composes with the live call as a no-op

Plus an outcome-driven improvement loop (SSR grading + OPRO-style directive optimization)
that never touches the operator's own system prompt.

## §2 — Meta-analysis: five converging threads

| Thread | Evidence |
| --- | --- |
| **Separate talker from deliberator** | Talker-Reasoner (Christakopoulou 2024); dual-process framing (Booch 2020) |
| **Supervision must be external** | Intrinsic self-correction *degrades* (GSM8K 75.9→74.7; CSQA 75.8→38.1) while oracle-triggered correction *gains* (→84.3) (Huang 2023) |
| **The supervisor can be small** | 6B verifier ≈ 30× smaller than generator (Cobbe 2021); 7B critic ≈ ChatGPT (Shepherd); monitor recall 95% (Baker 2025) |
| **Supervise turns, not outcomes** | Process supervision 78.2% vs outcome-only 72.4% on MATH (Lightman 2023) |
| **Never optimize against the monitor** | Obfuscated reward hacking; monitor recall → 0 when judgments join the reward (Baker 2025) |
| **Improve prompts offline, from scores** | OPRO, DSPy, TextGrad, ProTeGi, Darwin Gödel Machine |

> **Pivotal negative result (Huang et al.):** a model reviewing its *own* answer with no
> external feedback reliably gets *worse*. The refinement mechanism works; self-generated
> judgment is the weak link. A supervisor must be a separate process with separate context
> and access to ground truth — in a voice call, the tool results and event stream the
> *runtime*, not the model, holds.

## §3 — The runtime harness

### 3.1 The substrate problem

Three classes of serving stack (S2S / pipeline / framework), each with different event
vocabularies and quarterly-drifting wire formats. **This heterogeneity, not the oracle, is
the engineering problem.**

### 3.2 Canonical events + deterministic reducer

Per-provider adapters supply two pure functions — `parse: Raw → E*` and
`compile: D × Σ → A`. A deterministic reducer folds events into state **Σ**: transcript with
per-turn language tags, tool history, and **truth sub-state** (was the booking verified? did
the delivery send?). Σ contains no model call, is ground truth by construction, and is
replayable from the event log.

### 3.3 Capability-aware injection compilation

One abstract decision compiles across 14 audited runtimes (full table in
[04_provider_agnostic_framework.md](04_provider_agnostic_framework.md)).

### 3.4 The whisper path + degrade-safety

Off the hot path, the oracle maintains a **belief state** (identity, intent, emotion,
language, urgency) and produces a directive under operator guardrails, gated by a confidence
threshold. It runs behind a timeout with catch-all semantics:

> A stalled model, dead STT socket, or failed TTS backend cannot lengthen, alter, or end the
> call it shadows. **The worst case is the status quo.**

## §4 — The improvement loop

### 4.1 Grading against ground truth

Because Σ carries verified outcomes, calls are scored deterministically at session end:
unverified bookings, unverified sends, unbacked claims, and dead-air events each subtract
from a unit score. **No LLM grades production calls where tool-verified ground truth
exists.**

### 4.2 SSR grading (new in v1.1)

Where an LLM judge *is* required (builder test calls, objective classification), raw numeric
scores are unreliable — judges are poor regressors but consistent classifiers. So grading
uses a **five-level nominal scale**: "the agent did {poorly | ok | good | great | perfectly}
at achieving the objective," overall and per criterion. Each label maps deterministically
onto a canonical score + a discrete distribution over 10 buckets. Aggregating many calls
yields a real **score distribution** — the shape of performance, not just a pass rate —
exposed at `GET /v1/objective/distribution`.

Implemented as a LangGraph flow with two nodes: `grade` (the only model call) and `map`
(deterministic label → score + distribution). Degrades to sequential execution when
LangGraph is absent.

### 4.3 The standing directive

The harness owns one prompt surface: **its own channel**. The standing directive is a
persistent, versioned coaching preamble injected at call start. An improvement step feeds
recent scored reports (weighted toward moving calls out of the lowest levels first) + the
current directive to a critic model, OPRO-style, yielding a new version with a rationale.
Runs offline between calls; output is **injected context, never a training signal** (honoring
the obfuscation/verifier-gaming cautions). **The operator's base prompt is untouched by
design.**

### 4.4 Observability as a product invariant

Every whispered directive is logged with confidence, language, inferred caller emotion,
oracle latency, model, and billing cost. Every optimization step records the reports it
consumed. Every SSR verdict stores both label and mapped score.

## §5 — The Agent Factory

The same control plane that supervises third-party stacks can provision complete agents —
collapsing the five-key integration (telephony, TTS, STT, LLM, supervision) into one API
key. Supervision is on by default for factory agents; BYOK covers teams that own a stack.

## §6 — Limitations (stated honestly)

1. No controlled trial yet measures the sidecar's effect on business outcomes; the
   meta-analysis validates components in adjacent domains.
2. SSR grading applies only where an LLM judge is required; deterministic scoring covers
   only tool-verified ground truth.
3. Whisper uptake is bounded by each platform's injection semantics; **two platforms offer
   no channel** (Bland, Cartesia Line).
4. Standing-directive optimization inherits OPRO's brittleness; directive length is bounded
   and version history retained because regressions are expected.
5. The oracle adds cost per turn; small-supervisor economics + per-second metering make it
   visible.

## §7 — Conclusion (the thesis in one breath)

> Fast models need slow supervisors; supervision must be external; a small second model
> catches what the first cannot; its judgments must be injected, not optimized against; and
> prompt layers should improve offline from measured, distribution-shaped outcomes. What
> stood between that consensus and production voice AI was a substrate problem — closed by a
> canonical event algebra, a deterministic ground-truth reducer, capability-aware
> compilation, and no-op failure semantics.

## Key references

Christakopoulou 2024 (Talker-Reasoner) · Huang 2023 (self-correction fails) · Cobbe 2021
(verifiers) · Lightman 2023 (process supervision) · Baker 2025 (monitor obfuscation) · Wang
2023 (Shepherd) · Yang 2023 (OPRO) · Khattab 2023 (DSPy) · Yuksekgonul 2024 (TextGrad) ·
Pryzant 2023 (ProTeGi) · Bai 2022 (Constitutional AI). Full citations in the PDF.

---

*Next: [10_glossary_and_links.md](10_glossary_and_links.md)*
