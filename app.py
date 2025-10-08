from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import tempfile
from pdf2image import convert_from_path
from pptx import Presentation
from pptx.util import Inches

app = FastAPI(title="PDF to PPT Converter API")

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PDFToPPTConverter:
    def convert(self, pdf_path: str, ppt_path: str) -> dict:
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=180)
            
            if not images:
                return {"success": False, "error": "No images generated from PDF"}
            
            # Create a PowerPoint presentation
            prs = Presentation()
            
            # Use blank slide layout
            blank_slide_layout = prs.slide_layouts[6]
            
            for i, image in enumerate(images):
                # Create a slide
                slide = prs.slides.add_slide(blank_slide_layout)
                
                # Save image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    image.save(tmp_file.name, 'PNG')
                    img_path = tmp_file.name
                
                # Add image to slide
                left = Inches(0.5)
                top = Inches(0.5)
                slide.shapes.add_picture(img_path, left, top, height=Inches(7))
                
                # Clean up temporary image file
                os.unlink(img_path)
            
            # Save presentation
            prs.save(ppt_path)
            
            return {"success": True, "message": f"Converted {len(images)} pages to PPT"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

converter = PDFToPPTConverter()

@app.post("/convert/")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_file:
        content = await file.read()
        pdf_file.write(content)
        pdf_path = pdf_file.name
    
    ppt_path = tempfile.mktemp(suffix='.pptx')
    
    try:
        # Convert PDF to PPT
        result = converter.convert(pdf_path, ppt_path)
        
        if result["success"]:
            return FileResponse(
                ppt_path, 
                media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', 
                filename="converted.pptx"
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    finally:
        # Clean up temporary PDF file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)

@app.get("/")
async def root():
    return {"message": "PDF to PPT Converter API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)