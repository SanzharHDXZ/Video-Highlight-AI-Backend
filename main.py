import os
import uuid
import shutil
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel
from models import VideoMetadata, HighlightClip, ContentPlan, ProcessingStatus
from video_processor import VideoProcessor
from ai_analyzer import GeminiAIAnalyzer

app = FastAPI(
    title="Video Highlight Automation API",
    description="API for automatically extracting highlights from videos",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("clips", exist_ok=True)
os.makedirs("thumbnails", exist_ok=True)
os.makedirs("subtitles", exist_ok=True)
os.makedirs("content_plans", exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/clips", StaticFiles(directory="clips"), name="clips")
app.mount("/thumbnails", StaticFiles(directory="thumbnails"), name="thumbnails")

# In-memory database (replace with a real database in production)
videos_db = {}
highlights_db = {}
content_plans_db = {}
processing_status_db = {}

# Initialize AI analyzer
ai_analyzer = GeminiAIAnalyzer()

# Background task to process videos
async def process_video(video_id: str, file_path: str):
    try:
        # Update status
        processing_status_db[video_id] = ProcessingStatus(
            video_id=video_id,
            status="PROCESSING"
        )
        
        # Process video to extract metadata
        processor = VideoProcessor(file_path)
        
        # Update video metadata
        videos_db[video_id].duration = processor.get_duration()
        videos_db[video_id].frames = processor.get_frame_count()
        videos_db[video_id].processing_status = "PROCESSING"
        
        # Update status
        processing_status_db[video_id] = ProcessingStatus(
            video_id=video_id,
            status="ANALYZING"
        )
        
        # Analyze video with AI
        analysis_result = await ai_analyzer.analyze_video(file_path)
        
        # Extract highlights
        processing_status_db[video_id] = ProcessingStatus(
            video_id=video_id,
            status="EXTRACTING_HIGHLIGHTS"
        )
        
        highlights = analysis_result.get("highlighted_moments", [])
        highlight_clips = []
        
        for i, highlight in enumerate(highlights):
            highlight_id = str(uuid.uuid4())
            
            # Extract clip
            clip_filename = f"{video_id}_highlight_{i}.mp4"
            clip_path = os.path.join("clips", clip_filename)
            
            start_time = highlight.get("start_time", 0)
            end_time = highlight.get("end_time", 0)
            
            processor.extract_clip(start_time, end_time, clip_path)
            
            # Extract thumbnail
            thumbnail_filename = f"{highlight_id}.jpg"
            thumbnail_path = os.path.join("thumbnails", thumbnail_filename)
            
            thumbnail_time = start_time + ((end_time - start_time) / 2)
            processor.extract_thumbnail(thumbnail_time, thumbnail_path)
            
            # Generate subtitles
            subtitle_filename = f"{highlight_id}.vtt"
            subtitle_path = os.path.join("subtitles", subtitle_filename)
            
            subtitles = await ai_analyzer.generate_subtitles(clip_path)
            
            with open(subtitle_path, "w") as f:
                f.write(subtitles)
            
            # Create highlight object
            highlight_clip = HighlightClip(
                id=highlight_id,
                video_id=video_id,
                title=highlight.get("title", f"Highlight {i+1}"),
                description=highlight.get("description", ""),
                start_time=start_time,
                end_time=end_time,
                clip_path=clip_path,
                subtitle_path=subtitle_path,
                thumbnail_path=thumbnail_path
            )
            
            highlight_clips.append(highlight_clip)
            highlights_db[highlight_id] = highlight_clip
        
        # Generate content plan
        processing_status_db[video_id] = ProcessingStatus(
            video_id=video_id,
            status="GENERATING_CONTENT_PLAN"
        )
        
        content_plan = await ai_analyzer.generate_content_plan(highlight_clips)
        content_plans_db[video_id] = content_plan
        
        # Save content plan to file
        content_plan_filename = f"{video_id}_content_plan.json"
        content_plan_path = os.path.join("content_plans", content_plan_filename)
        
        videos_db[video_id].content_plan_path = content_plan_path
        videos_db[video_id].highlights_count = len(highlight_clips)
        videos_db[video_id].processing_status = "COMPLETED"
        
        # Update status
        processing_status_db[video_id] = ProcessingStatus(
            video_id=video_id,
            status="COMPLETED"
        )
        
    except Exception as e:
        print(f"Error processing video {video_id}: {str(e)}")
        videos_db[video_id].processing_status = "ERROR"
        videos_db[video_id].error_message = str(e)
        
        processing_status_db[video_id] = ProcessingStatus(
            video_id=video_id,
            status="ERROR"
        )

@app.post("/api/upload", response_model=VideoMetadata)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None)
):
    # Check file type
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only MP4, MOV, and AVI files are supported.")
    
    # Generate unique ID for the video
    video_id = str(uuid.uuid4())
    
    # Create upload directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join("uploads", f"{video_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create video metadata
    video_metadata = VideoMetadata(
        id=video_id,
        title=title,
        description=description,
        original_filename=file.filename,
        upload_path=file_path,
        file_type=file.content_type,
        upload_date=datetime.now().isoformat(),
        processing_status="PROCESSING",
        error_message=None,
        duration=None,
        frames=None,
        highlights_count=None,
        content_plan_path=None
    )
    
    # Save to database
    videos_db[video_id] = video_metadata
    
    # Start processing in background
    background_tasks.add_task(process_video, video_id, file_path)
    
    return video_metadata

