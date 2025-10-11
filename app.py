from fastapi import FastAPI

app = FastAPI()

@app.post("/convert")
async def convert_pdf():
    return {
        "status": "SUCCESS", 
        "message": "API is working!",
        "debug": "This endpoint accepts ANY request without validation"
    }

@app.get("/")
async def root():
    return {"message": "PDF to PPT API", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}