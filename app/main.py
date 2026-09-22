import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables
    Base.metadata.create_all(bind=engine)
    
    # Train/load ML model in background/cache
    try:
        from app.ml.train import load_trained_model
        load_trained_model()
    except Exception as e:
        print(f"Warning: ML model initialization: {e}")

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Responsive Web-Based Smart College Bus Tracking, Management, ETA Prediction and Notification System.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(api_router)

# Mount Static Files (Frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Partners Bus Prediction System API is running."}

@app.get("/health")
def health_check():
    return {"status": "ok", "system": settings.PROJECT_NAME, "privacy": "TRACK_THE_BUS_NOT_THE_STUDENT"}
