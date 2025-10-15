# api/convert.py
# Vercel-friendly FastAPI endpoint to convert uploaded PDF -> PPTX in real time.
# Accepts multipart form with field 'file'. Returns .pptx binary as attachment.
#
# Requirements: fastapi, uvicorn, python-multipart, pymupdf, python-pptx, aiofiles

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from tempfile import NamedTemporaryFile
from io import BytesIO
from typing import Tuple
import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Inches, Emu
import asyncio

app = FastAPI()

# Safety / resource limits (tweak as needed)
MAX_FILE_SIZE_BYTES = 40 * 1024 * 1024  # 40 MB upload cap
MAX_PAGES = 200  # maximum pages to convert to avoid heavy memory use
RENDER_DPI = 150  # DPI for PDF -> image rendering (150 is a reasonable tradeoff)

def _bytes_to_int(b: bytes) -> int:
    return len(b)

def _scale_and_place_image(prs: Presentation, slide, img_width_px: int, img_height_px: int, dpi: int, image_stream: BytesIO):
    """
    Add image_stream to slide and scale to fit slide preserving aspect ratio.
    prs.slide_width and prs.slide_height are in EMU.
    """
    # Convert image size in pixels to inches
    img_w_in = img_width_px / dpi
    img_h_in = img_height_px / dpi

    slide_w_emu = prs.slide_width  # in EMU
    slide_h_emu = prs.slide_height

    # Convert image size to EMU
    img_w_emu = Emu(img_w_in * 914400)  # 1 inch = 914400 EMU (pptx uses Emu helper but this is fine)
    img_h_emu = Emu(img_h_in * 914400)

    # Decide scaling: fit by width or height
    # Use only one dimension in add_picture to preserve aspect ratio, then compute top/left to center.
    slide_w = slide_w_emu
    slide_h = slide_h_emu

    # ratio comparisons must be numeric, convert Emu to int
    sw = int(slide_w)
    sh = int(slide_h)
    iw = int(img_w_emu)
    ih = int(img_h_emu)

    # If image fits without scaling, center it as is
    if iw <= sw and ih <= sh:
        left = int((sw - iw) / 2)
        top = int((sh - ih) / 2)
        pic = slide.shapes.add_picture(image_stream, left, top)
        return pic

    # Scale to fit
    # If image is proportionally wider than slide -> fit width
    if (iw * sh) >= (ih * sw):
        # fit width
        left = 0
        top = int((sh - int(iw * sh / sw * (ih/ih))) / 2)  # will adjust later
        pic = slide.shapes.add_picture(image_stream, 0, 0, width=slide_w_emu)
        # center vertically
        top_calc = int((sh - pic.height) / 2)
        pic.left = 0
        pic.top = top_calc
        return pic
    else:
        # fit height
        pic = slide.shapes.add_picture(image_stream, 0, 0, height=slide_h_emu)
        left_calc = int((sw - pic.width) / 2)
        pic.left = left_calc
        pic.top = 0
        return pic


@app.post("/api/convert")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    # Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF (content-type application/pdf).")

    # Read bytes (beware memory usage; for Vercel, uploads are typically small)
    contents = await file.read()
    size = _bytes_to_int(contents)
    if size == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max allowed: {MAX_FILE_SIZE_BYTES // (1024*1024)} MB")

    # Use PyMuPDF to open PDF from bytes
    try:
        # fitz.open can accept bytes with filetype='pdf'
        doc = fitz.open(stream=contents, filetype="pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open PDF: {e}")

    page_count = doc.page_count
    if page_count == 0:
        raise HTTPException(status_code=400, detail="PDF has no pages.")
    if page_count > MAX_PAGES:
        raise HTTPException(status_code=413, detail=f"PDF has {page_count} pages which exceeds the limit of {MAX_PAGES} pages.")

    # Create PPTX presentation
    prs = Presentation()
    # Optionally set slide size to common 16:9 (10 x 5.625 in) or keep default
    # prs.slide_width = Inches(13.333)  # example; keep default for compatibility

    # Convert each page to image and add to PPT
    try:
        for pno in range(page_count):
            page = doc.load_page(pno)
            # Render page to image pixmap
            mat = fitz.Matrix(RENDER_DPI / 72.0, RENDER_DPI / 72.0)  # scale from 72 dpi baseline
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_bytes = pix.tobytes("png")
            img_io = BytesIO(img_bytes)

            # Create a blank slide (layout 6 = blank in many templates)
            slide_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]
            slide = prs.slides.add_slide(slide_layout)

            # Add image scaling/placement
            _scale_and_place_image(prs, slide, pix.width, pix.height, RENDER_DPI, img_io)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed while rendering pages: {e}")
    finally:
        doc.close()

    # Write presentation to bytes
    out = BytesIO()
    prs.save(out)
    out.seek(0)

    # StreamingResponse will stream the PPTX back
    filename = file.filename.rsplit(".", 1)[0] if "." in file.filename else "converted"
    suggested = f"{filename}.pptx"
    headers = {
        "Content-Disposition": f'attachment; filename="{suggested}"'
    }
    return StreamingResponse(out, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers=headers)
