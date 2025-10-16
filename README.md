# PDF to PPT Conversion API

A Python-based API for converting PDF files to PowerPoint presentations, deployed on Vercel.

## Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /convert` - Convert PDF to PPT
- `POST /api/convert` - Alternative convert endpoint

## Usage

```bash
# Health check
curl https://your-app.vercel.app/health

# Convert PDF
curl -X POST https://your-app.vercel.app/convert \
  -H "Content-Type: application/json" \
  -d '{"pdf_url": "https://example.com/sample.pdf"}'