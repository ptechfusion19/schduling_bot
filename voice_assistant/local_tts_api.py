from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from melo.api import TTS
from config import Config
import torch
import uuid

app = FastAPI()

class TextToSpeechRequest(BaseModel):
    text: str
    language: str = 'EN'
    accent: str = 'EN-US'
    speed: float = 1.0
    filename: str = Field(default_factory=lambda: f"{uuid.uuid4()}.wav")

def get_device():
    if torch.cuda.is_available():
        return 'cuda'
    elif torch.backends.mps.is_available():
        return 'mps'
    else:
        return 'cpu'
device = get_device() 
model = TTS(language='EN', device=device)
speaker_ids = model.hps.data.spk2id

@app.post("/generate-audio/")
def generate_audio(request: TextToSpeechRequest):
    if request.accent not in speaker_ids:
        raise HTTPException(status_code=400, detail="Invalid accent specified")
    
    try:
        output_filename = request.filename
        model.tts_to_file(request.text, speaker_ids[request.accent], output_filename, speed=request.speed)
        return {"message": "Audio file generated successfully", "file_path": output_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.TTS_PORT_LOCAL)