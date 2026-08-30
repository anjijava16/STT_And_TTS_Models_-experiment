Absolutely. Since you already know **LangGraph, Google ADK, and agentic architectures**, I would **not** teach you Supafone as a beginner voice-AI tutorial. The useful way to prepare for tomorrow is to map Supafone onto concepts you already understand:

> **Supafone Labs = Voice Agent Runtime + Agent Factory + real-time Supervisor/Watcher + QA/Evaluation + Telephony/Voice infrastructure.**

I went through the current Supafone Labs site and its GitHub repository rather than relying on the earlier high-level description. The current architecture is broader than simply “Vapi alternative.” ([Supafone Labs][1])

Below is the **zero → hero README-style workshop guide** I would use to prepare.

---

# Supafone Labs — Zero to Hero

## 1. What problem is Supafone solving?

Traditional voice agents look like this:

```text
                 ┌──────────────┐
Caller ─────────►│ Voice Agent  │
                 └──────┬───────┘
                        │
                ┌───────┼────────┐
                ▼       ▼        ▼
               STT     LLM      TTS
```

The LLM is responsible for:

* understanding the caller
* deciding what to do
* calling tools
* remembering state
* following policies
* detecting problems
* recovering from failures
* responding naturally

And it must do all of that **in real time**.

That's a fundamental architectural problem.

Supafone's key idea is:

```text
                    ┌─────────────────────┐
                    │  Supervisor /       │
                    │  Second Mind        │
                    │                     │
                    │  Observe → Think    │
                    │  → Coach            │
                    └──────────┬──────────┘
                               │
                         silent guidance
                               │
                               ▼
Caller ───────────────► Voice Agent
```

The main voice agent **talks**.

The Supafone Supervisor **watches**.

The supervisor can then silently inject guidance into the agent.

Supafone describes this as an **off-latency-path second mind** that observes transcripts, state, tools and outcomes and sends provider-native corrective instructions. ([GitHub][2])

---

# 2. The most important concept

If you remember only one thing for your workshop, remember this:

## Talker ≠ Supervisor

A traditional architecture:

```text
             ONE AGENT

Caller
  │
  ▼
┌───────────────────────────┐
│       Voice Agent         │
│                           │
│ Understand                │
│ Reason                    │
│ Call tools                │
│ Follow policy             │
│ Respond                   │
└───────────────────────────┘
```

Supafone:

```text
                     ┌──────────────────┐
                     │    SUPERVISOR    │
                     │                  │
                     │ Observe          │
                     │ Analyze          │
                     │ Detect problems  │
                     │ Coach            │
                     └────────┬─────────┘
                              │
                       silent directive
                              │
                              ▼
Caller ───────────────► ┌──────────────┐
                        │ Voice Agent  │
                        │              │
                        │ Talk         │
                        │ Tools        │
                        │ Respond      │
                        └──────────────┘
```

This is the architectural innovation you should emphasize.

---

# 3. How this maps to LangGraph

Because you know LangGraph, this is the easiest mental model.

A LangGraph application might look like:

```text
START
  │
  ▼
Understand Intent
  │
  ▼
Retrieve Context
  │
  ▼
Call Tool
  │
  ▼
Validate
  │
  ▼
Respond
  │
 END
```

Supafone isn't primarily replacing that graph.

Instead:

```text
                 ┌──────────────────────┐
                 │ Supafone Supervisor  │
                 │                      │
                 │ Observe live graph   │
                 │ Detect bad state     │
                 │ Generate correction  │
                 └──────────┬───────────┘
                            │
                            ▼
┌───────────────────────────────────────────────┐
│             Your Voice Agent                 │
│                                               │
│ State → LLM → Tool → State → Response        │
└───────────────────────────────────────────────┘
```

So think:

> **LangGraph = orchestration of the primary agent.**

> **Supafone Supervisor = external runtime supervision of the primary voice agent.**

That's a very important distinction.

---

# 4. Why not just put this into the system prompt?

