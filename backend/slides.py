import json
from typing import Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth import get_current_user, decrypt_key
from backend.database import get_db
from backend.models import Slide, User

router = APIRouter(prefix="/slides", tags=["slides"])

SLIDE_PROMPT = """\
You are a professional presentation designer. Create a slide deck in {language} about: {topic}
{description_line}
Requirements:
- Exactly {slide_count} slides total
- Slide 1: type "cover" with fields "title" and "subtitle"
- Slides 2 to {last_content}: type "content" with fields "title" and "bullets" (list of 3-5 strings, each under 15 words)
- Slide {slide_count}: type "conclusion" with fields "title" and "summary"

Respond with ONLY valid JSON array, no markdown fences, no explanation:
[
  {{"index": 1, "type": "cover", "title": "...", "subtitle": "..."}},
  {{"index": 2, "type": "content", "title": "...", "bullets": ["...", "...", "..."]}},
  {{"index": {slide_count}, "type": "conclusion", "title": "...", "summary": "..."}}
]"""


def _call_gemini(api_key: str, prompt: str) -> list[dict]:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _generate_slides(
    api_key: str, topic: str, description: Optional[str], slide_count: int, language: str
) -> list[dict]:
    desc_line = f"\nAdditional context: {description}" if description else ""
    prompt = SLIDE_PROMPT.format(
        language=language,
        topic=topic,
        description_line=desc_line,
        slide_count=slide_count,
        last_content=slide_count - 1,
    )
    try:
        return _call_gemini(api_key, prompt)
    except (json.JSONDecodeError, Exception):
        retry_prompt = prompt + "\n\nIMPORTANT: Return ONLY the JSON array. No markdown, no text before or after."
        return _call_gemini(api_key, retry_prompt)


class GenerateBody(BaseModel):
    topic: str
    description: Optional[str] = None
    slide_count: int = Field(ge=5, le=25)
    language: str = "vi"
    theme: str = "purple"


@router.get("/history")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (
        db.query(Slide)
        .filter(Slide.user_id == user.id)
        .order_by(Slide.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "language": r.language,
            "slide_count": r.slide_count,
            "theme": r.theme,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.get("/export/{slide_id}")
def export_pptx(
    slide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from backend.pptx_builder import build_pptx

    record = db.query(Slide).filter(Slide.id == slide_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Slide not found")
    if record.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    pptx_bytes = build_pptx(json.loads(record.content_json), record.theme)
    filename = record.title[:50].replace(" ", "_") + ".pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{slide_id}")
def get_slide(
    slide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Slide).filter(Slide.id == slide_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Slide not found")
    if record.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "id": record.id,
        "title": record.title,
        "language": record.language,
        "slide_count": record.slide_count,
        "theme": record.theme,
        "created_at": record.created_at.isoformat(),
        "slides": json.loads(record.content_json),
    }


@router.post("/generate")
def generate(
    body: GenerateBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.gemini_api_key_enc:
        raise HTTPException(status_code=400, detail="No Gemini API key saved. Add it in account settings.")
    api_key = decrypt_key(user.gemini_api_key_enc)
    slides = _generate_slides(api_key, body.topic, body.description, body.slide_count, body.language)
    record = Slide(
        user_id=user.id,
        title=body.topic,
        language=body.language,
        slide_count=body.slide_count,
        theme=body.theme,
        content_json=json.dumps(slides, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"slide_id": record.id, "slides": slides}


@router.delete("/{slide_id}")
def delete_slide(
    slide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Slide).filter(Slide.id == slide_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Slide not found")
    if record.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    db.delete(record)
    db.commit()
    return {"status": "deleted"}
