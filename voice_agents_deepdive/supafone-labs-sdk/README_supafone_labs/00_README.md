# Supafone Labs — Deep Dive

Research notes on [Supafone Labs](https://labs.supafone.ai/) — production infrastructure
for voice agents. This folder complements the STT/TTS/pipeline notes in the parent
directory by studying a real-world, provider-agnostic voice-agent platform.

> **One-line thesis:** "Fast models need slow supervisors." A voice agent must reply
> in under a second to sound human, which structurally prevents the talking model from
> also being the model that deliberates. Supafone runs a second, slower model *beside*
> the call that whispers silent corrections — without ever being on the audio hot path.

## What Supafone Labs is

A developer SDK + hosted platform that does two things:

1. **Supervise an agent you already run** (`supercharge(my_agent)`) — the "Supafone
   Supervisor" sidecar. Works with Vapi, Retell, ElevenLabs, OpenAI Realtime, Ultravox,
   Deepgram, LiveKit, Pipecat, and more — 14 audited runtimes.
2. **Provision a complete agent** ("Agent Factory") — one API key gives you a phone
   number, voice, multi-stage flow, tools, transcripts, recordings, and supervision.

Open source (MIT) SDK; managed cloud at **$0.10/min** (5 free minutes to start).

## File index

| File | Topic |
| --- | --- |
| [01_overview.md](01_overview.md) | What Supafone Labs is, who it's for, the problems it solves |
| [02_architecture_sidecar_oracle.md](02_architecture_sidecar_oracle.md) | The sidecar architecture, canonical event loop, degrade-safety |
| [03_supafone_supervisor.md](03_supafone_supervisor.md) | The supervisor: belief state, whisper path, outcome loop |
| [04_provider_agnostic_framework.md](04_provider_agnostic_framework.md) | 14 adapters, injection modes, managed vs BYOK |
| [05_agent_factory_and_builder.md](05_agent_factory_and_builder.md) | Hosted Agent Factory, builder, call stages, tools |
| [06_stt_tts_in_supafone.md](06_stt_tts_in_supafone.md) | How STT/TTS fit — transcript authority, Deepgram tap, voices |
| [07_sdk_api_quickstart.md](07_sdk_api_quickstart.md) | Install, keys, SDK/REST/MCP surfaces, code examples |
| [08_pricing_and_credits.md](08_pricing_and_credits.md) | Plans, usage meters, credit ledger, number billing |
| [09_research_paper_summary.md](09_research_paper_summary.md) | "The Sidecar Oracle" whitepaper — meta-analysis + harness |
| [10_glossary_and_links.md](10_glossary_and_links.md) | Terminology, official links, further reading |

## Key facts at a glance

- **SDKs:** Python (`pip install "supafone-labs[all]"`) and TypeScript (`npm i supafone-labs`)
- **Surfaces:** Python, TypeScript, REST + WebSocket, MCP — one `sl_live_...` key for all
- **Frameworks covered:** 14 audited runtimes (Ultravox, Vapi, Retell, Bland, OpenAI
  Realtime, Grok Voice, Gemini Live, ElevenLabs, Deepgram VA, Inworld, LiveKit, Pipecat,
  Cartesia Line, generic webhook)
- **Telephony:** Twilio, Telnyx, Plivo, SignalWire, SIP/custom trunks
- **Claimed benchmark:** ~40% more reliable live calls vs baseline (same stack, supervisor added)
- **Whitepaper:** *The Sidecar Oracle*, Sam Savage, Supafone Labs, July 2026, v1.1
- **Repo:** https://github.com/samthedataman/supafone-labs

## How to use these notes

Read in order 01 → 09 for a full mental model. If you only care about the STT/TTS angle
(matching the rest of this workspace), jump straight to
[06_stt_tts_in_supafone.md](06_stt_tts_in_supafone.md). If you want to prototype, start
with [07_sdk_api_quickstart.md](07_sdk_api_quickstart.md).

---

*All content sourced from labs.supafone.ai/docs (fetched 2026-08-29). Treat pricing and
provider-support tables as point-in-time — verify against the live docs before building.*