This is one of the best questions to ask during the workshop.

Suppose your system prompt says:

```text
You are a helpful insurance agent.

Never confirm a cancellation until the
cancellation API succeeds.
```

That works at call start.

But during the call:

```text
Caller:
I want to cancel my policy.

Agent:
Sure, I'll cancel that for you.

Agent calls API.

API:
ERROR 500

Agent:
Your policy has been cancelled.
```

The prompt said:

> Don't claim cancellation unless API succeeds.

But the model still made a mistake.

Supafone's supervisor can observe:

```text
Tool:
cancel_policy()

Result:
ERROR
```

and inject:

```text
DO NOT confirm cancellation.
The cancellation tool failed.
Explain that the request could not be completed
and offer to retry/escalate.
```

So:

```text
SYSTEM PROMPT
      │
      │ static
      ▼
┌───────────────┐
│ Voice Agent   │
└───────────────┘
      ▲
      │ dynamic
      │
┌───────────────┐
│ Supervisor    │
└───────────────┘
```

### This is the core difference

**Prompt = static policy**

**Supervisor = dynamic runtime intervention**

The repository explicitly frames the problem this way: calls are live and the important event may happen after the initial prompt, so supervision needs to operate during the conversation. ([GitHub][2])

---

# 5. The Supafone architecture

The current architecture can be simplified to:

```text
                         SUPAFONE
                            │
              ┌─────────────┴─────────────┐
              │                           │
        Agent Factory               Supervisor
              │                           │
       Create agents                 Observe calls
       Create numbers                Analyze state
       Configure tools               Generate guidance
       Configure voices              Inject guidance
       Knowledge                     QA
       Campaigns                     Post-call analysis
              │                           │
              └──────────────┬────────────┘
                             │
                             ▼
                      Voice Runtime
                             │
          ┌──────────────────┼─────────────────┐
          ▼                  ▼                 ▼
       Telephony            STT               TTS
          │                  │                 │
       Twilio              Deepgram        Cartesia
       Telnyx              etc.            ElevenLabs
       SIP
```

The website currently describes two major pillars:

1. **Agent Factory**
2. **Supafone Supervisor**

It also includes phone/WebRTC, managed numbers, knowledge grounding, campaigns, call evidence, BYOK and multi-stage flows. ([Supafone Labs][1])

---

# 6. Supafone has TWO ways to use it

This is another critical workshop point.

## Mode A — Supafone hosts the agent

You let Supafone provide much of the infrastructure:

```text
Your Application
       │
       ▼
Supafone Agent Factory
       │
       ├── Phone number
       ├── Voice
       ├── STT
       ├── LLM
       ├── TTS
       ├── Tools
       ├── Knowledge
       ├── Supervisor
       └── QA
```

The SDK can create inbound/outbound agents and provision numbers. ([GitHub][2])

Example:

```python
from supafone_labs import Supafone

supafone = Supafone(
    api_key="YOUR_API_KEY"
)

agent = supafone.labs.agents.create_inbound_with_number(
    agent_key="insurance-intake",
    name="Insurance Intake",
    assistant_name="Maya",
    website_url="https://example.com",
    number={
        "search": {
            "areaCode": "415"
        }
    },
    labs={
        "enabled": True,
        "model": "gemma"
    }
)
```

Conceptually:

```text
create agent
     ↓
get phone number
     ↓
configure voice
     ↓
configure tools
     ↓
enable supervisor
     ↓
receive calls
```

---

# 7. Mode B — Bring your own voice stack

This is where Supafone becomes particularly interesting for someone with your background.

You already have:

```text
Vapi
Retell
LiveKit
Pipecat
OpenAI Realtime
Gemini Live
etc.
```

You don't necessarily need to replace it.

Instead:

```text
             YOUR EXISTING STACK

Caller
  │
  ▼
Vapi / LiveKit / Pipecat / Realtime
  │
  ▼
Voice Agent
  │
  │
  │       ┌────────────────────┐
  └──────►│ Supafone Supervisor │
          └─────────┬──────────┘
                    │
                    ▼
              Silent guidance
                    │
                    ▼
                 Agent
```

