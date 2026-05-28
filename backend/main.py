from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.database import Base, engine
from backend.auth import router as auth_router
from backend.slides import router as slides_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SlideAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(slides_router)
app.mount("/", StaticFiles(directory="public", html=True), name="frontend")
