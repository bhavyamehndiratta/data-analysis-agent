import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.services.claude_service import run_analysis

router = APIRouter()

class AnalysisRequest(BaseModel):
    session_id: str
    question: str

class AnalysisResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    code_executed: list[str]
    iterations: int
    drill_down: list[dict]

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM datasets WHERE session_id = ?",
        (request.session_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found. Upload a dataset first.")

    filepath = row["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=422, detail="Dataset file not found on disk.")

    try:
        result = run_analysis(filepath, request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return AnalysisResponse(
        session_id=request.session_id,
        question=request.question,
        answer=result["answer"],
        code_executed=result["code_executed"],
        iterations=result["iterations"],
        drill_down=result["drill_down"]
    )