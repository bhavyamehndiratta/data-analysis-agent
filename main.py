from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import init_db
from app.routes.upload import router as upload_router
from app.routes.analyze import router as analyze_router
from app.routes.stream import router as stream_router
from app.routes.eval import router as eval_router

load_dotenv()

app = FastAPI(title="Data Analysis Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(upload_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(eval_router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Data Analysis Agent is running"}