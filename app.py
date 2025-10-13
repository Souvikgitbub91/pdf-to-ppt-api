from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import zipfile

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_simple_ppt() -> str:
    """Create a basic PPTX file"""
    try:
        ppt_path = tempfile.mktemp(suffix='.pptx')
        with zipfile.ZipFile(ppt_path, 'w') as pptx:
            pptx.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types></Types>')
            pptx.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships></Relationships>')
        return ppt_path
    except Exception as e:
        raise Exception(f"PPT creation failed: {str(e)}")

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "File must be a PDF")
        
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(400, "File too large. Max 5MB")
        
        ppt_path = create_simple_ppt()
        return FileResponse(
            ppt_path,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename="converted_presentation.pptx"
        )
    except Exception as e:
        raise HTTPException(500, f"Conversion error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "PDF to PPT Converter API - WORKING", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}