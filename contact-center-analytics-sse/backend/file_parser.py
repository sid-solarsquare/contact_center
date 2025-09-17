import yaml
from pypdf import PdfReader
from typing import List, Dict, Union
from pathlib import PosixPath, Path
import json

def parse_sop_pdf(file_path: str) -> List[str]:
    """
    Parses a PDF file and extracts text from each page as a list of SOP points.
    Assumes each major point is on a new line or can be reasonably split.
    """
    print(f"Parsing SOP PDF: {file_path}")
    try:
        reader = PdfReader(file_path)
        sop_points = []
        for page in reader.pages:
            text = page.extract_text()
            # A simple split by newline. You can use more complex logic if needed.
            points = [p.strip() for p in text.split('\n') if p.strip()]
            sop_points.extend(points)
        print(f"Successfully parsed {len(sop_points)} SOP points.")
        return sop_points
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return []

def parse_questionnaire_yaml(file_path: str) -> Dict:
    """

    Parses a YAML file containing the business questionnaire.
    """
    print(f"Parsing Questionnaire YAML: {file_path}")
    try:
        with open(file_path, 'r') as stream:
            questionnaire = yaml.safe_load(stream)
        print("Successfully parsed questionnaire.")
        return questionnaire
    except Exception as e:
        print(f"Error parsing YAML {file_path}: {e}")
        return {}


def transcript_available(filename: str, transcript_name: str, output_path: PosixPath) -> Union[None, dict]:
    """
    Checks if the transcript data contains a valid transcript.
    """
    transcript_file = output_path / (Path(filename).stem + f"_{transcript_name}.json")
    print ("Checking for existing transcript file at:", transcript_file)
    if not transcript_file.exists():
        return None
    try:
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        return {
            "transcript_data": transcript_data
        }
    except Exception as e:
        print ("File exists but could not be read:", e)
        return None