This is the **"wrap your own stack"** model.

The GitHub documentation explicitly lists integrations with Vapi, Retell, OpenAI Realtime, Gemini Live, Grok, ElevenLabs, Deepgram, Pipecat, LiveKit and others. ([GitHub][2])

---

# 8. The "TAP → THINK → WHISPER" architecture

This is probably the best diagram to put into your presentation.

```text
                  LIVE CALL
                     │
                     ▼
             ┌───────────────┐
             │      TAP      │
             │               │
             │ Transcript    │
             │ Tools         │
             │ State         │
             │ Outcomes      │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │     THINK     │
             │               │
             │ Belief State  │
             │ Policy        │
             │ Oracle        │
             │ Risk          │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │    WHISPER    │
             │               │
             │ Provider      │
             │ Native        │
             │ Control       │
             └───────┬───────┘
                     │
                     ▼
                VOICE AGENT
```

Supafone's own architecture describes this as:

**TAP → THINK → WHISPER**

with the supervisor operating outside the primary latency path. ([GitHub][2])

---

# 9. TAP

The supervisor needs information.

For example:

```json
{
  "session_id": "abc123",
  "speaker": "caller",
  "text": "I need to cancel my insurance",
  "timestamp": "...",
  "language": "en"
}
```

Then:

```json
{
  "tool": "cancel_policy",
  "arguments": {
    "policy_id": "123"
  },
  "result": {
    "success": false,
    "error": "API timeout"
  }
}
```

The supervisor consumes these events.

It can therefore maintain a live state:

```text
Intent:
  cancellation

Customer:
  frustrated

Language:
  English

Tool state:
  cancellation FAILED

Policy:
  don't confirm cancellation

Risk:
  HIGH
```

That's essentially a **belief state**.

---

# 10. THINK

Now the second mind reasons.

For example:

```text
Observation:
cancel_policy failed

↓

Supervisor reasoning:

The agent is likely to confirm
the cancellation.

↓

Action:

Tell agent not to confirm.
Ask it to explain failure.
```

Output:

```text
"Cancellation failed. Do not tell the caller
it was completed. Explain the issue and offer
to retry or escalate."
```

Notice:

The supervisor doesn't speak to the customer.

It speaks to the **agent**.

---

# 11. WHISPER

This is where the architecture gets clever.

Different voice platforms have different APIs.

For example:

```text
Vapi
  → add-message

OpenAI Realtime
  → conversation.item.create

Grok
  → response.create.instructions

Gemini Live
  → clientContent

Pipecat
  → context frame

LiveKit
  → chat/context update
```

Supafone normalizes these.

Conceptually:

```text
                SUPERVISOR
                    │
             "Do not confirm"
                    │
                    ▼
            ┌───────────────┐
            │ Adapter Layer │
            └───────┬───────┘
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
      Vapi       OpenAI        Gemini
   add-message   realtime     clientContent
```

The current provider matrix explicitly documents provider-specific watcher delivery mechanisms. ([GitHub][2])

This is an important engineering concept:

> **Canonical internal control → provider-specific adapter.**

That's exactly the sort of abstraction you should recognize from LangGraph/ADK tooling.

---

# 12. Why the supervisor must be off the critical path

Suppose your voice agent has:

```text
Latency budget = 500 ms
```

If you do:

```text
Caller
 ↓
Voice Agent
 ↓
Supervisor
 ↓
LLM
 ↓
Voice Agent
 ↓
TTS
 ↓
Caller
```

you potentially add huge latency.

Instead:

```text
                  ┌──── Supervisor
                  │
Caller → Agent ───┤
          │       │
          │       └── async
          ▼
        Response
```

The primary agent continues.

Supervisor:

```text
timeout
   ↓
no response
   ↓
ignore
   ↓
call continues
```

That's called **degrade-safe supervision**.

