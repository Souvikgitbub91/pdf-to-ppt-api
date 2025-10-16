from flask import Flask, request, jsonify
import requests
from io import BytesIO
import base64

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "PDF to PPT API is running on Vercel",
        "status": "active",
        "endpoints": {
            "GET /api/status": "Health check",
            "POST /api/convert": "Convert PDF to PPT"
        }
    })

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "message": "PDF to PPT API is running",
        "status": "active",
        "version": "1.0"
    })

@app.route('/api/convert', methods=['POST'])
def convert_pdf_to_ppt():
    try:
        data = request.get_json()
        
        if not data or 'pdf_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'pdf_url' in request body"
            }), 400
        
        pdf_url = data['pdf_url']
        
        # For Vercel deployment (simplified version)
        # Download PDF
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(pdf_url, headers=headers, timeout=30)
        
        if response.status_code != 200 or not response.content.startswith(b'%PDF'):
            return jsonify({
                "success": False,
                "error": "Invalid PDF URL or unable to download"
            }), 400
        
        # Return success response (basic version for Vercel)
        return jsonify({
            "success": True,
            "message": "PDF received successfully. Ready for conversion.",
            "file_size": len(response.content),
            "conversion_id": f"conv_{hash(pdf_url) % 10000}",
            "note": "Full conversion available in local development"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Conversion error: {str(e)}"
        }), 500

# Vercel requires this
if __name__ == '__main__':
    app.run(debug=True)
else:
    # For Vercel serverless
    from flask import Flask
    app = Flask(__name__)