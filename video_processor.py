import os
import subprocess
from typing import Optional
from moviepy.editor import VideoFileClip

class VideoProcessor:
    def __init__(self, video_path: str):
        """Initialize the video processor with a video file path."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.video_path = video_path
        self.video_clip = VideoFileClip(video_path)
    
    def get_duration(self) -> float:
        """Get the duration of the video in seconds."""
        return self.video_clip.duration
    
    def get_frame_count(self) -> int:
        """Get the total number of frames in the video."""
        fps = self.video_clip.fps
        duration = self.video_clip.duration
        return int(fps * duration)
    
    def extract_clip(self, start_time: float, end_time: float, output_path: str) -> str:
        """
        Extract a clip from the video between start_time and end_time.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Path to save the extracted clip
            
        Returns:
            Path to the extracted clip
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract the subclip
        subclip = self.video_clip.subclip(start_time, end_time)
        
        # Optimize for social media (square format, shorter duration if needed)
        # For Instagram Reels or TikTok, you might want to crop to 9:16
        # Here we're keeping the original aspect ratio
        
        # Save the clip
        subclip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='ultrafast'  # Use 'medium' or 'slow' for better quality in production
        )
        
        return output_path
    
    def extract_thumbnail(self, time: float, output_path: str) -> str:
        """
        Extract a thumbnail from the video at the specified time.
        
        Args:
            time: Time in seconds
            output_path: Path to save the thumbnail
            
        Returns:
            Path to the thumbnail
        """
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract the frame
        frame = self.video_clip.get_frame(time)
        
        # Save the frame as an image
        from PIL import Image
        import numpy as np
        
        img = Image.fromarray(np.uint8(frame))
        img.save(output_path)
        
        return output_path
    
    def __del__(self):
        """Close the video clip when the processor is deleted."""
        if hasattr(self, 'video_clip') and self.video_clip is not None:
            self.video_clip.close()

    def add_subtitles(self, subtitle_path: str, output_path: Optional[str] = None) -> str:
        """
        Add subtitles to the video.
        
        Args:
            subtitle_path: Path to the subtitle file (.srt or .vtt)
            output_path: Path to save the video with subtitles
            
        Returns:
            Path to the video with subtitles
        """
        if output_path is None:
            base, ext = os.path.splitext(self.video_path)
            output_path = f"{base}_subtitled{ext}"
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use ffmpeg to add subtitles
        command = [
            'ffmpeg',
            '-i', self.video_path,
            '-vf', f'subtitles={subtitle_path}',
            '-c:a', 'copy',
            output_path
        ]
        
        subprocess.run(command, check=True)
        
        return output_path