The repository explicitly states that the supervisor is timeout-bounded and off the hot path so a failed supervisor cannot take down the underlying call. ([GitHub][2])

---

# 13. This is very similar to a Verifier architecture

This is where your agent expertise becomes useful.

You already know:

```text
Generator
    ↓
Output
    ↓
Verifier
```

Supafone applies the same concept to voice.

```text
               GENERATOR
                  │
                  ▼
             Voice Agent
                  │
                  ▼
              Response
                  │
                  ▼
              SUPERVISOR
                  │
             ┌────┴─────┐
             │          │
           Good        Bad
             │          │
             ▼          ▼
          Continue    Correct
```

So you can explain it as:

> "Supafone applies an external generator/verifier architecture to real-time voice agents."

That is a strong technical explanation.

---

# 14. Supafone vs Vapi

Don't say:

> "Supafone is just another Vapi."

That's too simplistic.

Use this:

| Capability                 | Vapi                | Supafone |
| -------------------------- | ------------------- | -------- |
| Voice-agent runtime        | ⭐⭐⭐⭐⭐               | ⭐⭐⭐⭐     |
| Telephony                  | ⭐⭐⭐⭐⭐               | ⭐⭐⭐⭐⭐    |
| Agent creation             | ⭐⭐⭐⭐⭐               | ⭐⭐⭐⭐⭐    |
| Voice providers            | ⭐⭐⭐⭐⭐               | ⭐⭐⭐⭐     |
| Supervisor                 | Limited/not primary | ⭐⭐⭐⭐⭐    |
| Cross-platform supervision | ❌                   | ⭐⭐⭐⭐⭐    |
| QA                         | ⭐⭐⭐⭐                | ⭐⭐⭐⭐⭐    |
| Open source SDK            | ❌                   | ✅        |
| BYOK                       | ✅                   | ✅        |
| Managed infrastructure     | ✅                   | ✅        |

The Supafone website itself positions the Supervisor as something that can sit **beside an existing stack rather than replacing it**. ([Supafone Labs][1])

---

# 15. Supafone vs LangGraph

This distinction is critical.

### LangGraph

```text
                  Graph
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    Node A       Node B      Node C
       │           │           │
       └────────── State ──────┘
```

LangGraph controls:

* state
* nodes
* edges
* checkpoints
* routing
* execution

### Supafone Supervisor

```text
               Voice Agent
                    │
             live execution
                    │
                    ▼
              Supafone
                    │
             observes state
                    │
             generates advice
                    │
                    ▼
               Voice Agent
```

So:

**LangGraph controls the graph.**

**Supafone observes and influences the running agent.**

---

# 16. Supafone vs Google ADK

Same distinction.

Google ADK:

```text
Root Agent
   │
   ├── Research Agent
   ├── Tool Agent
   ├── RAG Agent
   └── Specialist Agent
```

That's **agent orchestration**.

Supafone:

```text
Primary Voice Agent
       │
       ▼
Supervisor
       │
       ▼
Runtime correction
```

That's **agent supervision**.

So you can say:

> "ADK and LangGraph answer 'how do I orchestrate agents?' Supafone additionally answers 'how do I supervise a voice agent while it is running?'"

---

# 17. Agent Factory

The other major Supafone capability is **Agent Factory**.

Instead of manually configuring:

```text
phone number
+
STT
+
LLM
+
TTS
+
prompt
+
tools
+
routing
+
knowledge
+
recording
+
QA
```

Supafone exposes a unified contract.

```text
                Agent Factory
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Agent        Number        Voice
        │            │            │
        ├────────────┼────────────┤
        ▼            ▼            ▼
      Tools       Knowledge      Stages
```

The website describes the Agent Factory as turning a job into an editable prompt, stages, tools, voice, routing and safeguards. ([Supafone Labs][1])

---

# 18. Multi-stage agents

This is another important idea.

Instead of:

```text
ONE HUGE PROMPT

"You are a receptionist and you must..."
```

Supafone supports stages:

