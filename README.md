# Adaptive Quiz Preparation System

An intelligent, full-stack application designed to ingest a multi-section PDF dossier, generate dynamic Multiple Choice Questions (MCQs) using an LLM, and track user performance in a local Knowledge Base (KB).

The flagship feature of this system is **Adaptive Intelligence (RAG)**: the system queries the local database for the user's historical weak areas and dynamically instructs the LLM to target those specific conceptual gaps in future quiz generations.

---

# Architecture & Features

The system supports two distinct modes of operation:

## 1. Automated CLI Mode
A script-driven backend that rapidly simulates user interactions and generates the required `.json` evaluation outputs.

## 2. Interactive Full-Stack Mode
A FastAPI REST backend coupled with a Streamlit frontend, allowing real users to take quizzes, see live score metrics, and trigger the adaptive RAG logic interactively.

---

# Implemented Enhancements

## ✅ Containerization
Fully dockerized backend and frontend via `docker-compose`.

## ✅ Minimal UI
Interactive Streamlit application (`src/app.py`) with session state management and progress tracking.

## ✅ Test Coverage
Automated `pytest` suite for database initialization and graceful file-handling failures.

## ✅ Error Handling
Robust `try/except` blocks that catch LLM hallucinations/rate-limits and deploy a Graceful Fallback generator so the system never crashes.

## ✅ Structured Logging
A professional logging setup (`system.log`) tracking API calls, fallbacks, and DB operations.

---

# Tech Stack & Engineering Decisions

| Component | Technology | Reasoning |
|---|---|---|
| **Language** | Python 3.10+ | Modern ecosystem and excellent AI tooling |
| **LLM Engine** | Groq API (`llama-3.1-8b-instant`) | Fast inference, generous free tier, reliable `json_object` formatting. Initially built with Google Gemini 1.5 Flash, but persistent 429/geo-blocking issues on the free tier made testing unstable. Swapped to Groq because of its blazing-fast token generation, generous free tier, and reliable native json_object formatting. |
| **PDF Parser** | PyMuPDF (`fitz`) | Faster and more reliable section extraction than `pdfplumber` or `PyPDF2`. Chosen over pdfplumber or PyPDF2 for its speed and superior handling of raw text blocks, making Regex extraction of specific "Section X" headers much more reliable.|
| **Database** | SQLite3 | Zero-configuration setup and lightweight persistence . Zero-configuration setup. Fits the "run from scratch in 5 minutes" requirement perfectly while supporting robust SQL joins to retrieve historical weak areas for the RAG prompt.| 
| **API Layer** | FastAPI + Uvicorn | High performance and automatic Swagger documentation | 
| **Frontend** | Streamlit | Rapid development of an interactive UI without requiring React/Node |

---

# Setup Instructions (Under 5 Minutes)

##  Prerequisites

- Python 3.10 or higher
- Optional: Docker Desktop (for containerized deployment)

---

# Local Installation

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <your-project-folder>
```

---

## 2. Create and Activate a Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux
```bash
python -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_api_key_here
```

---

## 5. Add the PDF Source

Ensure the following file exists in the root directory:

```text
SLATEFALL_DOSSIER.pdf
```

---

# Running the Evaluation Scenarios

# Option 1: Automated CLI (Assessment Output Generation)

Use the CLI to automatically run evaluation scenarios, simulate user responses (~60% accuracy), and generate output folders.

---

## Scenario A — Cold-Start Preparation

Runs a baseline preparation session over two random sections.

```bash
python -m src.cli scenario-a
```

---

## Scenario B — Adaptive Iteration (Core Requirement)

Executes three consecutive iterations.

The system dynamically analyzes mistakes from Iteration 1 and adjusts future quiz generations to target weak areas.

```bash
python -m src.cli scenario-b
```

### Output Location

```text
outputs/scenario_b_iterX/
```

---

# Option 2: Interactive Web UI (Full Stack)

Test the adaptive logic interactively using the frontend UI.

---

## Using Docker (Recommended)

```bash
docker-compose up --build
```

---

## Using Local Python (Two Separate Terminals)

### Terminal 1 — Start Backend API

```bash
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

### Terminal 2 — Start Frontend UI

```bash
streamlit run src/app.py
```

---

## Access the Application

```text
http://localhost:8501
```

---

# Option 3: Run the Test Suite

Validate database initialization and error-handling logic.

```bash
pytest tests/
```

---

# Known Limitations & Assumptions

## LLM Formatting Quirks

Even with strict JSON-mode prompting, LLMs occasionally return:

```json
[
  ...
]
```

instead of:

```json
{
  "questions": [...]
}
```

The application handles this via exception catching and falls back to a simulated RAG generator to ensure uninterrupted execution.

---

## API Rate Limiting

Free-tier APIs are heavily throttled.

The CLI includes strategic `time.sleep()` pauses between iterations to reduce the likelihood of `429 Resource Exhausted` errors.

---

## PDF Structure Assumption

The parser logic assumes sections follow patterns such as:

```text
Section X.
```

or

```text
Section X:
```

---

## Streamlit State Management

Streamlit reruns the script aggressively on every interaction.

To prevent stale widget state ("ghost answers"), unique `uuid` keys are injected into widgets during every quiz generation cycle.

---

# Project Structure

```text
project-root/
│
├── src/
│   ├── api.py
│   ├── app.py
│   ├── cli.py
│   ├── parser.py
│   ├── rag.py
│   ├── database.py
│   └── ...
│
├── tests/
│   └── ...
│
├── outputs/
│   └── scenario_b_iterX/
│
├── requirements.txt
├── docker-compose.yml
├── .env
├── system.log
└── SLATEFALL_DOSSIER.pdf
```

---

# Core System Flow

```text
PDF Ingestion
      ↓
Section Extraction
      ↓
LLM-Based MCQ Generation
      ↓
Quiz Interaction
      ↓
Performance Tracking (SQLite)
      ↓
Weak Area Detection
      ↓
Adaptive RAG Prompting
      ↓
Targeted Future Quiz Generation
```

---

# Key Highlights

- Adaptive RAG-based learning loop
- Persistent knowledge tracking
- Fully containerized architecture
- Interactive frontend + REST API backend
- Robust fallback mechanisms
- Structured logging and automated testing
- Assessment-ready CLI evaluation pipeline

---

# Author Notes

The project was engineered with a strong emphasis on:

- Reliability under free-tier API limitations
- Fast local deployment
- Reproducibility
- Clear separation of backend/frontend responsibilities
- Graceful degradation under LLM failures

The result is a resilient adaptive learning system capable of both automated evaluation workflows and interactive user-driven study sessions.



