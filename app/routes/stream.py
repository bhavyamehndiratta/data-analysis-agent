import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.database import get_db
from app.services.claude_service import build_dataset_context, run_analysis
from anthropic import Anthropic
router = APIRouter()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class StreamRequest(BaseModel):
    session_id: str
    question: str

async def stream_analysis(filepath: str, question: str):
    # Run the full analysis and stream the result word by word
    result = run_analysis(filepath, question)
    answer = result["answer"]
    
    # Stream the answer in chunks to simulate streaming
    words = answer.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
    
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

@router.post("/stream")
async def stream_endpoint(request: StreamRequest):
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

    return StreamingResponse(
        stream_analysis(filepath, request.question),
        media_type="text/event-stream"
    )