```text
                    CALL
                     │
                     ▼
                  INTAKE
                     │
                     ▼
                QUALIFICATION
                     │
                     ▼
                 SCHEDULING
                     │
                     ▼
                CONFIRMATION
```

This is conceptually similar to a graph:

```text
START
  ↓
INTAKE
  ↓
QUALIFY
  ↓
SCHEDULE
  ↓
CONFIRM
  ↓
END
```

So if someone asks:

> "Is this basically LangGraph?"

You can answer:

**The multi-stage flow resembles graph orchestration, but Supafone is a voice-agent product/runtime rather than a general-purpose graph execution framework.**

---

# 19. Knowledge / RAG

Supafone can ground agents in business knowledge.

Conceptually:

```text
                 Documents
                    │
                    ▼
             Knowledge Base
                    │
                    ▼
                Retrieval
                    │
                    ▼
Voice Agent ───── Context
```

So it has RAG-like functionality, but again:

> **Supafone isn't trying to be a general-purpose RAG framework like your OpenSearch + embeddings + LangGraph architecture.**

It's providing knowledge grounding as part of a voice-agent product.

---

# 20. Campaigns

Supafone also moves beyond a single phone call.

Think:

```text
              Campaign
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      Lead 1    Lead 2    Lead 3
        │         │         │
       Call      Call      Call
        │         │         │
        ▼         ▼         ▼
       QA        QA        QA
```

The MCP integration is particularly interesting because Supafone exposes campaigns, calls, monitoring, hosted agents and other operations through an MCP server. ([GitHub][2])

That means:

```text
Claude / MCP Client
        │
        ▼
Supafone MCP
        │
        ├── Create agent
        ├── Create campaign
        ├── Add leads
        ├── Launch
        ├── Monitor
        └── Inspect calls
```

For an **Agentic AI architecture workshop**, this is worth mentioning.

---

# 21. MCP angle

You already know MCP, so think:

```text
                    LLM
                     │
                     ▼
                MCP Client
                     │
                     ▼
              Supafone MCP
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Agents      Campaigns      Calls
```

Instead of building a custom orchestration UI, an agent can interact with Supafone through tools.

Example natural language:

```text
"Create an outbound campaign
for these 100 leads using my
sales agent."
```

MCP translates that into operations.

That's a nice **agent-to-agent/platform** story for your presentation.

---

# 22. Post-call analysis

Supafone doesn't stop when the call ends.

It can classify calls against objectives.

For example:

```text
CALL ENDS
   │
   ▼
Post-call analysis
   │
   ├── Objective achieved?
   ├── Policy followed?
   ├── Tool succeeded?
   ├── Customer satisfied?
   └── Failure reasons
```

Example conceptual result:

```json
{
  "achieved": true,
  "criteria": {
    "identity_verified": true,
    "appointment_booked": true,
    "policy_followed": true
  },
  "failure_reasons": []
}
```

The current SDK README documents `post_call_analysis` and objective-based call classification. ([GitHub][2])

---

# 23. QA is especially interesting

Supafone can generate adversarial voice-agent scenarios from your agent's own prompt.

For example, your agent is:

```text
Dental appointment agent
```

The QA engine can generate:

```text
Scenario 1:
Angry customer

Scenario 2:
Customer changes appointment twice

Scenario 3:
Customer asks forbidden question

Scenario 4:
Customer switches language

Scenario 5:
Customer gives ambiguous date
```

Then:

```text
Scenario
   ↓
Mock call
   ↓
Voice Agent
   ↓
Judge
   ↓
PASS / FAIL
```

The QA system also supports supervised vs unsupervised A/B runs to measure supervision lift. ([GitHub][3])

---

# 24. This creates a complete lifecycle

This is the architecture I would show in your workshop:

