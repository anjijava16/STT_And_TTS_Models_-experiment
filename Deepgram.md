Yes ✅ **Deepgram supports both STT and TTS.**

### Deepgram capabilities

| Feature                        | Supported | Example models  |
| ------------------------------ | --------- | --------------- |
| **STT (Speech → Text)**        | ✅ Yes     | Nova-3, Flux    |
| **TTS (Text → Speech)**        | ✅ Yes     | Aura-2 voices   |
| **Speech-to-Speech pipelines** | ✅ Yes     | STT → LLM → TTS |

Deepgram provides APIs for **speech-to-text, text-to-speech, and full voice-agent pipelines**, allowing developers to build real-time voice apps with a single platform. ([Deepgram][1])

For example:

```
User speaks
   ↓
Deepgram STT (Nova-3)
   ↓
LLM (GPT / Claude / etc.)
   ↓
Deepgram TTS (Aura-2)
   ↓
User hears response
```

### Quick comparison of the tools you mentioned

| Platform   | STT            | TTS |
| ---------- | -------------- | --- |
| Deepgram   | ✅              | ✅   |
| AWS        | ✅              | ✅   |
| AssemblyAI | ✅              | ❌   |
| Cartesia   | ❌              | ✅   |
| ElevenLabs | ⚠️ limited STT | ✅   |

💡 **Many voice-agent startups use this combo:**

* **Deepgram → STT**
* **GPT / Claude → reasoning**
* **ElevenLabs or Cartesia → TTS**

But you **can also use only Deepgram for both STT and TTS**.

---

If you want, I can also show you **the top 10 companies that provide BOTH STT + TTS (best for voice agents in 2026)**.

[1]: https://deepgram.com/?utm_source=chatgpt.com "Enterprise Voice AI: STT, TTS & Agent APIs | Deepgram"
