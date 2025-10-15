from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Inches
import tempfile
import os

app = FastAPI()

@app.get("/")
def home():
    return {"message": "PDF to PPT Converter API is running. Use POST /api/convert with a PDF file."}

@app.post("/api/convert")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(await file.read())
            tmp_pdf_path = tmp_pdf.name

        # Create PPT
        prs = Presentation()
        pdf_doc = fitz.open(tmp_pdf_path)

        for page in pdf_doc:
            image = page.get_pixmap()
            image_path = f"{tmp_pdf_path}_{page.number}.png"
            image.save(image_path)

            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_picture(image_path, Inches(0), Inches(0), Inches(10), Inches(7.5))
            os.remove(image_path)

        pdf_doc.close()

        # Save PPT file
        pptx_path = tmp_pdf_path.replace(".pdf", ".pptx")
        prs.save(pptx_path)

        return FileResponse(pptx_path, filename="converted.pptx", media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)
