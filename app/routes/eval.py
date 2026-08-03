from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.eval_service import run_eval, init_eval_tables
from app.database import get_db
import os

router = APIRouter()

class EvalRequest(BaseModel):
    session_id: str
    test_cases: list[dict]

@router.post("/eval")
async def run_evaluation(request: EvalRequest):
    init_eval_tables()

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM datasets WHERE session_id = ?",
        (request.session_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    filepath = row["filepath"]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Dataset file not found on disk.")

    result = run_eval(filepath, request.test_cases)
    return result

@router.get("/eval/{run_id}")
async def get_eval_results(run_id: str):
    conn = get_db()
    run = conn.execute(
        "SELECT * FROM eval_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    results = conn.execute(
        "SELECT * FROM eval_results WHERE run_id = ?", (run_id,)
    ).fetchall()
    conn.close()

    if not run:
        raise HTTPException(status_code=404, detail="Eval run not found.")

    return {
        "run": dict(run),
        "results": [dict(r) for r in results]
    }