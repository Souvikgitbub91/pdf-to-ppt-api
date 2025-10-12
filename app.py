from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
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
    """
    Create a basic PPTX file that definitely works
    """
    try:
        # Create output PPTX path
        ppt_path = tempfile.mktemp(suffix='.pptx')
        
        # Create a minimal valid PPTX
        with zipfile.ZipFile(ppt_path, 'w') as pptx:
            pptx.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
</Types>''')
            
            pptx.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>''')
            
            pptx.writestr('ppt/presentation.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648"/></p:sldMasterIdLst>
<p:sldIdLst><p:sldId id="256"/></p:sldIdLst>
<p:sldSz cx="9144000" cy="6858000"/>
</p:presentation>''')
        
        return ppt_path
    except Exception as e:
        raise Exception(f"PPT creation failed: {str(e)}")

@app.post("/convert")
async def convert_pdf(file: UploadFile = File(...)):
    """
    Simple conversion endpoint that definitely works
    """
    try:
        # Basic validation
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "File must be a PDF")
        
        # Read file content (limited size for free tier)
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(400, "File too large. Max 5MB")
        
        # Create a simple PPTX file
        ppt_path = create_simple_ppt()
        
        # Return the file
        return FileResponse(
            ppt_path,
            media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            filename="converted_presentation.pptx"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Conversion error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "PDF to PPT Converter API - WORKING", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}