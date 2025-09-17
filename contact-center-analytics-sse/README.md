# DialogIQ: Intelligent Communication Analysis Tool

**DialogIQ** is a comprehensive call center analytics platform built for **SolarSquare Energy**. It leverages advanced AI to transcribe, analyze, and provide deep insights into agent-customer conversations, helping to improve quality, ensure compliance, and identify high-quality leads.

---

## Features

* **Multi-Language Transcription & Diarization**: Automatically transcribes audio, separates speakers (Agent vs. Customer), and provides transcripts in both the original language and English.
* **Customer Persona Analysis**: Generates a detailed customer profile, including sentiment, price/quality sensitivity, and technical proficiency.
* **Automated Script Adherence**: Evaluates agent performance against predefined scripts (SOPs) with nuanced ratings (Fully/Partially/Not Covered).
* **Intelligent Lead Scoring**: Analyzes conversations against a business questionnaire to generate a "Lead Hotness Score" and a summary of call quality.
* **Interactive Q&A**: A chat interface allows users to ask specific, open-ended questions about the call and receive instant answers.
* **Web-Based UI**: A clean, professional user interface for uploading calls, viewing results, and managing scripts.

---

## Getting Started

Follow these steps to set up and run the application on your local machine.

### 1. Prerequisites

* Python 3.8+
* An active Google AI API key

### 2. Setup Instructions

1.  **Clone the Repository**
    Clone this project to your local machine.
    ```bash
    git clone <repository-url>
    cd contact-center-analytics-sse
    ```

2.  **Create a Virtual Environment**
    It's highly recommended to use a virtual environment to manage dependencies.
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**
    Install all required Python packages from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a file named `.env` in the root of the project directory (`call_analytics_project/`). Add your Google AI API key to this file.
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_AI_API_KEY_HERE"
    ```

### 3. Running the Application

The application consists of two parts: the backend server and the frontend interface. **You must run them in two separate terminals.**

#### Terminal 1: Start the Backend Server

1.  Navigate to the root directory of the project (`call_analytics_project/`).
2.  Run the following command to start the FastAPI server:
    ```bash
    uvicorn backend.api:app --reload
    ```
3.  Keep this terminal running. You should see a confirmation that the server is active on `http://127.0.0.1:8000`.

#### Terminal 2: Start the Frontend Server

1.  Open a **new terminal window**.
2.  Navigate **into the `frontend` directory**:
    ```bash
    cd frontend
    ```
3.  Start the simple Python web server on port `8001`:
    ```bash
    # For Python 3
    python -m http.server 8001
    ```
4.  Keep this terminal running as well.

### 4. How to Test the Code

1.  Open your web browser (Chrome, Firefox, Edge) and navigate to:
    **`http://localhost:8001`**

2.  You should see the DialogIQ homepage.
3.  Use the form to upload an audio file (.mp3, .wav, etc.).
4.  Click the "Analyze Call" button to process the audio.
5.  Once the analysis is complete, the results will be displayed on the page.
6.  Navigate through the different tabs to view the script adherence details, the scoring questionnaire, and to use the interactive "Ask Specific Questions" chat.

---

## Project Structure
```bash
call_analytics_project/
├── backend/
│   ├── api.py                 # FastAPI server and all API endpoints
│   ├── gemini_agents.py       # All AI agent logic and prompts
│   ├── file_parser.py         # Utilities for parsing YAML/PDF files
│   └── inputs/
│       ├── sop.yaml           # Editable script adherence file
│       └── questionnaire.yaml # Editable lead scoring file
├── frontend/
│   ├── index.html             # Main application UI
│   ├── script.js              # All frontend logic and API calls
│   └── style.css              # All custom styling
├── outputs/                   # (Ignored by git) Where results can be saved
├── .env                       # (Ignored by git) Stores secret API keys
├── .gitignore                 # Specifies files for git to ignore
└── README.md                  # This file
```