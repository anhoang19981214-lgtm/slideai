from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.database import Base, engine
from backend.auth import router as auth_router
from backend.slides import router as slides_router
from sqlalchemy import text

try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE slides ADD COLUMN IF NOT EXISTS template VARCHAR(50)"))
        conn.commit()
except Exception:
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE slides ADD COLUMN template VARCHAR(50)"))
            conn.commit()
    except Exception:
        pass

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

_public = Path(__file__).parent.parent / "public"
if _public.exists():
    app.mount("/", StaticFiles(directory=str(_public), html=True), name="frontend")
