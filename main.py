import logging
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from colorama import Fore, init
from voice_assistant.audio import record_audio, play_audio
from voice_assistant.transcription import transcribe_audio
from voice_assistant.response_generation import generate_response
from voice_assistant.text_to_speech import text_to_speech
from voice_assistant.utils import delete_file
from voice_assistant.config import Config
from voice_assistant.api_key_manager import get_transcription_api_key, get_response_api_key, get_tts_api_key
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from datetime import datetime

templates = Jinja2Templates(directory="templates")



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

init(autoreset=True)
app = FastAPI()
active_users = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = []
        logging.info(Fore.GREEN + f"Client connected: {websocket}" + Fore.RESET)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logging.info(Fore.RED + f"Client disconnected: {websocket}" + Fore.RESET)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/assistant")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        today = datetime.now().date()
        chat_history = [{
            "role": "system",
            "content": f"""You are Ptechfusion, a meeting scheduling assistant dedicated to helping users schedule meetings with doctors. 
            You have access to doctors' show_available_doctors, get_available_slots and schedule_appointment for meetings. Your task is 
            to assist users by suggesting users the doctor on basis of their issues, providing available slots on the basis of the given 
            date and time range by users and scheduling meetings with the doctors on the exact datetime they give you. Always begin by asking 
            for the user's name before proceeding, always ask the date and prefered time range from user before showing availaible slots 
            for appointmens and the exact date and time for the appointment before scheduling appointment. Remember that today's date is
            {today}. And be very consistent with your time format use 24 hr time format without AM/PM."""
            }]
        await websocket.send_text("Please start speaking...")
        while True:
            transcription_api_key = get_transcription_api_key()
            
            audio_data = await websocket.receive_bytes()

            with open(Config.INPUT_AUDIO, "wb") as audio_file:
                audio_file.write(audio_data)

            print('audio recieved')
            user_input = transcribe_audio(Config.TRANSCRIPTION_MODEL, transcription_api_key, Config.INPUT_AUDIO, Config.LOCAL_MODEL_PATH)
            print(f"--------------\n{user_input}\n-------------------------")
            
            if not user_input:
                await websocket.send_text("Error: Unable to transcribe audio.")
                logging.error(Fore.RED + f"Transcription failed." + Fore.RESET)
                continue

            logging.info(Fore.GREEN + f"You said: {user_input}" + Fore.RESET)

            if "goodbye" in user_input.lower():
                await manager.send_message("Goodbye!", websocket)
                break

            chat_history.append({"role": "user", "content": user_input})

            response_api_key = get_response_api_key()
            print('generating response')
            response_text = generate_response(Config.RESPONSE_MODEL, response_api_key, chat_history, Config.LOCAL_MODEL_PATH)
            print('generated response')

            if not response_text:
                await websocket.send_text("Error: Unable to generate a response.")
                logging.error(Fore.RED + f"Response generation failed." + Fore.RESET)
                continue

            logging.info(Fore.CYAN + "Response: " + response_text + Fore.RESET)

            chat_history.append({"role": "assistant", "content": response_text})

            await manager.send_message(response_text, websocket)

            output_file = 'output.wav' if Config.TTS_MODEL not in ['openai', 'elevenlabs', 'melotts', 'cartesia'] else 'modeloutput.mp3'

            tts_api_key = get_tts_api_key()
            text_to_speech(Config.TTS_MODEL, tts_api_key, response_text, output_file, Config.LOCAL_MODEL_PATH)
            print('speaking response response')

            if os.path.exists(output_file):
                try:
                    with open(output_file, "rb") as audio_file:
                        audio_data = audio_file.read()
                        if len(audio_data) == 0:
                            logging.error(f"Error: {output_file} is empty")
                            await websocket.send_text(f"Error: {output_file} is empty")
                        else:
                            await websocket.send_bytes(audio_data)
                            logging.info(f"Sent audio file: {output_file}")
                except Exception as e:
                    logging.error(f"Error sending file: {e}")
                    await websocket.send_text(f"Error: Unable to send {output_file}")
            else:
                await websocket.send_text(f"Error: File {output_file} not found")

            print(f"Response spoken via {Config.TTS_MODEL}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logging.error(Fore.RED + f"An error occurred: {e}" + Fore.RESET)
        delete_file(Config.INPUT_AUDIO)
        if 'output_file' in locals() and os.path.exists(output_file):
            delete_file(output_file)
        time.sleep(1)