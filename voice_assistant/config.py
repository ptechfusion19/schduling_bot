import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Model selection
    TRANSCRIPTION_MODEL = 'groq'
    RESPONSE_MODEL = 'groq' 
    TTS_MODEL = 'openai' 

    # LLM Selection
    OLLAMA_LLM="llama3:8b"
    GROQ_LLM="llama3-groq-70b-8192-tool-use-preview"#"llama3-8b-8192"
    OPENAI_LLM="gpt-4o"

    # API keys and paths
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH")
    CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
    TTS_PORT_LOCAL = 5150
    INPUT_AUDIO = "test.mp3"

    @staticmethod
    def validate_config():
        if Config.TRANSCRIPTION_MODEL not in ['openai', 'groq', 'deepgram', 'fastwhisperapi', 'local']:
            raise ValueError("Invalid TRANSCRIPTION_MODEL. Must be one of ['openai', 'groq', 'deepgram', 'fastwhisperapi', 'local']")
        if Config.RESPONSE_MODEL not in ['openai', 'groq', 'ollama', 'local']:
            raise ValueError("Invalid RESPONSE_MODEL. Must be one of ['openai', 'groq', 'local']")
        if Config.TTS_MODEL not in ['openai', 'deepgram', 'elevenlabs', 'melotts', 'cartesia', 'local']:
            raise ValueError("Invalid TTS_MODEL. Must be one of ['openai', 'deepgram', 'elevenlabs', 'melotts', 'cartesia', 'local']")

        if Config.TRANSCRIPTION_MODEL == 'openai' and not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI models")
        if Config.TRANSCRIPTION_MODEL == 'groq' and not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required for Groq models")
        if Config.TRANSCRIPTION_MODEL == 'deepgram' and not Config.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is required for Deepgram models")

        if Config.RESPONSE_MODEL == 'openai' and not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI models")
        if Config.RESPONSE_MODEL == 'groq' and not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required for Groq models")

        if Config.TTS_MODEL == 'openai' and not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI models")
        if Config.TTS_MODEL == 'deepgram' and not Config.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is required for Deepgram models")
        if Config.TTS_MODEL == 'elevenlabs' and not Config.ELEVENLABS_API_KEY:
            raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs models")
        if Config.TTS_MODEL == 'cartesia' and not Config.CARTESIA_API_KEY:
            raise ValueError("CARTESIA_API_KEY is required for Cartesia models")