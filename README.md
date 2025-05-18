Video Highlight Automation Backend
A Python-based backend service for automatically extracting highlights from long-form videos and creating content plans for social media.
Features

Upload long videos (MP4, MOV, AVI)
Automatically detect video highlights using Gemini AI API
Extract highlight clips with proper formatting for social media
Generate subtitles for clips
Create content plans with suggested posting dates and captions
RESTful API for integration with the frontend
Optional integration with YouTube and Instagram APIs

Requirements

Python 3.8+
ffmpeg (for video processing)
Google API key for Gemini AI

Installation

Clone the repository

bashgit clone https://github.com/yourusername/video-highlight-automation.git
cd video-highlight-automation/backend

Create a virtual environment and activate it

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bashpip install -r requirements.txt

Set up environment variables

bash# Linux/macOS
export GOOGLE_API_KEY="your-gemini-api-key"

# Windows
set GOOGLE_API_KEY=your-gemini-api-key
Alternatively, create a .env file in the project root with:
GOOGLE_API_KEY=your-gemini-api-key
Project Structure
backend/
├── main.py             # FastAPI application entry point
├── models.py           # Pydantic data models
├── video_processor.py  # Video processing utilities
├── ai_analyzer.py      # Gemini AI integration
├── requirements.txt    # Python dependencies
├── uploads/            # Uploaded videos storage
├── clips/              # Extracted highlights storage
├── subtitles/          # Generated subtitles storage
└── content_plans/      # Generated content plans storage
API Endpoints
EndpointMethodDescription/api/uploadPOSTUpload a video for processing/api/status/{video_id}GETGet processing status of a video/api/videos/{video_id}GETGet metadata for a specific video/api/videosGETList all uploaded videos/api/videos/{video_id}/highlightsGETGet all highlights for a specific video/api/videos/{video_id}/content_planGETGet the content plan for a specific video/api/videos/{video_id}DELETEDelete a video and all its associated data/api/publish/youtube/{clip_id}POSTPublish a highlight clip to YouTube (optional)/api/publish/instagram/{clip_id}POSTPublish a highlight clip to Instagram (optional)
Running the Server
bashuvicorn main:app --reload
The API will be available at http://localhost:8000.
API Documentation
FastAPI automatically generates interactive API documentation:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

Dependencies

FastAPI: Web framework
moviepy: Video processing
google-generativeai: Gemini AI API
Pillow: Image processing
python-multipart: Form data handling
uvicorn: ASGI server