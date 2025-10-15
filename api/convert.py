from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches
from PyPDF2 import PdfReader
from fpdf import FPDF

app = FastAPI()

@app.get("/")
def home():
    return {"message": "PDF to PPT Converter API is running. Use POST /api/convert with a PDF file."}

@app.post("/api/convert")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        prs = Presentation()

        for i, page in enumerate(reader.pages):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            text = page.extract_text() or " "
            textbox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
            textbox.text = text.strip()

        output = BytesIO()
        prs.save(output)
        output.seek(0)
        filename = file.filename.replace(".pdf", ".pptx")
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
