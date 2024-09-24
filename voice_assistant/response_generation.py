from openai import OpenAI
from groq import Groq
import ollama
import logging
from voice_assistant.config import Config
from voice_assistant.agent_actions import *

def generate_response(model, api_key, chat_history, local_model_path=None):

    try:
        if model == 'openai':
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=Config.OPENAI_LLM,
                messages=chat_history
            )
            return response.choices[0].message.content
        elif model == 'groq':
            client = Groq(api_key=api_key)

            return run_conversation(chat_history, client)

        elif model == 'ollama':
            response = ollama.chat(
                model=Config.OLLAMA_LLM,
                messages=chat_history,
            )
            return response['message']['content']
        elif model == 'local':
            return "Generated response from local model"
        else:
            raise ValueError("Unsupported response generation model")
    except Exception as e:
        logging.error(f"Failed to generate response: {e}")
        return "Error in generating response"