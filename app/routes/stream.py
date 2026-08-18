import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.database import get_db
from app.services.claude_service import build_dataset_context
from anthropic import Anthropic

router = APIRouter()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class StreamRequest(BaseModel):
    session_id: str
    question: str

async def stream_analysis(filepath: str, question: str):
    dataset_context = build_dataset_context(filepath)

    system_prompt = """You are a data analysis agent. The user will ask a question about a dataset.
Use code execution to answer accurately. Think step by step, show your reasoning, then give a final answer with any caveats."""

    user_message = f"""Here is the dataset:

{dataset_context}

To use it in code, load it like this:
```python
import pandas as pd
import io

data = \"\"\"
{open(filepath).read()}
\"\"\"
df = pd.read_csv(io.StringIO(data))
```

Question: {question}
"""

    # Stream the response
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        tools=[{"type": "code_execution_20250522", "name": "code_execution"}],
        messages=[{"role": "user", "content": user_message}]
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"

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