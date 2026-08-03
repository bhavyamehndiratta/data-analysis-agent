import os
import uuid
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.database import get_db

router = APIRouter()

UPLOAD_DIR = "data/uploads"

class DatasetSummary(BaseModel):
    session_id: str
    filename: str
    rows: int
    columns: int
    column_names: list[str]
    missing_values: dict[str, int]
    duplicate_rows: int
    dtypes: dict[str, str]

@router.post("/upload", response_model=DatasetSummary)
async def upload_dataset(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")

    # 2. Generate session ID and save file
    session_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_DIR, f"{session_id}_{file.filename}")

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    # 3. Load into pandas
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {str(e)}")

    # 4. Data quality checks
    missing = df.isnull().sum()
    missing_dict = {col: int(count) for col, count in missing.items() if count > 0}
    duplicate_rows = int(df.duplicated().sum())
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # 5. Store in SQLite
    conn = get_db()
    conn.execute(
        "INSERT INTO datasets (session_id, filename, filepath, rows, columns) VALUES (?, ?, ?, ?, ?)",
        (session_id, file.filename, filepath, len(df), len(df.columns))
    )
    conn.commit()
    conn.close()

    return DatasetSummary(
        session_id=session_id,
        filename=file.filename,
        rows=len(df),
        columns=len(df.columns),
        column_names=list(df.columns),
        missing_values=missing_dict,
        duplicate_rows=duplicate_rows,
        dtypes=dtypes
    )