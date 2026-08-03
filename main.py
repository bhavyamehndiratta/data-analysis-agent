from fastapi import FastAPI
from dotenv import load_dotenv
from app.database import init_db
from app.routes.upload import router as upload_router

load_dotenv()

app = FastAPI(title="Data Analysis Agent")

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(upload_router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Data Analysis Agent is running"}