```text
                    SUPAFONE
                       │
        ┌──────────────┼───────────────┐
        │              │               │
        ▼              ▼               ▼
      BUILD          TEST           DEPLOY
        │              │               │
        ▼              ▼               ▼
   Agent Factory   QA Scenarios    Phone/WebRTC
        │              │               │
        ▼              ▼               ▼
      Configure      Evaluate        Run Calls
        │                              │
        └──────────────┬───────────────┘
                       ▼
                  SUPERVISE
                       │
                       ▼
                    ANALYZE
                       │
                       ▼
                   OPTIMIZE
```

That's much bigger than simply "voice API."

---

# 25. The full production architecture

For an enterprise architecture, I'd draw:

```text
                       ┌──────────────────────────┐
                       │       APPLICATION        │
                       │                          │
                       │ CRM / Web / Mobile / ERP │
                       └────────────┬─────────────┘
                                    │
                                    ▼
                       ┌──────────────────────────┐
                       │      VOICE AGENT         │
                       │                          │
                       │ Vapi / LiveKit /         │
                       │ Pipecat / Realtime       │
                       └────────────┬─────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
                 STT               LLM               TTS
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    │
                                    ▼
                         ┌────────────────────┐
                         │ SUPAFONE SUPERVISOR│
                         │                    │
                         │ Observe            │
                         │ State              │
                         │ Tools              │
                         │ Policy             │
                         │ Language           │
                         │ Outcome            │
                         └─────────┬──────────┘
                                   │
                            silent directive
                                   │
                                   ▼
                              Voice Agent
```

And outside the call:

```text
              ┌─────────────────────────┐
              │     Supafone Platform   │
              │                         │
              │ Agent Factory           │
              │ Knowledge               │
              │ Campaigns               │
              │ QA                      │
              │ Post-call analysis      │
              │ Audit logs              │
              │ MCP                     │
              └─────────────────────────┘
```

---

# 26. The 5 layers you should remember

If someone asks you:

> "What exactly is Supafone?"

Answer with these five layers:

### Layer 1 — Agent Factory

Create/configure agents.

### Layer 2 — Voice Runtime

Phone/WebRTC, STT, LLM, TTS, tools.

### Layer 3 — Supervisor

Observe live calls and dynamically coach the agent.

### Layer 4 — QA / Evaluation

Test agents and measure reliability.

### Layer 5 — Operations

Campaigns, numbers, knowledge, logs, transcripts, call evidence and MCP.

That's a much more accurate description than "Vapi competitor."

---

# 27. The killer use case

Here's the example I'd use in your workshop.

### Customer support agent

Customer:

> "I was charged $500 twice."

Agent:

```text
I'll check your account.
```

Agent calls:

```text
get_transactions()
```

Result:

```json
{
  "transactions": [
    {"amount": 500},
    {"amount": 500}
  ]
}
```

Agent says:

> "Yes, I see two charges."

So far good.

Then customer says:

> "Can you refund one?"

Agent calls:

```text
refund()
```

Result:

```text
FAILED
```

Without supervisor:

```text
Agent:
"Your refund has been processed."
```

Bad.

With Supafone:

```text
                 TOOL RESULT
                     │
                  FAILED
                     │
                     ▼
              SUPERVISOR
                     │
                     ▼
       "Refund failed. Do not confirm
        completion. Explain failure."
                     │
                     ▼
                  AGENT
                     │
                     ▼
"I wasn't able to complete the refund.
Let me retry or connect you to support."
```

**That's the entire Supafone story in one example.**

---

# 28. What happens if Supafone fails?

This is an important production question.

Suppose:

```text
Supervisor LLM
     ↓
TIMEOUT
```

The call shouldn't die.

Architecture:

```text
Voice Agent ───────────────► Customer
      │
      │
      └────► Supervisor
                  │
                  X timeout

                  ↓
             No directive

Voice Agent continues
```

This is what Supafone calls **degrade-safe** supervision. ([GitHub][2])

For enterprise architecture, that's a very important property.

---

# 29. Multilingual supervision

Another interesting feature:

```text
Caller:
Hola, necesito cancelar mi póliza.
```

Supervisor detects:

```text
language = Spanish
intent = cancellation
```

