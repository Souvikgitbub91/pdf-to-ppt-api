# api/convert.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from tempfile import TemporaryDirectory
from pptx import Presentation
from pptx.util import Inches, Emu
from pdf2image import convert_from_bytes

app = FastAPI()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
MAX_PAGES = 100

def _scale_and_place(slide, prs, img_bytes, img_w, img_h):
    # add image to slide and scale preserving aspect ratio
    stream = BytesIO(img_bytes)
    slide_w = prs.slide_width
    slide_h = prs.slide_height
    # compute image emu sizes
    # Need to scale by resolution; we assume 96 dpi for image
    img_w_emu = Emu(img_w * 914400 / 96)
    img_h_emu = Emu(img_h * 914400 / 96)
    # if too large, scale
    if img_w_emu > slide_w or img_h_emu > slide_h:
        # choose scaling factor
        scale = min(slide_w / img_w_emu, slide_h / img_h_emu)
        img_w_emu = int(img_w_emu * scale)
        img_h_emu = int(img_h_emu * scale)
    left = int((slide_w - img_w_emu) / 2)
    top = int((slide_h - img_h_emu) / 2)
    pic = slide.shapes.add_picture(stream, left, top, width=img_w_emu, height=img_h_emu)
    return pic

@app.post("/api/convert")
async def convert(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Must upload PDF")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        pages = convert_from_bytes(content, fmt="png", dpi=150)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cannot render PDF: {e}")

    prs = Presentation()
    for i, page_img in enumerate(pages):
        if i >= MAX_PAGES:
            break
        slide = prs.slides.add_slide(prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0])
        img_buffer = BytesIO()
        page_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        _scale_and_place(slide, prs, img_buffer.getvalue(), page_img.width, page_img.height)

    out = BytesIO()
    prs.save(out)
    out.seek(0)
    filename = file.filename.rsplit(".", 1)[0] + ".pptx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers=headers)
