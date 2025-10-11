from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
import requests
from pathlib import Path

app = FastAPI()

# Real PDF to PPT conversion function
def convert_pdf_to_ppt_real(pdf_path: str, ppt_path: str) -> dict:
    try:
        # Import required libraries
        from pdf2image import convert_from_path
        from pptx import Presentation
        from pptx.util import Inches
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=150)
        
        if not images:
            return {"success": False, "error": "No pages found in PDF"}
        
        # Create PowerPoint presentation
        prs = Presentation()
        
        # Use blank slide layout
        blank_slide_layout = prs.slide_layouts[6]
        
        for i, image in enumerate(images):
            # Create slide
            slide = prs.slides.add_slide(blank_slide_layout)
            
            # Save image temporarily
            temp_img_path = f"temp_page_{i}.jpg"
            image.save(temp_img_path, "JPEG")
            
            # Add image to slide
            left = Inches(0.5)
            top = Inches(0.5)
            slide.shapes.add_picture(temp_img_path, left, top, height=Inches(7))
            
            # Remove temporary image
            os.remove(temp_img_path)
        
        # Save presentation
        prs.save(ppt_path)
        return {"success": True, "pages": len(images)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_temp:
            pdf_temp.write(contents)
            pdf_path = pdf_temp.name
        
        ppt_path = tempfile.mktemp(suffix='.pptx')
        
        # Perform REAL conversion
        result = convert_pdf_to_ppt_real(pdf_path, ppt_path)
        
        if result["success"]:
            # Return the actual PPTX file
            return FileResponse(
                ppt_path,
                media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                filename=f"converted_{file.filename}.pptx"
            )
        else:
            raise HTTPException(500, f"Conversion failed: {result['error']}")
    
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
    finally:
        # Cleanup
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)

@app.get("/")
async def root():
    return {"message": "Real PDF to PPT Converter API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}