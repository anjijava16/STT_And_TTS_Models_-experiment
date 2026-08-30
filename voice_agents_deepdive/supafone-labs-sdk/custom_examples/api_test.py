import asyncio
import json
import websockets

async def test_retell_llm():
    uri = "ws://localhost:8087/llm-websocket/test-call-123"
    async with websockets.connect(uri) as ws:
        # Read the config message sent by the server
        config = await ws.recv()
        print("Config:", config)

        # Send a mock "response_required" message (like Retell would)
        mock_message = {
            "interaction_type": "response_required",
            "response_id": "resp-001",
            "transcript": [
                {"role": "user", "content": "I need legal help."},
                {"role": "agent", "content": "Sure, tell me more."}
            ],
            "call_id": "test-call-123"  # optional, will be set by server
        }
        await ws.send(json.dumps(mock_message))

        # Wait for the response from your server
        response = await ws.recv()
        print("Response:", response)

        # Optionally send a reminder or end message
        # ...

if __name__ == "__main__":
    asyncio.run(test_retell_llm())