@app.get("/api/status/{video_id}", response_model=ProcessingStatus)
async def get_processing_status(video_id: str):
    if video_id not in processing_status_db:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return processing_status_db[video_id]

@app.get("/api/videos/{video_id}", response_model=VideoMetadata)
async def get_video(video_id: str):
    if video_id not in videos_db:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return videos_db[video_id]

@app.get("/api/videos", response_model=List[VideoMetadata])
async def get_videos():
    return list(videos_db.values())

@app.get("/api/videos/{video_id}/highlights", response_model=List[HighlightClip])
async def get_highlights(video_id: str):
    if video_id not in videos_db:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return [h for h in highlights_db.values() if h.video_id == video_id]

@app.get("/api/videos/{video_id}/content_plan", response_model=ContentPlan)
async def get_content_plan(video_id: str):
    if video_id not in videos_db:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video_id not in content_plans_db:
        raise HTTPException(status_code=404, detail="Content plan not found")
    
    return content_plans_db[video_id]

@app.delete("/api/videos/{video_id}")
async def delete_video(video_id: str):
    if video_id not in videos_db:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get video data
    video = videos_db[video_id]
    
    # Delete the video file
    if os.path.exists(video.upload_path):
        os.remove(video.upload_path)
    
    # Delete highlights
    highlights = [h for h in highlights_db.values() if h.video_id == video_id]
    
    for highlight in highlights:
        # Delete clip
        if os.path.exists(highlight.clip_path):
            os.remove(highlight.clip_path)
        
        # Delete thumbnail
        if highlight.thumbnail_path and os.path.exists(highlight.thumbnail_path):
            os.remove(highlight.thumbnail_path)
        
        # Delete subtitle
        if highlight.subtitle_path and os.path.exists(highlight.subtitle_path):
            os.remove(highlight.subtitle_path)
        
        # Remove from database
        if highlight.id in highlights_db:
            del highlights_db[highlight.id]
    
    # Delete content plan
    if video_id in content_plans_db:
        del content_plans_db[video_id]
    
    # Delete from database
    del videos_db[video_id]
    
    if video_id in processing_status_db:
        del processing_status_db[video_id]
    
    return {"message": "Video deleted successfully"}

# Optional: Endpoints for publishing to social media
@app.post("/api/publish/youtube/{clip_id}")
async def publish_to_youtube(clip_id: str):
    if clip_id not in highlights_db:
        raise HTTPException(status_code=404, detail="Highlight clip not found")
    
    # This would integrate with the YouTube API
    # For now, just return a placeholder response
    return {"message": "YouTube publishing feature coming soon", "status": "pending"}

@app.post("/api/publish/instagram/{clip_id}")
async def publish_to_instagram(clip_id: str):
    if clip_id not in highlights_db:
        raise HTTPException(status_code=404, detail="Highlight clip not found")
    
    # This would integrate with the Instagram API
    # For now, just return a placeholder response
    return {"message": "Instagram publishing feature coming soon", "status": "pending"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)