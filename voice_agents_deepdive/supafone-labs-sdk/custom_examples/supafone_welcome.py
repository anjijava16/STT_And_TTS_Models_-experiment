import json
import os

from supafone_labs import Supafone

# supervisor=True adds live guidance, QA, and call scoring.
# Set False to run only the base agent runtime.
supafone = Supafone(
    api_key=os.environ["SUPAFONE_API_KEY"],
    supervisor=True,
)

def resolve_env(value):
    if isinstance(value, dict):
        return {key: resolve_env(item) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_env(item) for item in value]
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ[value[2:-1]]
    return value

agent_config = resolve_env(json.loads("{\n  \"agentKey\": \"welcome-inbound-custom\",\n  \"agentType\": \"phone\",\n  \"style\": \"inbound\",\n  \"direction\": \"inbound\",\n  \"name\": \"welcome Receptionist\",\n  \"assistantName\": \"Custom\",\n  \"businessName\": \"welcome\",\n  \"agentPlatform\": {\n    \"mode\": \"supafone_managed\",\n    \"provider\": \"supafone\",\n    \"label\": \"Supafone Agent Factory\"\n  },\n  \"numberStrategy\": \"default_pool\",\n  \"numberPool\": \"default\",\n  \"premium\": false,\n  \"presetKey\": \"general_intake_receptionist\",\n  \"runtimeMode\": \"multi_stage\",\n  \"goal\": \"Understand the caller's request, use only approved information and tools, and complete the next verified action.\",\n  \"greeting\": \"Hi, thanks for calling. How can I help today?\",\n  \"systemPrompt\": \"You are a inbound custom voice agent.\\n\\nGoal:\\nUnderstand the caller's request, use only approved information and tools, and complete the next verified action.\\n\\nRules:\\n- Speak in short, natural turns.\\n- Ask one question at a time.\\n- Never invent prices, bookings, policies, availability, or outcomes.\\n- Only say an action succeeded after a tool or system confirms it.\\n- Escalate to a human for legal, medical, financial, safety, or angry-caller edge cases.\\n- Read Supafone self-healing whispers silently and adjust the next response without saying the whisper aloud.\",\n  \"language\": \"en\",\n  \"languageVoiceRouting\": false,\n  \"languageProfiles\": [\n    {\n      \"language\": \"en\",\n      \"languageHint\": \"en\"\n    }\n  ],\n  \"voice\": {\n    \"provider\": \"cartesia_sonic\",\n    \"voiceId\": \"f786b574-daa5-4673-aa0c-cbe3e8534c02\"\n  },\n  \"number\": {\n    \"search\": {\n      \"numberStrategy\": \"default_pool\",\n      \"numberPool\": \"default\",\n      \"premium\": false\n    },\n    \"telephony\": {\n      \"mode\": \"supafone_managed\",\n      \"provider\": \"supafone\"\n    }\n  },\n  \"telephony\": {\n    \"mode\": \"supafone_managed\",\n    \"provider\": \"supafone\",\n    \"numberStrategy\": \"default_pool\",\n    \"numberPool\": \"default\",\n    \"premium\": false,\n    \"label\": \"welcome-inbound-custom\"\n  },\n  \"recording\": {\n    \"enabled\": true,\n    \"recordAudio\": true,\n    \"consentRequired\": true,\n    \"announcement\": \"This call may be recorded for quality and training.\",\n    \"retentionDays\": 30,\n    \"storage\": \"supafone_managed\",\n    \"redactPii\": true\n  },\n  \"transcription\": {\n    \"enabled\": true,\n    \"provider\": \"supafone_managed\",\n    \"language\": \"multi\",\n    \"redactPii\": true,\n    \"diarization\": true,\n    \"timestamps\": true\n  },\n  \"artifacts\": {\n    \"recordings\": true,\n    \"transcripts\": true,\n    \"summaries\": true,\n    \"qaReports\": true,\n    \"logs\": true,\n    \"retentionDays\": 30\n  },\n  \"compliance\": {\n    \"consent_required\": true,\n    \"announcement\": \"This call may be recorded for quality and training.\"\n  },\n  \"tools\": {\n    \"callRouting\": true,\n    \"scheduling\": false,\n    \"sms\": false,\n    \"email\": false,\n    \"firmKnowledge\": true,\n    \"voicemail\": false,\n    \"emergencyEscalation\": false,\n    \"ivrNavigation\": false\n  },\n  \"labs\": {\n    \"enabled\": true,\n    \"supervisor\": true,\n    \"model\": \"supafone-labs-oracle\",\n    \"mode\": \"supafone_managed\",\n    \"managedInfrastructure\": true,\n    \"label\": \"welcome-inbound-custom\"\n  },\n  \"supervisor\": true,\n  \"metadata\": {\n    \"generated_by\": \"supafone-labs-builder\",\n    \"sdk_package\": \"supafone-labs\",\n    \"sdk_version\": \"0.5.3\",\n    \"agent_platform\": \"supafone\",\n    \"number_strategy\": \"default_pool\",\n    \"self_healing\": true\n  }\n}"))

result = supafone.labs.agents.create_inbound_with_number(agent_config)

if agent_config.get("websiteUrl") and result.get("agent", {}).get("id"):
    supafone.labs.agents.syncKnowledge(
        result["agent"]["id"],
        websiteUrl=agent_config["websiteUrl"],
    )

print({
    "agent_key": result.get("agent", {}).get("agent_key"),
    "number": result.get("number", {}).get("number", {}).get("phone_number"),
})