import requests
from voice_assistant.config import Config


def generate_audio_file_melotts(text, language='EN', accent='EN-US', speed=1.0, filename=None):

    url = f"http://localhost:{Config.TTS_PORT_LOCAL}/generate-audio/"

    # Define the payload
    payload = {
        "text": text,
        "language": language,
        "accent": accent,
        "speed": speed
    }

    if filename:
        payload["filename"] = filename
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

if __name__ == "__main__":
    try:
        result = generate_audio_file_melotts(
            text="What is the purpose of life?",
            language="EN",
            accent="EN-US",
            speed=1.0,
            filename="my_custom_audio.wav"
        )
        print("Audio file generated successfully")
        print("File path:", result.get("file_path"))
    except requests.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")