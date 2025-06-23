import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
import shutil

from config import Config
from utils.script_generator import ScriptGenerator
from utils.tts_engine import TTSEngine
from utils.video_composer import VideoComposer


class AutoVideoGenerator:
    def __init__(self):
        """Initialize the video generator with all components"""
        self.script_generator = ScriptGenerator()
        self.tts_engine = TTSEngine()
        self.video_composer = VideoComposer()
        
        # Create necessary directories
        self._setup_directories()
    
    def _setup_directories(self):
        """Create required directories if they don't exist"""
        directories = [
            Config.UPLOAD_DIR,
            Config.OUTPUT_DIR,
            Config.TEMP_DIR,
            Config.ASSETS_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def generate_video(self,
                      image_path: str,
                      news_topic: str,
                      duration: int = 30,
                      style: str = "modern",
                      voice_provider: str = "auto",
                      background_music_path: Optional[str] = None,
                      voice_samples_dir: Optional[str] = None) -> Dict:
        """
        Generate a complete news video from image and topic
        
        Args:
            image_path: Path to the portrait/image
            news_topic: News headline or topic
            duration: Target duration in seconds
            style: Visual style (modern, classic, dramatic)
            voice_provider: TTS provider (auto, elevenlabs, azure, cloned)
            background_music_path: Optional background music file
            voice_samples_dir: Directory with voice samples for cloning
        
        Returns:
            Dictionary with generation results and file paths
        """
        try:
            # Validate inputs
            if not os.path.exists(image_path):
                return {"success": False, "error": "Image file not found"}
            
            if not news_topic.strip():
                return {"success": False, "error": "News topic is required"}
            
            # Generate unique filename for this video
            import uuid
            video_id = str(uuid.uuid4())[:8]
            base_filename = f"news_video_{video_id}"
            
            # File paths
            audio_path = os.path.join(Config.TEMP_DIR, f"{base_filename}_audio.mp3")
            output_path = os.path.join(Config.OUTPUT_DIR, f"{base_filename}.mp4")
            
            # Step 1: Generate script
            print("🤖 Generating news script...")
            script = self.script_generator.generate_news_script(
                topic=news_topic,
                duration_seconds=duration,
                style=style.lower()
            )
            
            if not script:
                return {"success": False, "error": "Failed to generate script"}
            
            # Analyze script timing
            timing_info = self.script_generator.analyze_script_timing(script)
            print(f"📝 Script generated: {timing_info['word_count']} words, "
                  f"~{timing_info['estimated_duration_seconds']}s")
            
            # Step 2: Generate voiceover
            print("🗣️ Generating voiceover...")
            tts_success = self.tts_engine.generate_speech(
                text=script,
                output_path=audio_path,
                voice_provider=voice_provider,
                voice_samples_dir=voice_samples_dir
            )
            
            if not tts_success:
                return {"success": False, "error": "Failed to generate voiceover"}
            
            # Get actual audio duration
            actual_duration = self.tts_engine.get_audio_duration(audio_path)
            print(f"🎵 Voiceover generated: {actual_duration:.1f}s")
            
            # Step 3: Create video
            print("🎬 Creating video...")
            video_success = self.video_composer.create_video(
                image_path=image_path,
                audio_path=audio_path,
                script_text=script,
                output_path=output_path,
                background_music_path=background_music_path,
                style=style
            )
            
            if not video_success:
                return {"success": False, "error": "Failed to create video"}
            
            # Cleanup temporary files
            try:
                os.remove(audio_path)
            except:
                pass
            
            print(f"✅ Video created successfully: {output_path}")
            
            return {
                "success": True,
                "video_path": output_path,
                "script": script,
                "timing_info": timing_info,
                "actual_duration": actual_duration,
                "style": style,
                "voice_provider": voice_provider
            }
            
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            return {"success": False, "error": str(e)}
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get information about a generated video"""
        if not os.path.exists(video_path):
            return {"exists": False}
        
        file_size = os.path.getsize(video_path)
        file_size_mb = file_size / (1024 * 1024)
        
        return {
            "exists": True,
            "path": video_path,
            "size_bytes": file_size,
            "size_mb": round(file_size_mb, 2),
            "filename": os.path.basename(video_path)
        }
    
    def get_available_voices(self) -> Dict:
        """Get available TTS providers and their status"""
        providers = self.tts_engine.get_available_providers()
        
        return {
            "providers": providers,
            "elevenlabs_available": "elevenlabs" in providers,
            "azure_available": "azure" in providers,
            "recommended": providers[0] if providers else "basic"
        }
    
    def validate_setup(self) -> Dict:
        """Validate that all required components are properly configured"""
        issues = []
        
        # Check API keys
        missing_keys = Config.validate_keys()
        if missing_keys:
            issues.append(f"Missing API keys: {', '.join(missing_keys)}")
        
        # Check directories
        for directory in [Config.UPLOAD_DIR, Config.OUTPUT_DIR, Config.TEMP_DIR]:
            if not os.path.exists(directory):
                issues.append(f"Directory not found: {directory}")
        
        # Check TTS availability
        voice_info = self.get_available_voices()
        if voice_info["providers"] == ["basic"]:
            issues.append("No premium TTS providers available (only basic fallback)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "voice_providers": voice_info["providers"]
        }
    
    def cleanup_old_files(self, days_old: int = 7):
        """Clean up old temporary and output files"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        directories_to_clean = [Config.TEMP_DIR, Config.OUTPUT_DIR]
        cleaned_files = []
        
        for directory in directories_to_clean:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        if file_time < cutoff_time:
                            try:
                                os.remove(file_path)
                                cleaned_files.append(file_path)
                            except Exception as e:
                                print(f"Error cleaning {file_path}: {e}")
        
        return cleaned_files
    
    def extract_voice_from_video(self, video_path: str, output_path: str) -> Dict:
        """Extract voice from video file"""
        return self.tts_engine.extract_voice_from_video(video_path, output_path)
    
    def extract_voice_from_audio(self, audio_path: str, output_path: str) -> Dict:
        """Extract and process voice from audio file"""
        return self.tts_engine.extract_voice_from_audio(audio_path, output_path)
    
    def record_voice_from_microphone(self, duration: int, output_path: str, 
                                   gain_multiplier: float = 1.0,
                                   device_index: Optional[int] = None,
                                   progress_callback: Optional[callable] = None) -> Dict:
        """Record voice from microphone with gain control and progress tracking"""
        return self.tts_engine.record_voice_from_microphone(
            duration=duration, 
            output_path=output_path,
            gain_multiplier=gain_multiplier,
            device_index=device_index,
            progress_callback=progress_callback
        )
    
    def create_voice_samples_from_media(self, media_path: str, media_type: str = "auto") -> Dict:
        """
        Create voice samples from video or audio file
        
        Args:
            media_path: Path to video or audio file
            media_type: "video", "audio", or "auto" for automatic detection
            
        Returns:
            Dictionary with voice sample creation results
        """
        try:
            import uuid
            session_id = str(uuid.uuid4())[:8]
            temp_audio_path = os.path.join(Config.TEMP_DIR, f"extracted_audio_{session_id}.wav")
            voice_samples_dir = os.path.join(Config.TEMP_DIR, f"voice_samples_{session_id}")
            
            # Detect media type if auto
            if media_type == "auto":
                file_ext = os.path.splitext(media_path)[1].lower()
                if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                    media_type = "video"
                elif file_ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
                    media_type = "audio"
                else:
                    return {"success": False, "error": "Unsupported file format"}
            
            # Extract audio from media
            if media_type == "video":
                extraction_result = self.extract_voice_from_video(media_path, temp_audio_path)
            else:
                extraction_result = self.extract_voice_from_audio(media_path, temp_audio_path)
            
            if not extraction_result.get("success"):
                return extraction_result
            
            # Create voice samples
            samples_result = self.tts_engine.create_voice_samples(temp_audio_path, voice_samples_dir)
            
            # Add session info
            if samples_result.get("success"):
                samples_result["session_id"] = session_id
                samples_result["voice_samples_dir"] = voice_samples_dir
                samples_result["extracted_audio_path"] = temp_audio_path
                samples_result["source_media"] = media_path
                samples_result["media_type"] = media_type
            
            return samples_result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_available_microphones(self) -> List[Dict]:
        """Get available microphones"""
        return self.tts_engine.get_available_microphones()
    
    def test_microphone(self, device_index: Optional[int] = None) -> Dict:
        """Test microphone functionality"""
        return self.tts_engine.test_microphone(device_index)
    
    def start_audio_monitoring(self, device_index: Optional[int] = None, 
                             gain_multiplier: float = 1.0) -> Dict:
        """Start real-time audio level monitoring"""
        return self.tts_engine.start_audio_monitoring(
            device_index=device_index,
            gain_multiplier=gain_multiplier
        )
    
    def stop_audio_monitoring(self) -> Dict:
        """Stop audio monitoring"""
        return self.tts_engine.stop_audio_monitoring()
    
    def get_current_audio_level(self) -> Dict:
        """Get current audio level from monitoring thread"""
        return self.tts_engine.get_current_audio_level()
    
    def get_audio_level_preview(self, device_index: Optional[int] = None, 
                              gain_multiplier: float = 1.0, 
                              duration: float = 0.1) -> Dict:
        """Get a quick audio level preview"""
        return self.tts_engine.get_audio_level_preview(
            device_index=device_index,
            gain_multiplier=gain_multiplier,
            duration=duration
        ) 