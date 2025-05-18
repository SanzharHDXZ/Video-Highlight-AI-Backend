import os
import json
import base64
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import google.generativeai as genai
from google.oauth2 import service_account
from models import ContentPlan, ContentPost, HighlightClip

class GeminiAIAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini AI Analyzer with Google API credentials."""
        # Try to get API key from environment variable if not provided
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        
        if not self.api_key:
            # Look for service account credentials file
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path and os.path.exists(creds_path):
                self.credentials = service_account.Credentials.from_service_account_file(creds_path)
            else:
                raise ValueError(
                    "No API key or credentials found. Set GOOGLE_API_KEY environment variable "
                    "or provide a service account credentials file path in GOOGLE_APPLICATION_CREDENTIALS."
                )
        else:
            # Configure the Gemini AI client with API key
            genai.configure(api_key=self.api_key)
    
    async def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze a video to detect highlights using Gemini AI.
        
        This is a simplified implementation. In a real application, you would:
        1. Extract audio and convert to text
        2. Extract frames at regular intervals
        3. Send both to Gemini AI for multimodal analysis
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dict with analysis results including highlighted moments
        """
        # Extract a few frames and audio for demo purposes
        # In a real implementation, you'd process the entire video
        
        from moviepy.editor import VideoFileClip
        import numpy as np
        from PIL import Image
        import io
        
        # Load video
        video = VideoFileClip(video_path)
        duration = video.duration
        
        # Extract frames at regular intervals (just for demo)
        frame_times = [duration * i / 5 for i in range(1, 5)]
        frames = [video.get_frame(t) for t in frame_times]
        
        # Convert frames to base64 for API
        frame_bases64 = []
        for frame in frames:
            img = Image.fromarray(np.uint8(frame))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            frame_bases64.append(img_str)
        
        # Extract audio and convert to text (simplified)
        # In reality, you would use a speech-to-text service
        audio_text = "This is placeholder text for speech-to-text conversion."
        
        # Create a prompt for Gemini
        prompt = f"""
        You are a video analysis AI. Analyze the following video frames and transcribed audio to identify 
        the most engaging moments that would make good highlights or clips for social media.
        
        The video is {duration} seconds long.
        
        Transcribed audio: {audio_text}
        
        Identify 3-5 highlight moments with start and end times. For each highlight:
        1. Estimate the best start and end time based on natural breaks in content
        2. Create a title for the highlight
        3. Write a short description
        4. Explain why this moment would be engaging on social media
        
        Format your response as a JSON object with a "highlighted_moments" array, where each item has:
        - start_time (in seconds)
        - end_time (in seconds)
        - title (string)
        - description (string)
        - engagement_reason (string)
        """
        
        # Initialize Gemini model - using gemini-pro-vision for multimodal capabilities
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare multimodal content with both text and images
        # This would be properly implemented in a production system
        # For now, we'll use a simplified approach
        response = await asyncio.to_thread(
            model.generate_content,
            [prompt, *[{"mime_type": "image/jpeg", "data": img} for img in frame_bases64[:2]]]  # Only send a couple frames as example
        )
        
        try:
            # Try to parse the response as JSON
            response_text = response.text
            # Find JSON content if wrapped in markdown code blocks
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_content)
            elif "```" in response_text:
                json_content = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_content)
            else:
                # Try to parse the whole response as JSON
                return json.loads(response_text)
        except (json.JSONDecodeError, IndexError):
            # If parsing fails, create a mock response with simulated highlights
            # This is just for demo purposes
            mock_highlights = []
            segment_duration = duration / 5
            
            for i in range(3):
                start_time = i * segment_duration + random.uniform(0, segment_duration * 0.3)
                end_time = start_time + random.uniform(segment_duration * 0.5, segment_duration * 0.8)
                
                if end_time > duration:
                    end_time = duration
                
                mock_highlights.append({
                    "start_time": start_time,
                    "end_time": end_time,
                    "title": f"Highlight Moment {i+1}",
                    "description": f"This is an automatically detected highlight from the video.",
                    "engagement_reason": "This moment contains significant visual or audio elements that may engage viewers."
                })
            
            return {"highlighted_moments": mock_highlights}
    
    async def generate_subtitles(self, clip_path: str) -> str:
        """
        Generate subtitles for a video clip using Gemini AI.
        
        In a real implementation, you would:
        1. Extract audio and convert to text using a speech-to-text service
        2. Format the text as subtitles with proper timing
        
        Args:
            clip_path: Path to the video clip
            
        Returns:
            Subtitles in WebVTT format
        """
        # Extract audio from the clip
        from moviepy.editor import VideoFileClip
        
        # Load clip
        clip = VideoFileClip(clip_path)
        duration = clip.duration
        
        # In a real implementation, you would extract audio and convert to text
        # For demo purposes, we'll create mock subtitles
        
        # Initialize Gemini model - text-only is fine for this use case
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a subtitle generation AI. Create realistic subtitles for a video clip that is {duration} seconds long.
        The clip is likely a highlight from a longer video. Create subtitles that would make sense for such a clip.
        
        Format your response as WebVTT subtitles, with appropriate timestamps. For example:
        
        WEBVTT
        
        00:00:00.000 --> 00:00:02.500
        Hello, welcome to this video!
        
        00:00:02.800 --> 00:00:05.200
        Today we're going to discuss an important topic.
        
        Make sure to cover the entire duration of the clip, which is {duration} seconds.
        Only respond with the WebVTT content, nothing else.
        """
        
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        # Extract the WebVTT content
        subtitles = response.text
        
        # Clean up the response if needed
        if "```" in subtitles:
            subtitles = subtitles.split("```")[1].strip()
        
        if not subtitles.startswith("WEBVTT"):
            subtitles = "WEBVTT\n\n" + subtitles
        
        return subtitles
    
    async def generate_content_plan(self, highlights: List[HighlightClip]) -> ContentPlan:
        """
        Generate a content plan for posting the highlights on social media.
        
        Args:
            highlights: List of highlight clips
            
        Returns:
            Content plan with suggested posting dates and captions
        """
        if not highlights:
            raise ValueError("No highlights provided for content plan generation")
        
        # Initialize Gemini model - text-only is sufficient for content planning
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare highlight information for the prompt
        highlights_info = []
        for i, highlight in enumerate(highlights):
            highlights_info.append(f"""
            Highlight {i+1}:
            - Title: {highlight.title}
            - Description: {highlight.description}
            - Duration: {highlight.end_time - highlight.start_time:.2f} seconds
            """)
        
        highlights_text = "\n".join(highlights_info)
        
        prompt = f"""
        You are a social media content planner. Create a posting schedule and captions for the following video highlights.
        These highlights will be posted across different social media platforms.
        
        {highlights_text}
        
        For each highlight, create:
        1. An engaging title suitable for social media
        2. A caption that describes the content and encourages engagement
        3. A recommended platform (Instagram, YouTube, TikTok, etc.)
        4. 3-5 relevant hashtags
        5. A suggested posting date (starting from tomorrow and spaced appropriately)
        
        Format your response as a JSON object with a "content_plan" array, where each item includes:
        - clip_id (string, use the index number)
        - title (string)
        - caption (string)
        - platform (string)
        - suggested_posting_date (string in YYYY-MM-DD format)
        - hashtags (array of strings)
        
        Only provide the JSON object, no additional text.
        """
        
        response = await asyncio.to_thread(
            model.generate_content,
            prompt
        )
        
        try:
            # Try to parse the response as JSON
            response_text = response.text
            
            # Find JSON content if wrapped in markdown code blocks
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
                parsed_plan = json.loads(json_content)
            elif "```" in response_text:
                json_content = response_text.split("```")[1].split("```")[0].strip()
                parsed_plan = json.loads(json_content)
            else:
                # Try to parse the whole response as JSON
                parsed_plan = json.loads(response_text)
            
            # Create ContentPlan object
            content_plan = ContentPlan(
                video_id=highlights[0].video_id,
                title=f"Content Plan for {len(highlights)} Highlights",
                generated_date=datetime.now().isoformat(),
                posts=[]
            )
            
            # Get the plan items from the response
            plan_items = parsed_plan.get("content_plan", [])
            
            # Create ContentPost objects for each item
            for i, item in enumerate(plan_items):
                if i >= len(highlights):
                    break
                    
                # Get the corresponding highlight
                highlight = highlights[i]
                
                post = ContentPost(
                    clip_id=highlight.id,
                    title=item.get("title", highlight.title),
                    caption=item.get("caption", "Check out this highlight!"),
                    platform=item.get("platform", "Instagram"),
                    suggested_posting_date=item.get("suggested_posting_date", 
                                                  (datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d")),
                    hashtags=item.get("hashtags", ["video", "highlights", "content"])
                )
                
                content_plan.posts.append(post)
            
            return content_plan
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # If parsing fails, create a simple content plan
            content_plan = ContentPlan(
                video_id=highlights[0].video_id,
                title=f"Content Plan for {len(highlights)} Highlights",
                generated_date=datetime.now().isoformat(),
                posts=[]
            )
            
            # Create a basic plan for each highlight
            for i, highlight in enumerate(highlights):
                post = ContentPost(
                    clip_id=highlight.id,
                    title=f"Highlight {i+1}: {highlight.title}",
                    caption=f"Check out this amazing highlight from our video! {highlight.description}",
                    platform="Instagram" if i % 2 == 0 else "YouTube",
                    suggested_posting_date=(datetime.now() + timedelta(days=i+1)).strftime("%Y-%m-%d"),
                    hashtags=["video", "highlights", "content", f"part{i+1}"]
                )
                
                content_plan.posts.append(post)
            
            return content_plan