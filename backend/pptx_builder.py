import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

THEMES = {
    "purple": {"bg": (26, 0, 51),   "accent": (102, 126, 234), "text": (226, 217, 243)},
    "pink":   {"bg": (50, 0, 30),   "accent": (245, 87, 108),  "text": (252, 231, 243)},
    "blue":   {"bg": (0, 20, 50),   "accent": (79, 172, 254),  "text": (224, 242, 254)},
    "green":  {"bg": (0, 30, 20),   "accent": (67, 233, 123),  "text": (220, 252, 231)},
    "sunset": {"bg": (40, 0, 20),   "accent": (250, 112, 154), "text": (255, 228, 230)},
}

W = Inches(13.33)
H = Inches(7.5)


def _textbox(slide, text: str, left, top, width, height, size: int, bold: bool, color: tuple):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    run = p.runs[0]
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(*color)


def _set_bg(slide, color: tuple):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(*color)


def build_pptx(slides: list[dict], theme: str) -> bytes:
    colors = THEMES.get(theme, THEMES["purple"])
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    blank = prs.slide_layouts[6]

    for s in slides:
        slide = prs.slides.add_slide(blank)
        _set_bg(slide, colors["bg"])

        if s["type"] == "cover":
            _textbox(slide, s.get("title", ""), Inches(1), Inches(2.5), Inches(11.33), Inches(1.5), 40, True, colors["accent"])
            _textbox(slide, s.get("subtitle", ""), Inches(1), Inches(4.2), Inches(11.33), Inches(1), 22, False, colors["text"])

        elif s["type"] == "content":
            _textbox(slide, s.get("title", ""), Inches(0.8), Inches(0.5), Inches(11.73), Inches(1), 28, True, colors["accent"])
            for i, bullet in enumerate(s.get("bullets", [])):
                _textbox(slide, f"▸  {bullet}", Inches(1), Inches(1.7 + i * 0.9), Inches(11), Inches(0.8), 18, False, colors["text"])

        elif s["type"] == "conclusion":
            _textbox(slide, s.get("title", ""), Inches(1), Inches(2), Inches(11.33), Inches(1.2), 34, True, colors["accent"])
            _textbox(slide, s.get("summary", ""), Inches(1), Inches(3.5), Inches(11.33), Inches(2), 20, False, colors["text"])

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
