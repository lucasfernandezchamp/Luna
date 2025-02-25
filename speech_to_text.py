import requests

class SpeechToText:
    def __init__(self, url, version, key):
        self.url  = url
        self.url += "/speechtotext/transcriptions:transcribe?api-version="+version
        self.headers = {
            "Ocp-Apim-Subscription-Key": key
        }

    def transcribe(self, audio_filepath: str):
        files = {
            "audio": open(audio_filepath, "rb"),
            "definition": (None, '{"locales":["en-US"]}', 'application/json'),
        }
        response = requests.post(self.url, headers=self.headers, files=files)

        if response.status_code == 200:
            json_reponse = response.json()
            text = json_reponse["combinedPhrases"][0]["text"]
            return {"text": text}
        else:
            response.raise_for_status()
            raise Exception("Error on the speech to text service")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    stt = SpeechToText(
            url = os.getenv("AZURE_COGNITIVE_ENDPOINT"),
            version = os.getenv("AZURE_COGNITIVE_VERSION"),
            key = os.getenv("AZURE_OPENAI_API_KEY")
        )
    print(stt.transcribe("ca3d8949-0e8c-4e57-abca-bea0d2332320.wav"))