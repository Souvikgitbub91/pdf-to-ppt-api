from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import tempfile

app = FastAPI(title="PDF to PPT Converter API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PDFToPPTConverter:
    def __init__(self):
        self.max_pages = int(os.getenv("MAX_PAGES", "5"))
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "5242880"))
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "90"))
    
    def convert_pdf_to_ppt(self, pdf_path: str, ppt_path: str) -> dict:
        try:
            # Import here to avoid startup issues
            from pdf2image import convert_from_path
            from pptx import Presentation
            from pptx.util import Inches
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=100, first_page=1, last_page=self.max_pages)
            
            if not images:
                return {"success": False, "error": "No images generated from PDF"}
            
            # Create presentation
            prs = Presentation()
            blank_layout = prs.slide_layouts[6]
            
            for image in images:
                slide = prs.slides.add_slide(blank_layout)
                
                # Save image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    image.save(tmp_file.name, 'JPEG', quality=60)
                    img_path = tmp_file.name
                
                # Add to slide
                left = Inches(0.5)
                top = Inches(0.5)
                slide.shapes.add_picture(img_path, left, top, height=Inches(6))
                os.unlink(img_path)
            
            prs.save(ppt_path)
            return {"success": True, "pages": len(images)}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

converter = PDFToPPTConverter()

@app.post("/convert/")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "File must be a PDF")
    
    content = await file.read()
    if len(content) > converter.max_file_size:
        raise HTTPException(400, f"File too large. Max {converter.max_file_size//1024//1024}MB")
    
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_file:
        pdf_file.write(content)
        pdf_path = pdf_file.name
    
    ppt_path = tempfile.mktemp(suffix='.pptx')
    
    try:
        result = converter.convert_pdf_to_ppt(pdf_path, ppt_path)
        
        if result["success"]:
            return FileResponse(
                ppt_path,
                media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                filename="converted.pptx"
            )
        else:
            raise HTTPException(500, result["error"])
    
    finally:
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

@app.get("/")
async def root():
    return {"message": "PDF to PPT API is running", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)