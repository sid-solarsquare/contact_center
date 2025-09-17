import os
import shutil
import json
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, APIRouter # Import APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

import main as analytics

app = FastAPI(
    title="Dialogue IQ - AI Analytics",
    description="An API to analyze call center audio recordings using Gemini.",
    version="1.0.0",
)

# Use an APIRouter to prefix all routes with /api
router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=analytics.AUDIO_DIR), name="audio")

config = analytics.load_config()

def get_audio_duration(filepath):
    try:
        if filepath.lower().endswith('.mp3'): audio = MP3(filepath)
        elif filepath.lower().endswith('.wav'): audio = WAVE(filepath)
        elif filepath.lower().endswith('.m4a'): audio = MP4(filepath)
        elif filepath.lower().endswith('.ogg'): audio = OggVorbis(filepath)
        else: return 0
        return round(audio.info.length / 60, 2)
    except Exception:
        return 0

@router.get("/list_audio", summary="List all available audio files") # Note: using router
def list_audio():
    supported_formats = ['.mp3', '.wav', '.m4a', '.ogg']
    audio_files = []
    try:
        for filename in os.listdir(analytics.AUDIO_DIR):
            if any(filename.lower().endswith(fmt) for fmt in supported_formats):
                file_path = os.path.abspath(os.path.join(analytics.AUDIO_DIR, filename))
                duration = get_audio_duration(file_path)
                audio_files.append({
                    "filename": filename,
                    "path": file_path,
                    "duration_mins": duration
                })
        return {"audio_files": audio_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_audio", summary="Analyze an audio file") # Note: using router
async def analyze_audio(audio_id: Optional[str] = Form(None), file: Optional[UploadFile] = File(None)):
    if not audio_id and not file:
        raise HTTPException(status_code=400, detail="You must provide either an 'audio_id' or upload a 'file'.")

    if file:
        audio_path = os.path.join(analytics.AUDIO_DIR, file.filename)
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    else:
        audio_path = os.path.abspath(os.path.join(analytics.AUDIO_DIR, audio_id))
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail=f"Audio file with id '{audio_id}' not found.")

    analysis_result = analytics.analyze_call(audio_path, config)

    if "error" in analysis_result:
        raise HTTPException(status_code=500, detail=analysis_result["error"])

    return JSONResponse(content=analysis_result)

# Include the router in your main app
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
