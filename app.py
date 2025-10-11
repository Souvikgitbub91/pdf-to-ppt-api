from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import json

app = FastAPI()

# Model for JSON requests
class ConvertRequest(BaseModel):
    file_url: str

# Endpoint that accepts BOTH JSON and form data
@app.post("/convert")
async def convert_pdf(
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None)
):
    try:
        # Handle JSON request (file_url in body)
        if file_url:
            return {
                "status": "SUCCESS", 
                "message": "API is working with URL!",
                "received_url": file_url,
                "type": "url_request"
            }
        
        # Handle file upload
        if file:
            return {
                "status": "SUCCESS", 
                "message": "API is working with file upload!",
                "filename": file.filename,
                "type": "file_upload"
            }
        
        # If neither provided
        raise HTTPException(status_code=422, detail="Either provide file_url or upload a file")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "PDF to PPT API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Safe exception handler
@app.exception_handler(Exception)
async def universal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error - please check your request format"}
    )