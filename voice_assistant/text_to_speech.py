import logging
import elevenlabs
from openai import OpenAI
from deepgram import DeepgramClient, SpeakOptions
from elevenlabs.client import ElevenLabs
from cartesia import Cartesia
import pyaudio
import soundfile as sf
import json

from voice_assistant.local_tts_generation import generate_audio_file_melotts
def text_to_speech(model, api_key, text, output_file_path, local_model_path=None):
    
    try:
        if model == 'openai':
            client = OpenAI(api_key=api_key)
            speech_response = client.audio.speech.create(
                model="tts-1",
                voice="fable",
                input=text
            )

            speech_response.stream_to_file(output_file_path)

        elif model == 'deepgram':
            client = DeepgramClient(api_key=api_key)
            options = SpeakOptions(
                model="aura-arcas-en", 
                encoding="linear16",
                container="wav"
            )
            SPEAK_OPTIONS = {"text": text}
            response = client.speak.v("1").save(output_file_path, SPEAK_OPTIONS, options)
        elif model == 'elevenlabs':
            ELEVENLABS_VOICE_ID = "Paul J."
            client = ElevenLabs(api_key=api_key)
            audio = client.generate(
                text=text, voice=ELEVENLABS_VOICE_ID, output_format="mp3_22050_32", model="eleven_turbo_v2"
            )
            elevenlabs.save(audio, output_file_path)
        elif model == "cartesia":

            client = Cartesia(api_key=api_key)
            voice_id = "f114a467-c40a-4db8-964d-aaba89cd08fa"#"a0e99841-438c-4a64-b679-ae501e7d6091"
            voice = client.voices.get(id=voice_id)
            model_id = "sonic-english"

            output_format = {
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 44100,
            }

            p = pyaudio.PyAudio()
            rate = 44100

            stream = None

            for output in client.tts.sse(
                model_id=model_id,
                transcript=text,
                voice_embedding=voice["embedding"],
                stream=True,
                output_format=output_format,
            ):
                buffer = output["audio"]

                if not stream:
                    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=rate, output=True)
                stream.write(buffer)

            stream.stop_stream()
            stream.close()
            p.terminate()

        elif model == "melotts":
            generate_audio_file_melotts(text=text, filename=output_file_path)
        elif model == 'local':
            with open(output_file_path, "wb") as f:
                f.write(b"Local TTS audio data")
        else:
            raise ValueError("Unsupported TTS model")
    except Exception as e:
        logging.error(f"Failed to convert text to speech: {e}")