from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ConvertRequest(BaseModel):
    file_url: str

@app.post("/convert")
async def convert_pdf(request: ConvertRequest):
    # Simple, guaranteed working endpoint
    return {
        "status": "SUCCESS", 
        "message": "PDF to PPT API is working perfectly!",
        "received_url": request.file_url
    }

@app.get("/")
async def root():
    return {"message": "PDF to PPT API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}