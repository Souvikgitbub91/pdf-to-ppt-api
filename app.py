from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import tempfile
from pdf2image import convert_from_path
from pptx import Presentation
from pptx.util import Inches
import asyncio
import threading

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
    def __init__(self):
        # Read from environment variables with fallback values
        self.max_pages = int(os.getenv("MAX_PAGES", "10"))
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "8388608"))  # 8MB default
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "120"))
        self.conversion_dpi = int(os.getenv("CONVERSION_DPI", "150"))
    
    def count_pdf_pages(self, pdf_path: str) -> int:
        """Count pages in PDF without full conversion"""
        try:
            images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=50)
            return len(images)
        except:
            # Fallback: try to get at least first few pages
            try:
                images = convert_from_path(pdf_path, first_page=1, last_page=5, dpi=50)
                return min(len(images), 5)
            except:
                return 0
    
    def convert_with_timeout(self, pdf_path: str, ppt_path: str) -> dict:
        """Run conversion with timeout to prevent hanging"""
        result = {"success": False, "error": "Conversion timeout"}
        
        def conversion_worker():
            try:
                # Convert PDF to images using DPI from environment variable
                images = convert_from_path(pdf_path, dpi=self.conversion_dpi, thread_count=2)
                
                if not images:
                    result.update({"success": False, "error": "No images generated from PDF"})
                    return
                
                # Limit number of pages for free tier
                if len(images) > self.max_pages:
                    images = images[:self.max_pages]
                
                # Create PowerPoint presentation
                prs = Presentation()
                blank_slide_layout = prs.slide_layouts[6]
                
                for i, image in enumerate(images):
                    # Save image temporarily with lower quality
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        image.save(tmp_file.name, 'JPEG', quality=70)  # JPEG with lower quality
                        img_path = tmp_file.name
                    
                    # Add image to slide
                    left = Inches(0.5)
                    top = Inches(0.5)
                    slide = prs.slides.add_slide(blank_slide_layout)
                    slide.shapes.add_picture(img_path, left, top, height=Inches(6.5))
                    
                    # Clean up temporary image file
                    os.unlink(img_path)
                
                # Save presentation
                prs.save(ppt_path)
                result.update({
                    "success": True, 
                    "message": f"Converted {len(images)} pages to PPT",
                    "pages_converted": len(images),
                    "original_pages": len(images)
                })
                
            except Exception as e:
                result.update({"success": False, "error": str(e)})
        
        # Run conversion in a thread with timeout
        thread = threading.Thread(target=conversion_worker)
        thread.start()
        thread.join(timeout=self.timeout_seconds)
        
        if thread.is_alive():
            # Thread is still running - timeout occurred
            return {"success": False, "error": f"Conversion timeout after {self.timeout_seconds} seconds"}
        
        return result

converter = PDFToPPTConverter()

@app.post("/convert/")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    # Check file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    # Check file size limit
    if file_size > converter.max_file_size:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum {converter.max_file_size // 1024 // 1024}MB allowed for free tier."
        )
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_file:
        pdf_file.write(content)
        pdf_path = pdf_file.name
    
    ppt_path = tempfile.mktemp(suffix='.pptx')
    
    try:
        # Quick page count check
        page_count = converter.count_pdf_pages(pdf_path)
        if page_count > converter.max_pages:
            raise HTTPException(
                status_code=400, 
                detail=f"PDF has too many pages ({page_count}). Maximum {converter.max_pages} pages allowed for free tier."
            )
        
        # Convert PDF to PPT with timeout
        result = converter.convert_with_timeout(pdf_path, ppt_path)
        
        if result["success"]:
            return FileResponse(
                ppt_path, 
                media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', 
                filename="converted.pptx",
                headers={
                    "X-Pages-Converted": str(result.get("pages_converted", 0)),
                    "X-Original-Pages": str(result.get("original_pages", 0))
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    
    finally:
        # Clean up temporary PDF file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        # PPT file will be deleted after sending by FileResponse

@app.get("/")
async def root():
    return {
        "message": "PDF to PPT Converter API is running",
        "limits": {
            "max_file_size_mb": converter.max_file_size // 1024 // 1024,
            "max_pages": converter.max_pages,
            "timeout_seconds": converter.timeout_seconds,
            "conversion_dpi": converter.conversion_dpi  # Added this line
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)