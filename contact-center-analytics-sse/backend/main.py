import os
import google.generativeai as genai
import argparse
import asyncio
import json
from dotenv import load_dotenv
from pathlib import Path
from tqdm import tqdm

from file_parser import parse_sop_pdf, parse_questionnaire_yaml
from gemini_agents import (
    upload_file_to_google_ai,
    agent_01_foundational_processor,
    agent_02a_persona_analyzer,
    agent_02b_sop_adherence,
    agent_02c_lead_scoring
)


async def main_pipeline(audio_path: str, sop_path: str, questionnaire_path: str, output_dir: str):
    """
    Main function to run the entire call analytics pipeline.
    """
    print("--- Starting Call Center Analytics Pipeline ---")

    # --- 1. Load and Parse Inputs ---
    sop_points = parse_sop_pdf(sop_path)
    questionnaire = parse_questionnaire_yaml(questionnaire_path)

    if not sop_points or not questionnaire:
        print("Failed to parse input files. Exiting.")
        return

    # --- 2. Upload Audio and Get Transcript (Agent 1) ---
    audio_file_object = upload_file_to_google_ai(audio_path)
    if not audio_file_object:
        print("Failed to upload audio file. Exiting.")
        return

    transcript_data = agent_01_foundational_processor(audio_file_object)
    if not transcript_data or "transcript" not in transcript_data:
        print("Failed to get a valid transcript. Exiting.")
        # Clean up uploaded file
        genai.delete_file(audio_file_object.name)
        return

    # --- 3. Run Enrichment Agents in Parallel (Agent 2) ---
    print("\n--- Running Parallel Enrichment Agents ---")

    with tqdm(total=3, desc="Enrichment Progress") as pbar:
        tasks = []

        task_a = asyncio.create_task(agent_02a_persona_analyzer(transcript_data))
        task_a.add_done_callback(lambda t: pbar.update(1))
        tasks.append(task_a)

        task_b = asyncio.create_task(agent_02b_sop_adherence(transcript_data, sop_points))
        task_b.add_done_callback(lambda t: pbar.update(1))
        tasks.append(task_b)

        task_c = asyncio.create_task(agent_02c_lead_scoring(transcript_data, questionnaire))
        task_c.add_done_callback(lambda t: pbar.update(1))
        tasks.append(task_c)

        enrichment_results = await asyncio.gather(*tasks)

    # --- 4. Aggregate and Save Results ---
    print("\n--- Aggregating Final Results ---")

    final_call_record = {
        "source_audio_file": Path(audio_path).name,
        "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    # Combine results from all agents
    final_call_record.update(transcript_data)
    for result in enrichment_results:
        final_call_record.update(result)

    # --- 5. Save Output ---
    output_filename = f"{Path(audio_path).stem}_analysis.json"
    output_path = Path(output_dir) / output_filename
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(final_call_record, f, indent=4)

    print(f"\n✅ Pipeline Complete! Analysis saved to: {output_path}")

    # --- 6. Cleanup ---
    print(f"Cleaning up uploaded file: {audio_file_object.name}")
    genai.delete_file(audio_file_object.name)


if __name__ == "__main__":
    # --- Setup Command Line Interface ---
    parser = argparse.ArgumentParser(description="Call Center Analytics Pipeline using Gemini")
    parser.add_argument("--audio", required=True, help="Path to the audio file (e.g., mp3, wav)")
    parser.add_argument("--sop", required=True, help="Path to the SOP PDF file")
    parser.add_argument("--questionnaire", required=True, help="Path to the business questionnaire YAML file")
    parser.add_argument("--output_dir", default="outputs", help="Directory to save the analysis JSON file")

    args = parser.parse_args()

    # --- Load API Key and Configure ---
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
    genai.configure(api_key=api_key)

    # --- Run Pipeline ---
    asyncio.run(main_pipeline(args.audio, args.sop, args.questionnaire, args.output_dir))