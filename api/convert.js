export default async function handler(request, response) {
  if (request.method === 'POST') {
    try {
      const { pdf_url } = request.body;
      
      if (!pdf_url) {
        return response.status(400).json({
          success: false,
          error: "Missing pdf_url in request body"
        });
      }

      // Return immediate success (you can add actual conversion later)
      response.status(200).json({
        success: true,
        message: "PDF to PPT conversion request received",
        conversion_id: `conv_${Date.now()}`,
        status: "queued",
        pdf_url: pdf_url,
        note: "This is a working API endpoint. Add your conversion logic here."
      });
      
    } catch (error) {
      response.status(500).json({
        success: false,
        error: "Server error: " + error.message
      });
    }
  } else {
    response.status(405).json({
      success: false,
      error: "Method not allowed. Use POST."
    });
  }
}