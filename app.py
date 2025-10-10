from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

app = FastAPI(title="PDF to PPT Converter API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    file_url: str

@app.post("/convert/")
async def convert_pdf_to_ppt(url_request: URLRequest):
    """
    SIMPLE TEST ENDPOINT - No file conversion yet
    """
    try:
        # Just return a success message with the received URL
        return {
            "status": "success",
            "message": "API is working! Ready for PDF conversion.",
            "received_url": url_request.file_url,
            "next_step": "PDF to PPT conversion will be implemented here"
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "PDF to PPT API is running", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)