Then sends guidance in Spanish:

```text
"No confirmes la cancelación hasta
que la API confirme éxito."
```

So the supervisor isn't merely observing English transcripts.

The current implementation includes multilingual live transcription and language-aware coaching. ([GitHub][2])

---

# 30. The abstraction you should focus on as an engineer

From your LangGraph/ADK background, I would focus less on:

```text
How do I create a phone number?
```

and more on:

```text
How does Supafone create a
cross-provider control plane?
```

That's the technically interesting part.

Think:

```text
Provider A
     │
     ▼
Provider Adapter
     │
     ▼
Canonical Event
     │
     ▼
Supervisor Brain
     │
     ▼
Canonical Directive
     │
     ▼
Provider Adapter
     │
     ▼
Provider B
```

This is analogous to building an **Agent Registry / Agent Control Plane**.

And given your work around agent orchestration and registries, this is probably the most valuable architectural angle for you.

---

# 31. The provider adapter pattern

Conceptually:

```python
class VoiceProviderAdapter:

    def parse_event(self, event):
        ...

    def inject_instruction(self, instruction):
        ...
```

Then:

```python
class VapiAdapter(VoiceProviderAdapter):
    ...

class OpenAIRealtimeAdapter(VoiceProviderAdapter):
    ...

class GeminiLiveAdapter(VoiceProviderAdapter):
    ...

class LiveKitAdapter(VoiceProviderAdapter):
    ...
```

Your supervisor doesn't care.

It says:

```python
directive = supervisor.decide(state)

adapter.inject_instruction(directive)
```

That's the architectural abstraction.

---

# 32. Supafone's Cloud API

The current API includes endpoints around:

```text
/v1/signup
/v1/oracle/complete
/v1/models
/v1/tts
/v1/voices
/v1/stt
/v1/stt/live
/v1/usage
/v1/billing/balance
/v1/logs
/v1/qa/generate
/v1/qa/suite
/v1/calls/classify
```

So it isn't only a supervisor API.

It's effectively a **voice-agent platform API + supervisor API + QA API**. ([GitHub][2])

---

# 33. Python mental model

At the highest level:

```python
import supafone_labs

brain = supafone_labs.supercharge(
    my_agent,
    scenario="customer_support"
)

result = await brain.observe(raw_event)

if result.actions:
    send_to_voice_platform(
        result.actions
    )
```

The important conceptual API is:

```text
observe(event)
       ↓
supervisor reasoning
       ↓
actions
       ↓
provider-specific injection
```

---

# 34. Hosted vs BYOK

There are two deployment philosophies.

### Managed

```text
Supafone
 ├── Telephony
 ├── STT
 ├── TTS
 ├── Models
 ├── Agent
 └── Supervisor
```

### BYOK

```text
Your infrastructure
 ├── Twilio
 ├── Vapi
 ├── OpenAI
 ├── Deepgram
 └── ElevenLabs

             +
             
         Supafone
         Supervisor
```

Supafone explicitly supports both approaches. ([GitHub][2])

---

# 35. Where Supafone fits relative to your stack

If I were designing an enterprise architecture with technologies you already work with:

```text
                    Enterprise AI Platform
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
        Text Agents      Voice Agents       Workflows
             │                │                │
             │                ▼                │
             │        Vapi/LiveKit/etc.       │
             │                │                │
             │                ▼                │
             │        Supafone Supervisor      │
             │                │                │
             └────────────────┼────────────────┘
                              │
                       Agent Control Plane
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
                MCP        Registry       Eval
```

Then:

```text
LangGraph
   +
Google ADK
   +
MCP
   +
Agent Registry
   +
Supafone
```

can coexist.

Supafone isn't necessarily something you'd replace LangGraph with.

---

# 36. The "expert answer" if someone asks you tomorrow

If someone says:

> **"What is Supafone Labs?"**

I'd answer:

