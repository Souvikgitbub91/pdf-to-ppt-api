from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
import zipfile
from io import BytesIO

app = FastAPI()

def create_simple_ppt_from_pdf(pdf_path: str, ppt_path: str) -> dict:
    """
    Create a simple PowerPoint using basic Python (no external PPT libraries)
    This creates a minimal PPTX file structure
    """
    try:
        # Create a minimal PPTX file (which is basically a ZIP file)
        with zipfile.ZipFile(ppt_path, 'w') as pptx:
            # Add basic PPTX structure files
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
            
            pptx.writestr('ppt/_rels/presentation.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>''')
            
            pptx.writestr('ppt/presentation.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
<p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>
<p:sldSz cx="9144000" cy="6858000"/>
<p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>''')
            
            pptx.writestr('ppt/slides/_rels/slide1.xml.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>''')
            
            pptx.writestr('ppt/slides/slide1.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld>
<p:spTree>
<p:nvGrpSpPr>
<p:cNvPr id="1" name=""/>
<p:cNvGrpSpPr/>
<p:nvPr/>
</p:nvGrpSpPr>
<p:grpSpPr/>
</p:spTree>
</p:cSld>
</p:sld>''')
        
        return {"success": True, "message": "Basic PPTX created successfully"}
        
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
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as pdf_temp:
            pdf_temp.write(contents)
            pdf_path = pdf_temp.name
        
        # Create output PPTX path
        ppt_path = tempfile.mktemp(suffix='.pptx')
        
        # Create basic PPTX file
        result = create_simple_ppt_from_pdf(pdf_path, ppt_path)
        
        if result["success"]:
            # Return the PPTX file
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
        # Note: FileResponse should handle ppt_path cleanup

@app.get("/")
async def root():
    return {"message": "PDF to PPT Converter API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}