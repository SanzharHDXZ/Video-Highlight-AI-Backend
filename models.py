from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class VideoMetadata(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    original_filename: str
    upload_path: str
    file_type: str
    upload_date: str
    processing_status: str  # "PROCESSING", "COMPLETED", "ERROR"
    error_message: Optional[str] = None
    duration: Optional[float] = None
    frames: Optional[int] = None
    highlights_count: Optional[int] = None
    content_plan_path: Optional[str] = None

class HighlightClip(BaseModel):
    id: str
    video_id: str
    title: str
    description: Optional[str] = None
    start_time: float
    end_time: float
    clip_path: str
    subtitle_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

class ContentPost(BaseModel):
    clip_id: str
    title: str
    caption: str
    platform: str  # "INSTAGRAM", "YOUTUBE", "TIKTOK", etc.
    suggested_posting_date: Optional[str] = None
    hashtags: List[str] = []

class ContentPlan(BaseModel):
    video_id: str
    title: str
    generated_date: str
    posts: List[ContentPost] = []

class ProcessingStatus(BaseModel):
    video_id: str
    status: str  # "PROCESSING", "ANALYZING", "EXTRACTING_HIGHLIGHTS", "GENERATING_CONTENT_PLAN", "COMPLETED", "ERROR"