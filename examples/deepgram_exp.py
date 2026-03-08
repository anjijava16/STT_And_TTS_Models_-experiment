from deepgram import DeepgramClient, AnalyzeOptions

DEEPGRAM_API_KEY = "xxxx"

TEXT =  {
    "buffer": "Enter your text here."
}

def main():
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)

        options = AnalyzeOptions(
            language="en",
            summarize="v2",
            topics=True,
            intents=True,
            sentiment=True,
        )

        response = deepgram.read.analyze.v("1").analyze_text(
            TEXT,
            options,
        )

        print(response.to_json(indent=4))

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