> **"Supafone Labs is a voice-agent platform with an interesting supervisory architecture. It can either host the entire voice-agent stack or sit alongside an existing platform like Vapi, LiveKit, Pipecat, OpenAI Realtime or Gemini Live. Its differentiator is the Supervisor — a second, asynchronous reasoning process that observes the live conversation, tool state and outcomes and injects silent, provider-native corrective instructions into the primary voice agent. Around that it provides agent provisioning, telephony, knowledge, campaigns, QA, post-call analysis, auditability and MCP."**

That's a strong technical answer.

---

# 37. The 30-second version

If you have only 30 seconds:

> **"Think of Supafone as an AgentOps/control layer for voice agents. Vapi and similar platforms primarily run the voice agent. Supafone can run one too, but its unique idea is a second mind that watches the live call and silently coaches the primary agent when it detects problems. It also provides agent creation, telephony, knowledge, campaigns, QA and post-call evaluation."**

---

# 38. The 3 diagrams I would put in your presentation

### Slide 1 — Traditional

```text
Caller
  ↓
Voice Agent
  ↓
STT → LLM → TTS
  ↓
Caller
```

### Slide 2 — Supafone

```text
                   Supervisor
                  /           \
              observe       whisper
                 ↓             ↓
Caller → Voice Agent ──────────┘
             ↓
            STT
             ↓
            LLM
             ↓
            TTS
```

### Slide 3 — Enterprise

```text
                  AI APPLICATION
                        │
           ┌────────────┴────────────┐
           │                         │
       Text Agents              Voice Agents
           │                         │
     LangGraph/ADK           Vapi/LiveKit/etc.
                                     │
                                     ▼
                              SUPAFONE
                              SUPERVISOR
                                     │
                    ┌────────────────┼──────────────┐
                    ▼                ▼              ▼
                   QA             Analytics        MCP
```

---

# 39. What I would learn tonight

Since your workshop is **tomorrow**, don't try to memorize the entire SDK.

Focus on these **10 concepts in this order**:

```text
1. Voice Agent architecture
       ↓
2. Talker vs Supervisor
       ↓
3. TAP → THINK → WHISPER
       ↓
4. Off-path / async supervision
       ↓
5. Silent provider-native injection
       ↓
6. Provider adapter architecture
       ↓
7. Agent Factory
       ↓
8. QA + post-call evaluation
       ↓
9. MCP integration
       ↓
10. Managed vs BYOK deployment
```

If you understand those ten, you will understand **the architecture**, not just the API.

The official repository is the best source for the implementation details, provider matrix, SDK examples, QA APIs, MCP server and architecture. [Supafone Labs GitHub repository](https://github.com/samthedataman/supafone-labs?utm_source=chatgpt.com) [Supafone Labs website](https://labs.supafone.ai/?utm_source=chatgpt.com)

### One important correction to my earlier answer

After reviewing the current repository, I would **not describe Supafone simply as "Vapi + supervisor."** It now has a full **Agent Factory/managed-agent path**, including numbers, voices, tools, knowledge, campaigns and QA. The **Supervisor is its most distinctive architectural feature**, but it's only one of its two major pillars. ([GitHub][2])

If you want to prepare effectively for tomorrow, the next useful step is a **hands-on 90-minute workshop path**: **install → API key → build one voice agent → connect Vapi → enable Supafone Supervisor → deliberately make the agent fail → watch the supervisor correct it → run QA → inspect logs → MCP integration**, with the exact Python/TypeScript code and what to say on each presentation slide.

[1]: https://labs.supafone.ai/ "Supafone Labs — the voice-agent framework behind Supafone"
[2]: https://github.com/samthedataman/supafone-labs?utm_source=chatgpt.com "GitHub - samthedataman/supafone-labs: Public SDKs for Supafone Labs, staged privately before release · GitHub"
[3]: https://github.com/samthedataman/supafone-labs/blob/main/gitbook/voice-qa-landscape.md?utm_source=chatgpt.com "supafone-labs/gitbook/voice-qa-landscape.md at main · samthedataman/supafone-labs · GitHub"
