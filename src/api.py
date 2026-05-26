from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from src.db import init_db, get_weak_areas
from src.parser import extract_sections_from_pdf
from src.llm import generate_mcqs
from src.config import logger
from typing import Any, Dict

app = FastAPI(title="Adaptive Prep API")


class PrepRequest(BaseModel):
    section_ids: List[int]

@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("Database initialized via API startup.")

@app.post("/api/generate")
def generate_quiz(request: PrepRequest):
    logger.info(f"API Request: Generate MCQs for sections {request.section_ids}")
    
    try:
        all_sections = extract_sections_from_pdf()
    except Exception as e:
        logger.error(f"PDF Parse Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse PDF document.")

    results = {}
    for sec_id in request.section_ids:
        if sec_id not in all_sections:
            logger.warning(f"Invalid section ID requested: {sec_id}")
            continue
        
        text_chunk = all_sections[sec_id]
        questions = generate_mcqs(sec_id, text_chunk)
        results[sec_id] = questions

    return {"status": "success", "data": results}

@app.get("/api/history/{section_id}")
def get_history(section_id: int):
    logger.info(f"API Request: Fetch history for section {section_id}")
    weak_areas = get_weak_areas(section_id)
    return {"section_id": section_id, "weak_areas": weak_areas}



class SaveRequest(BaseModel):
    scenario_name: str
    section_ids: List[int]
    qa_results: List[Dict[str, Any]]

@app.post("/api/save")
def save_quiz_session(request: SaveRequest):
    from src.db import save_session
    try:
        session_id = save_session(
            scenario_name=request.scenario_name,
            section_ids=request.section_ids,
            qa_results=request.qa_results
        )
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
        raise HTTPException(status_code=500, detail="Failed to save to database")
