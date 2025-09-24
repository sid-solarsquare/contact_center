import google.generativeai as genai
import time
import json
import re
from typing import List, Dict


# --- HELPER FUNCTION FOR ROBUST JSON PARSING ---
def extract_json_from_text(text: str) -> str:
    """
    Finds and extracts the first valid JSON block (dict or list) from a string.
    Handles markdown code fences (```json ... ```) as well.
    """
    # First, try to find a JSON block within markdown fences
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1)

    # If no markdown fence, find the first '{' or '[' and the last '}' or ']'
    start_bracket = -1
    end_bracket = -1

    first_curly = text.find('{')
    first_square = text.find('[')

    if first_curly == -1 and first_square == -1:
        return None  # No JSON object or array found

    if first_curly != -1 and (first_square == -1 or first_curly < first_square):
        start_bracket = first_curly
        end_bracket = text.rfind('}')
    else:
        start_bracket = first_square
        end_bracket = text.rfind(']')

    if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
        return text[start_bracket: end_bracket + 1]

    return None  # Return None if no valid block is found

# --- Models ---
PRO_MODEL = 'models/gemini-2.5-pro'
FLASH_MODEL = 'models/gemini-2.5-flash-lite'

# --- File Upload Function ---
def upload_file_to_google_ai(file_path: str, retries=3, delay=5):
    """Uploads a file to the Google AI File API for use with Gemini."""
    print(f"Uploading file to Google AI: {file_path}...")
    for attempt in range(retries):
        try:
            audio_file = genai.upload_file(path=file_path)
            while audio_file.state.name == "PROCESSING":
                time.sleep(10)
                audio_file = genai.get_file(audio_file.name)

            if audio_file.state.name == "FAILED":
                raise Exception(f"File processing failed: {audio_file.uri}")

            print(f"File uploaded successfully: {audio_file.uri}")
            return audio_file
        except Exception as e:
            print(f"Upload attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("All upload retries failed.")
                return None


# --- Agent Functions ---

def agent_01_foundational_processor(audio_file_object) -> dict:
    """
    Processes the raw audio file to create the source-of-truth transcript.
    """
    print("🚀 Executing Agent 01: Foundational Audio Processing...")
    model = genai.GenerativeModel(PRO_MODEL)

    prompt = """
    You are a transcription and diarization expert for call centers. Process the attached audio file.
    Your task is to provide a structured JSON output of the conversation.
    1.  **Diarize**: Identify and label each speaker (e.g., "Agent", "Customer").
    2.  **Transcribe**: Provide two transcriptions for each segment: one in the original language spoken ('transcript_local_language') and one translated to English ('transcript_english').
    3.  **Name Identification**: If a speaker states their name (e.g., "My name is Priya"), replace their generic label (like "Customer") with their actual name for all their subsequent dialogue segments.
    4.  **Timestamps**: Include 'start_time' and 'end_time' in seconds for each segment.

    The final output must be a single JSON object with a key "transcript" which is a list of segment objects.
    Each segment object must have the keys: "speaker", "start_time", "end_time", "transcript_local_language", "transcript_english".
    """

    try:
        response = model.generate_content([prompt, audio_file_object], request_options={"timeout": 1200})
        raw_response_text = response.candidates[0].content.parts[0].text

        json_string = extract_json_from_text(raw_response_text)
        if not json_string:
            raise ValueError("Could not extract a valid JSON object from the model's response.")

        json_response = json.loads(json_string)
        print("✅ Agent 01: Complete.")
        return json_response
    except Exception as e:
        print(f"❌ Agent 01 Error: {e}")
        if 'raw_response_text' in locals():
            print("\n--- RAW RESPONSE FROM MODEL ---")
            print(raw_response_text)
            print("-----------------------------\n")
        return {}

## OLDER BLOCK OF CODE - REPLACED BY DETAILED VERSION BELOW
# async def agent_02a_persona_analyzer(transcript_data: dict) -> dict:
#     """
#     Analyzes the transcript to build a customer persona.
#     """
#     print("🚀 Executing Agent 02a: Persona Analyzer...")
#     model = genai.GenerativeModel(FLASH_MODEL)
#
#     prompt = f"""
#     Based on the following transcript, generate a JSON object for the customer persona.
#     Analyze only the dialogue from the customer.
#     The JSON must contain these keys:
#     - "price_sensitivity": A rating from 0 (not sensitive) to 5 (very sensitive), with a brief "justification".
#     - "quality_sensitivity": A rating from 0 to 5, with a "justification".
#     - "technical_proficiency": A rating from 0 (non-technical) to 5 (very technical), with a "justification".
#     - "sentiment": Choose one: 'Open', 'Excited', 'Un-excited', 'Rude', 'Not Interested'.
#     - "occupation_inference": Infer the occupation if possible ('Business', 'Salaried', 'Other', 'Unknown').
#     - "lead_source": Extract how they heard about the company, if mentioned.
#     - "brand_impression_pre_call": ('Good', 'Bad', 'Neutral', 'Unknown').
#
#     Transcript:
#     {json.dumps(transcript_data, indent=2)}
#     """
#     try:
#         response = await model.generate_content_async(prompt)
#         raw_response_text = response.candidates[0].content.parts[0].text
#
#         json_string = extract_json_from_text(raw_response_text)
#         if not json_string:
#             raise ValueError("Could not extract a valid JSON object from the model's response.")
#
#         json_response = json.loads(json_string)
#         print("✅ Agent 02a: Complete.")
#         return {"customer_persona": json_response}
#     except Exception as e:
#         print(f"❌ Agent 02a Error: {e}")
#         return {"customer_persona": {"error": str(e)}}

async def agent_02a_persona_analyzer(transcript_data: dict, persona_guidelines: Dict) -> dict:
    """
    Analyzes the transcript to build a detailed, evidence-backed customer persona
    based on a structured guideline.
    """
    print("🚀 Executing Agent 02a: Detailed Persona Analyzer...")
    model = genai.GenerativeModel(FLASH_MODEL)

    prompt = f"""
    You are an expert customer profiler and market researcher for a solar energy company.
    Your task is to analyze the provided call transcript and generate a detailed customer persona based on the structured `persona_guidelines`.

    INSTRUCTIONS:
    1.  Carefully read the entire `call_transcript`.
    2.  Iterate through each `category` and `point` in the `persona_guidelines`.
    3.  For EACH point, you MUST find evidence in the transcript.
    4.  Your final output must be a single JSON object with two top-level keys: "detailed_analysis" and "persona_summary".

    The "detailed_analysis" key should contain a list of objects, one for each category in the guidelines. Each category object should have:
    - "category": The name of the category (e.g., "Demographics & Customer Profile").
    - "points": A list of analysis objects for each point within that category. Each analysis object must contain:
        - "label": The human-readable label for the point (e.g., "Customer Type").
        - "value": Your inferred value based on the transcript (e.g., "Residential"). If no information is found, this MUST be "Not Mentioned".
        - "citation": The EXACT quote from the transcript that justifies your value. If no information, this should be null.
        - "commentary": A brief, one-sentence AI justification for your inference. If no information, this should be null.

    The "persona_summary" key should contain an object with:
    - "persona_tagline": A concise, one-sentence summary of the customer (e.g., "Cost-conscious homeowner seeking quick ROI").
    - "three_key_traits": A list of the three most important traits identified (e.g., ["Cost Savings", "High Urgency", "Price-Sensitive"]).
    - "lead_potential_score": Your final assessment of the lead's potential ('High', 'Medium', or 'Low').

    DATA:
    {{
        "persona_guidelines": {json.dumps(persona_guidelines, indent=2)},
        "call_transcript": {json.dumps(transcript_data, indent=2)}
    }}
    """
    try:
        response = await model.generate_content_async(prompt)
        raw_response_text = response.candidates[0].content.parts[0].text

        json_response = await parse_and_repair_json(raw_response_text, model)
        print("✅ Agent 02a: Complete.")
        return {"customer_persona": json_response}
    except Exception as e:
        print(f"❌ Agent 02a Error: {e}")
        return {"customer_persona": {"error": str(e)}}



async def agent_02b_sop_adherence(transcript_data: dict, sop_points: List[str]) -> dict:
    """
    Checks for Script Adherence with a more nuanced evaluation.
    """
    print("🚀 Executing Agent 02b: Script Adherence...")
    model = genai.GenerativeModel(FLASH_MODEL)

    prompt = f"""
    You are a strict but fair compliance officer. For each Script Point provided below, evaluate the agent's dialogue in the transcript.
    Analyze the INTENT behind the script point, not just the literal words.

    Your output must be a JSON object with a key "sop_adherence_report", which is a list of objects.
    Each object must contain:
    - "sop_point": The script point being checked.
    - "compliance": A string value from one of three options: "Fully Covered", "Partially Covered", or "Not Covered".
    - "evidence": The exact quote(s) from the agent's dialogue that apply. If not covered, this should be null.
    - "commentary": A brief, one-sentence explanation for your rating. For "Partially Covered", explain what was missing. For "Not Covered", state that the topic was not discussed.

    Example for a partial match: If the script says "Introduce yourself and the company" and the agent only says "My name is Alex", the compliance should be "Partially Covered" with commentary explaining the company name was omitted.

    Script Checklist:
    {json.dumps(sop_points)}

    Call Transcript:
    {json.dumps(transcript_data, indent=2)}
    """
    try:
        response = await model.generate_content_async(prompt)
        raw_response_text = response.candidates[0].content.parts[0].text

        json_string = extract_json_from_text(raw_response_text)
        if not json_string:
            raise ValueError("Could not extract a valid JSON object from the model's response.")

        json_response = json.loads(json_string)
        print("✅ Agent 02b: Complete.")
        return json_response
    except Exception as e:
        print(f"❌ Agent 02b Error: {e}")
        return {"sop_adherence_report": {"error": str(e)}}

async def agent_02c_lead_scoring(transcript_data: dict, questionnaire: Dict) -> dict:
    """
    Scores the lead based on a questionnaire and summarizes call quality.
    """
    print("🚀 Executing Agent 02c: Lead Scoring & Quality...")
    model = genai.GenerativeModel(FLASH_MODEL)

    prompt = f"""
    You are a sales manager analyzing a sales call. Based on the transcript and the business questionnaire, generate a final analysis.
    The output must be a single JSON object containing "lead_scoring_report" and "call_quality_summary".

    1.  **lead_scoring_report**: A list of objects. For each question in the questionnaire, find the answer in the transcript. Each object must have:
        - "question": The question from the questionnaire.
        - "answered": A boolean (true if an answer was found, false otherwise).
        - "citation": The exact quote from the customer that answers the question. Null if not answered.

    2.  **call_quality_summary**: An object containing:
        - "lead_hotness_score": A percentage from 0-100 on the likelihood to buy, with a "justification".
        - "overall_call_quality": 'Excellent', 'Good', 'Average', or 'Poor'.
        - "overall_lead_quality": 'Hot', 'Warm', or 'Cold'.
        - "greetings_check": Bool (Done/Not-Done).
        - "rapport_building_check":  Bool (Done/Not-Done).
        - "needs_analysis_check":  Bool (Done/Not-Done).
        - "product_recommendation_check":  Bool (Done/Not-Done).
        - "required_follow_up": If the agent promised some information or follow-up.

    Business Questionnaire:
    {json.dumps(questionnaire, indent=2)}

    Call Transcript:
    {json.dumps(transcript_data, indent=2)}
    """
    try:
        response = await model.generate_content_async(prompt)
        raw_response_text = response.candidates[0].content.parts[0].text

        json_string = extract_json_from_text(raw_response_text)
        if not json_string:
            raise ValueError("Could not extract a valid JSON object from the model's response.")

        json_response = json.loads(json_string)
        print("✅ Agent 02c: Complete.")
        return json_response
    except Exception as e:
        print(f"❌ Agent 02c Error: {e}")
        return {"lead_scoring_report": {"error": str(e)}, "call_quality_summary": {"error": str(e)}}


async def parse_and_repair_json(raw_text: str, model) -> dict:
    """
    Tries to parse JSON from text. If it fails, asks the model to repair it.
    """
    json_string = extract_json_from_text(raw_text)
    if not json_string:
        raise ValueError("Could not extract a JSON block from the text.")

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"⚠️ Initial JSON parsing failed: {e}. Attempting to repair...")

        # Create a repair prompt
        repair_prompt = f"""
        The following text is a malformed JSON string. Please fix the syntax errors (like missing commas or unescaped characters) and return only the corrected, valid JSON object.
        The error encountered was: {e}

        Malformed JSON:
        {json_string}
        """

        # Call the model to repair the JSON
        repair_response = await model.generate_content_async(repair_prompt)
        repaired_text = repair_response.candidates[0].content.parts[0].text

        # Try parsing the repaired text
        repaired_json_string = extract_json_from_text(repaired_text)
        if not repaired_json_string:
            raise ValueError("JSON repair failed. Could not extract JSON from the repair model's response.")

        print("✅ JSON successfully repaired and parsed.")
        return json.loads(repaired_json_string)


async def agent_rag_question_answerer(transcript_text: str, question: str) -> dict:
    """
    Answers a specific question based on the provided transcript.
    """
    print("🚀 Executing RAG Agent: Answering specific question...")
    model = genai.GenerativeModel(FLASH_MODEL)

    prompt = f"""
    You are an intelligent call analysis assistant. Your task is to answer a user's question based *only* on the provided call transcript.
    Do not use any external knowledge. If the answer is not found in the transcript, state that clearly.
    Provide a concise and direct answer.

    --- TRANSCRIPT ---
    {transcript_text}
    --- END TRANSCRIPT ---

    QUESTION: "{question}"

    ANSWER:
    """
    try:
        response = await model.generate_content_async(prompt)
        response_text = response.candidates[0].content.parts[0].text
        print("✅ Agent: Complete.")
        return {"answer": response_text}
    except Exception as e:
        print(f"❌ RAG Agent Error: {e}")
        return {"answer": f"Sorry, an error occurred while processing your question: {e}"}