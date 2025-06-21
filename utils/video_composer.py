import os
import cv2
import numpy as np
try:
    from moviepy.editor import (
        VideoClip, ImageClip, AudioFileClip, CompositeVideoClip,
        TextClip, concatenate_videoclips
    )
    from moviepy.video.fx.all import resize
    MOVIEPY_AVAILABLE = True
except ImportError:
    # Create dummy classes to prevent NameError
    class VideoClip:
        pass
    class ImageClip:
        pass
    class AudioFileClip:
        pass
    class CompositeVideoClip:
        pass
    class TextClip:
        pass
    
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not available. Video creation will be disabled.")
from PIL import Image, ImageDraw, ImageFont
import tempfile
from typing import List, Tuple, Optional, Dict
from config import Config

class VideoComposer:
    def __init__(self):
        self.temp_files = []
        self.available = MOVIEPY_AVAILABLE
    
    def create_video(self, 
                    image_path: str, 
                    audio_path: str, 
                    script_text: str,
                    output_path: str,
                    background_music_path: Optional[str] = None,
                    style: str = "modern") -> bool:
        """
        Create a complete video with image, audio, subtitles, and effects
        
        Args:
            image_path: Path to the main image
            audio_path: Path to the voiceover audio
            script_text: Text for subtitles
            output_path: Output video path
            background_music_path: Optional background music
            style: Visual style (modern, classic, dramatic)
        
        Returns:
            Boolean indicating success
        """
        if not self.available:
            print("❌ MoviePy not available. Cannot create video.")
            return False
            
        try:
            # Load and prepare audio
            audio_clip = AudioFileClip(audio_path)
            video_duration = audio_clip.duration + Config.VIDEO_DURATION_BUFFER
            
            # Create video clip from image
            video_clip = self._create_image_video(image_path, video_duration, style)
            
            # Add subtitles
            subtitle_clips = self._create_subtitle_clips(script_text, video_duration, style)
            
            # Combine video with subtitles
            final_video = CompositeVideoClip([video_clip] + subtitle_clips)
            
            # Add voiceover audio
            final_video = final_video.set_audio(audio_clip)
            
            # Add background music if provided
            if background_music_path and os.path.exists(background_music_path):
                final_video = self._add_background_music(final_video, background_music_path)
            
            # Apply final effects
            final_video = self._apply_final_effects(final_video, style)
            
            # Write final video
            final_video.write_videofile(
                output_path,
                fps=Config.VIDEO_FPS,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile=tempfile.mktemp(suffix='.m4a'),
                remove_temp=True
            )
            
            # Clean up
            audio_clip.close()
            final_video.close()
            self._cleanup_temp_files()
            
            return True
            
        except Exception as e:
            print(f"Error creating video: {e}")
            self._cleanup_temp_files()
            return False
    
    def _create_image_video(self, image_path: str, duration: float, style: str) -> VideoClip:
        """Create a video clip from a static image with effects"""
        # Load and process image
        img = Image.open(image_path)
        
        # Resize image to fit video dimensions while maintaining aspect ratio
        img_resized = self._resize_image_for_video(img)
        
        # Create background
        background = self._create_styled_background(img_resized, style)
        
        # Save processed image
        temp_img_path = tempfile.mktemp(suffix='.jpg')
        background.save(temp_img_path, 'JPEG')
        self.temp_files.append(temp_img_path)
        
        # Create video clip
        video_clip = ImageClip(temp_img_path, duration=duration)
        
        # Apply motion effects based on style
        if style == "modern":
            # Subtle zoom effect
            video_clip = video_clip.resize(lambda t: 1 + 0.02 * t / duration)
        elif style == "dramatic":
            # Ken Burns effect (zoom + pan)
            video_clip = video_clip.resize(lambda t: 1 + 0.05 * t / duration)
            video_clip = video_clip.set_position(lambda t: ((-10 * t / duration), 0))
        
        return video_clip
    
    def _resize_image_for_video(self, img: Image.Image) -> Image.Image:
        """Resize image to fit video dimensions while maintaining aspect ratio"""
        video_aspect = Config.VIDEO_WIDTH / Config.VIDEO_HEIGHT
        img_aspect = img.width / img.height
        
        if img_aspect > video_aspect:
            # Image is wider - fit by height
            new_height = Config.VIDEO_HEIGHT
            new_width = int(new_height * img_aspect)
        else:
            # Image is taller - fit by width
            new_width = Config.VIDEO_WIDTH
            new_height = int(new_width / img_aspect)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _create_styled_background(self, img: Image.Image, style: str) -> Image.Image:
        """Create a styled background for the image"""
        # Create canvas
        canvas = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), (0, 0, 0))
        
        # Apply style-specific background
        if style == "modern":
            # Gradient background
            canvas = self._create_gradient_background()
        elif style == "classic":
            # Solid color background
            canvas = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT), (20, 20, 30))
        elif style == "dramatic":
            # Dark gradient with subtle texture
            canvas = self._create_dramatic_background()
        
        # Center the image on the canvas
        paste_x = (Config.VIDEO_WIDTH - img.width) // 2
        paste_y = (Config.VIDEO_HEIGHT - img.height) // 2
        
        # Add subtle shadow effect
        if style in ["modern", "dramatic"]:
            shadow = Image.new('RGBA', img.size, (0, 0, 0, 50))
            canvas.paste(shadow, (paste_x + 5, paste_y + 5), shadow)
        
        canvas.paste(img, (paste_x, paste_y))
        
        return canvas
    
    def _create_gradient_background(self) -> Image.Image:
        """Create a modern gradient background"""
        img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(img)
        
        # Create gradient from top to bottom
        for y in range(Config.VIDEO_HEIGHT):
            ratio = y / Config.VIDEO_HEIGHT
            r = int(15 + ratio * 10)  # Dark blue to slightly lighter
            g = int(25 + ratio * 15)
            b = int(45 + ratio * 20)
            draw.line([(0, y), (Config.VIDEO_WIDTH, y)], fill=(r, g, b))
        
        return img
    
    def _create_dramatic_background(self) -> Image.Image:
        """Create a dramatic dark background"""
        img = Image.new('RGB', (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(img)
        
        # Create radial gradient
        center_x, center_y = Config.VIDEO_WIDTH // 2, Config.VIDEO_HEIGHT // 2
        max_radius = max(Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT) // 2
        
        for radius in range(max_radius, 0, -10):
            intensity = 1 - (radius / max_radius)
            color_val = int(5 + intensity * 15)
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], fill=(color_val, color_val, color_val + 5))
        
        return img
    
    def _create_subtitle_clips(self, text: str, duration: float, style: str) -> List[VideoClip]:
        """Create subtitle clips with timing"""
        words = text.split()
        words_per_second = len(words) / duration
        
        # Create subtitle segments (every 3-4 seconds)
        segment_duration = 3.5
        segments = []
        words_per_segment = int(words_per_second * segment_duration)
        
        for i in range(0, len(words), words_per_segment):
            segment_words = words[i:i + words_per_segment]
            segment_text = ' '.join(segment_words)
            
            start_time = i / words_per_second
            end_time = min(start_time + segment_duration, duration)
            
            if segment_text.strip():
                subtitle_clip = self._create_subtitle_clip(
                    segment_text, start_time, end_time - start_time, style
                )
                segments.append(subtitle_clip)
        
        return segments
    
    def _create_subtitle_clip(self, text: str, start_time: float, duration: float, style: str) -> VideoClip:
        """Create a single subtitle clip"""
        # Style configurations
        style_configs = {
            "modern": {
                "fontsize": 48,
                "color": "white",
                "stroke_color": "black",
                "stroke_width": 2,
                "font": "Arial-Bold"
            },
            "classic": {
                "fontsize": 44,
                "color": "white",
                "stroke_color": "black",
                "stroke_width": 1,
                "font": "Arial"
            },
            "dramatic": {
                "fontsize": 52,
                "color": "yellow",
                "stroke_color": "black",
                "stroke_width": 3,
                "font": "Arial-Bold"
            }
        }
        
        config = style_configs.get(style, style_configs["modern"])
        
        # Create text clip
        txt_clip = TextClip(
            text,
            fontsize=config["fontsize"],
            color=config["color"],
            stroke_color=config["stroke_color"],
            stroke_width=config["stroke_width"],
            font=config["font"],
            method='caption',
            size=(Config.VIDEO_WIDTH - 100, None)  # Leave margins
        )
        
        # Position at bottom of screen
        txt_clip = txt_clip.set_position(('center', Config.VIDEO_HEIGHT - 150))
        txt_clip = txt_clip.set_start(start_time).set_duration(duration)
        
        # Add fade in/out effects
        if duration > 0.5:
            txt_clip = txt_clip.crossfadein(0.2).crossfadeout(0.2)
        
        return txt_clip
    
    def _add_background_music(self, video_clip: VideoClip, music_path: str) -> VideoClip:
        """Add background music to the video"""
        try:
            music = AudioFileClip(music_path)
            
            # Adjust music duration to match video
            if music.duration > video_clip.duration:
                music = music.subclip(0, video_clip.duration)
            else:
                # Loop music if it's shorter than video
                music = music.loop(duration=video_clip.duration)
            
            # Lower the volume of background music
            music = music.volumex(0.3)
            
            # Combine original audio with background music
            final_audio = CompositeAudioClip([video_clip.audio, music])
            
            return video_clip.set_audio(final_audio)
            
        except Exception as e:
            print(f"Error adding background music: {e}")
            return video_clip
    
    def _apply_final_effects(self, video_clip: VideoClip, style: str) -> VideoClip:
        """Apply final visual effects based on style"""
        if style == "dramatic":
            # Add slight color grading
            video_clip = video_clip.fx(colorx, 1.1)  # Increase saturation slightly
        elif style == "classic":
            # Add subtle sepia tone
            video_clip = video_clip.fx(colorx, 0.9)
        
        # Add fade in/out
        video_clip = video_clip.crossfadein(0.5).crossfadeout(0.5)
        
        return video_clip
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")
        self.temp_files = [] 