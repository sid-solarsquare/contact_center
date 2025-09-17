import os
import asyncio
import json
import yaml
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Import your existing agent and parser logic
from backend.gemini_agents import (
    upload_file_to_google_ai,
    agent_01_foundational_processor,
    agent_02a_persona_analyzer,
    agent_02b_sop_adherence,
    agent_02c_lead_scoring,
    agent_rag_question_answerer
)
from backend.file_parser import (
    parse_questionnaire_yaml,
    transcript_available
)

# --- Pydantic Models for request bodies ---
class QuestionRequest(BaseModel):
    transcript_text: str
    question: str

# --- App Initialization ---
app = FastAPI()

# --- CORS Configuration ---
# Allows the frontend (running on a different port) to communicate with this backend
origins = ["*"]  # In production, restrict this to your frontend's domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load API Key ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=api_key)

# --- Define file paths ---
INPUTS_DIR = Path(__file__).parent / "inputs"
SOP_PATH = INPUTS_DIR / "sop_scheduling_call.yaml"
QUESTIONNAIRE_PATH = INPUTS_DIR / "questionnaire.yaml"
TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = Path(__file__).parent / "../outputs"


# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "Call Analytics API is running."}


@app.get("/api/sop")
def get_sop():
    """Endpoint to read and return the current SOP YAML file."""
    try:
        with open(SOP_PATH, 'r') as f:
            sop_data = yaml.safe_load(f)
        return sop_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="SOP file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-audio")
async def process_audio_endpoint(audio: UploadFile = File(...)):
    """
    Main endpoint to process an uploaded audio file and return a full analysis.
    """
    # 1. Save uploaded audio file temporarily
    audio_path = TEMP_DIR / audio.filename
    with open(audio_path, "wb") as buffer:
        buffer.write(await audio.read())

    # 2. Parse SOP and Questionnaire from server-side files
    try:
        with open(SOP_PATH, 'r') as f:
            sop_data = yaml.safe_load(f)
            sop_points = [item['point'] for item in sop_data.get('sop_checklist', [])]

        questionnaire = parse_questionnaire_yaml(str(QUESTIONNAIRE_PATH))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing config files: {e}")

    # 3. Run the full pipeline
    try:
        # Step 1: Foundational Analysis
        audio_file_object = upload_file_to_google_ai(str(audio_path))
        if not audio_file_object:
            raise HTTPException(status_code=500, detail="Failed to upload audio file to Google AI.")

        older_transcript = transcript_available(filename=audio.filename, transcript_name="transcript", output_path=OUTPUT_DIR)
        print ("Checking for older transcript", type(older_transcript))
        if older_transcript is not None:
            transcript_data = older_transcript.get('transcript_data', {})
            print("Got older transcript data")
        else:
            transcript_data = agent_01_foundational_processor(audio_file_object)
            if not transcript_data or "transcript" not in transcript_data:
                raise HTTPException(status_code=500, detail="Failed to get a valid transcript.")

            with open(OUTPUT_DIR / (Path(audio.filename).stem + "_transcript.json"), 'w') as f:
                json.dump(transcript_data, f)

        # Step 2: Run enrichment agents in parallel
        enrichment_tasks_names = ["Persona Analysis", "SOP Adherence", "Lead Scoring"]
        # enrichment_results_old = [
        #     transcript_available(
        #         filename=audio.filename,
        #         transcript_name=name,
        #         output_path=OUTPUT_DIR
        #     ) for name in enrichment_tasks_names]
        #
        # # Check if all are not None
        # if not all(result is not None for result in enrichment_results_old):
        enrichment_tasks = [
            agent_02a_persona_analyzer(transcript_data),
            agent_02b_sop_adherence(transcript_data, sop_points),
            agent_02c_lead_scoring(transcript_data, questionnaire)
        ]
        enrichment_results = await asyncio.gather(*enrichment_tasks)

        # Step 3: Aggregate results
        final_call_record = {"source_audio_file": audio.filename}
        final_call_record.update(transcript_data)
        for index, result in enumerate(enrichment_results):
            final_call_record.update(result)
            with open(OUTPUT_DIR / (Path(audio.filename).stem + f"_{enrichment_tasks_names[index]}.json"), 'w') as f:
                json.dump(transcript_data, f)

        # 4. Cleanup
        os.remove(audio_path)
        genai.delete_file(audio_file_object.name)

        return final_call_record

    except Exception as e:
        # Ensure cleanup happens even on error
        if 'audio_file_object' in locals() and audio_file_object:
            genai.delete_file(audio_file_object.name)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {e}")

@app.get("/api/questionnaire") # <-- NEW ENDPOINT
def get_questionnaire():
    """Endpoint to read and return the current Questionnaire YAML file."""
    try:
        with open(QUESTIONNAIRE_PATH, 'r') as f:
            questionnaire_data = yaml.safe_load(f)
        return questionnaire_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Questionnaire file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask-question") # <-- NEW ENDPOINT
async def ask_question(request: QuestionRequest):
    """Endpoint to answer a specific question based on a transcript."""
    try:
        result = await agent_rag_question_answerer(request.transcript_text, request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {e}")

