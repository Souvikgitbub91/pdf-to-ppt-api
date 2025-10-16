export default function handler(request, response) {
  response.status(200).json({
    message: "PDF to PPT API is running",
    status: "active",
    timestamp: new Date().toISOString()
  });
}