from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import signal

app = FastAPI(title="PDF to PPT Converter API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=1)

class Timeout:
    """Timeout context manager for synchronous code"""
    def __init__(self, seconds=30):
        self.seconds = seconds
    
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.seconds)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
    
    def timeout_handler(self, signum, frame):
        raise TimeoutError("Conversion timed out")

class PDFToPPTConverter:
    def __init__(self):
        self.max_pages = int(os.getenv("MAX_PAGES", "3"))  # Reduced for free tier
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "2097152"))  # 2MB
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "25"))
        self.dpi = int(os.getenv("CONVERSION_DPI", "80"))  # Lower DPI for speed
    
    def convert_pdf_to_ppt(self, pdf_path: str, ppt_path: str) -> dict:
        try:
            # Import here to avoid startup issues
            from pdf2image import convert_from_path
            from pptx import Presentation
            from pptx.util import Inches
            
            # Check if poppler is available
            import subprocess
            result = subprocess.run(
                ["which", "pdftoppm"], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                return {"success": False, "error": "poppler-utils not installed"}
            
            # Convert PDF to images with timeout protection
            with Timeout(seconds=self.timeout_seconds):
                images = convert_from_path(
                    pdf_path, 
                    dpi=self.dpi, 
                    first_page=1, 
                    last_page=self.max_pages,
                    thread_count=1  # Reduce memory usage
                )
            
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
            
        except TimeoutError:
            return {"success": False, "error": "Conversion timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

converter = PDFToPPTConverter()

@app.post("/convert/")
async def convert_pdf_to_ppt(file: UploadFile = File(...)):
    # Validate file - removed content type check to fix 422 error
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(422, "File must be a PDF")
    
    # Read file content with size check
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(422, "Empty file")
    
    if len(content) > converter.max_file_size:
        raise HTTPException(413, f"File too large. Max {converter.max_file_size//1024//1024}MB")
    
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_file:
        pdf_file.write(content)
        pdf_path = pdf_file.name
    
    ppt_path = tempfile.mktemp(suffix='.pptx')
    
    try:
        # Run conversion in thread pool with timeout
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, converter.convert_pdf_to_ppt, pdf_path, ppt_path),
            timeout=converter.timeout_seconds
        )
        
        if result["success"]:
            return FileResponse(
                ppt_path,
                media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                filename="converted.pptx"
            )
        else:
            raise HTTPException(500, f"Conversion failed: {result.get('error', 'Unknown error')}")
    
    except asyncio.TimeoutError:
        raise HTTPException(408, "Conversion timeout - try a smaller PDF or fewer pages")
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")
    finally:
        # Cleanup
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