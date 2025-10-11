from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

class URLRequest(BaseModel):
    file_url: str

@app.post("/convert")
async def convert_pdf_to_ppt(url_request: URLRequest):
    return {
        "status": "SUCCESS - DEBUG MODE",
        "received_url": url_request.file_url,
        "message": "The API is working! Now we can add PDF conversion step by step."
    }

@app.get("/")
async def root():
    return {"message": "PDF to PPT API - DEBUG MODE", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Remove the if __name__ block since Render uses uvicorn directly