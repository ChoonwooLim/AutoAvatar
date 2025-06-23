import os
import tempfile
from typing import Optional, Union, Dict, List
import requests
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    speechsdk = None
    AZURE_AVAILABLE = False
    print("⚠️ Azure Speech SDK not available. Azure TTS will be disabled.")
try:
    from elevenlabs import generate, set_api_key
except ImportError:
    try:
        from elevenlabs.client import ElevenLabs
        generate = None  # Will be handled differently
        set_api_key = None
    except ImportError:
        generate = None
        set_api_key = None
from pydub import AudioSegment
from config import Config
from .voice_cloner import VoiceCloner

class TTSEngine:
    def __init__(self):
        self.elevenlabs_available = bool(Config.ELEVENLABS_API_KEY) and (generate is not None)
        self.azure_available = bool(Config.AZURE_SPEECH_KEY) and AZURE_AVAILABLE
        self.elevenlabs_client = None
        
        if self.elevenlabs_available:
            try:
                if set_api_key:
                    set_api_key(Config.ELEVENLABS_API_KEY)
                else:
                    # Use new ElevenLabs client
                    from elevenlabs.client import ElevenLabs
                    self.elevenlabs_client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)
            except Exception as e:
                print(f"ElevenLabs initialization error: {e}")
                self.elevenlabs_available = False
        
        # Initialize voice cloner
        self.voice_cloner = VoiceCloner()
        self.voice_cloner_available = True
        
        if not self.elevenlabs_available and not self.azure_available and not self.voice_cloner_available:
            print("Warning: No TTS options found. Only basic TTS will be available.")
    
    def generate_speech(self, text: str, output_path: str, voice_provider: str = "auto", voice_samples_dir: Optional[str] = None) -> bool:
        """
        Generate speech from text using available TTS services
        
        Args:
            text: Text to convert to speech
            output_path: Output file path for the audio
            voice_provider: "elevenlabs", "azure", "cloned", or "auto" for automatic selection
            voice_samples_dir: Directory containing voice samples for cloning
        
        Returns:
            Boolean indicating success
        """
        if voice_provider == "auto":
            # Auto-select best available provider
            if voice_samples_dir and self.voice_cloner_available:
                voice_provider = "cloned"
            elif self.elevenlabs_available:
                voice_provider = "elevenlabs"
            elif self.azure_available:
                voice_provider = "azure"
            else:
                return self._generate_basic_tts(text, output_path)
        
        try:
            if voice_provider == "cloned" and voice_samples_dir and self.voice_cloner_available:
                return self._generate_cloned_speech(text, output_path, voice_samples_dir)
            elif voice_provider == "elevenlabs" and self.elevenlabs_available:
                return self._generate_elevenlabs_speech(text, output_path)
            elif voice_provider == "azure" and self.azure_available:
                return self._generate_azure_speech(text, output_path)
            else:
                return self._generate_basic_tts(text, output_path)
        except Exception as e:
            print(f"Error generating speech with {voice_provider}: {e}")
            # Fallback to basic TTS
            return self._generate_basic_tts(text, output_path)
    
    def _generate_elevenlabs_speech(self, text: str, output_path: str) -> bool:
        """Generate speech using ElevenLabs API"""
        try:
            if generate:
                # Old API method
                audio = generate(
                    text=text,
                    voice=Config.ELEVENLABS_VOICE_ID,
                    model="eleven_monolingual_v1"
                )
            elif self.elevenlabs_client:
                # New API method
                audio = self.elevenlabs_client.generate(
                    text=text,
                    voice=Config.ELEVENLABS_VOICE_ID,
                    model="eleven_monolingual_v1"
                )
            else:
                return False
            
            with open(output_path, 'wb') as f:
                f.write(audio)
            
            return True
        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return False
    
    def _generate_azure_speech(self, text: str, output_path: str) -> bool:
        """Generate speech using Azure Cognitive Services"""
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=Config.AZURE_SPEECH_KEY,
                region=Config.AZURE_SPEECH_REGION
            )
            speech_config.speech_synthesis_voice_name = Config.AZURE_VOICE_NAME
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None
            )
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                with open(output_path, 'wb') as f:
                    f.write(result.audio_data)
                return True
            else:
                print(f"Azure TTS failed: {result.reason}")
                return False
                
        except Exception as e:
            print(f"Azure TTS error: {e}")
            return False
    
    def _generate_basic_tts(self, text: str, output_path: str) -> bool:
        """Basic TTS fallback using system TTS or simple audio generation"""
        try:
            # This is a placeholder for basic TTS
            # In a real implementation, you might use pyttsx3 or similar
            print(f"Warning: Using fallback TTS for: {text[:50]}...")
            
            # Create a simple silence audio file as placeholder
            silence = AudioSegment.silent(duration=len(text.split()) * 500)  # 500ms per word
            silence.export(output_path, format="mp3")
            
            return True
        except Exception as e:
            print(f"Basic TTS error: {e}")
            return False
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # Convert to seconds
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    
    def adjust_audio_speed(self, input_path: str, output_path: str, speed_factor: float) -> bool:
        """
        Adjust audio playback speed
        
        Args:
            input_path: Input audio file
            output_path: Output audio file
            speed_factor: Speed multiplier (1.0 = normal, 1.5 = 1.5x faster)
        """
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Change speed without changing pitch
            faster_audio = audio.speedup(playback_speed=speed_factor)
            
            faster_audio.export(output_path, format="mp3")
            return True
        except Exception as e:
            print(f"Error adjusting audio speed: {e}")
            return False
    
    def _generate_cloned_speech(self, text: str, output_path: str, voice_samples_dir: str) -> bool:
        """Generate speech using cloned voice"""
        try:
            result = self.voice_cloner.clone_voice_with_text(
                voice_samples_dir=voice_samples_dir,
                text=text,
                output_path=output_path
            )
            return result.get("success", False)
        except Exception as e:
            print(f"Cloned TTS error: {e}")
            return False
    
    def extract_voice_from_video(self, video_path: str, output_path: str) -> Dict:
        """Extract voice from video file"""
        return self.voice_cloner.extract_voice_from_video(video_path, output_path)
    
    def extract_voice_from_audio(self, audio_path: str, output_path: str) -> Dict:
        """Extract and process voice from audio file"""
        return self.voice_cloner.extract_voice_from_audio(audio_path, output_path)
    
    def record_voice_from_microphone(self, duration: int, output_path: str, 
                                   gain_multiplier: float = 1.0,
                                   device_index: Optional[int] = None,
                                   progress_callback: Optional[callable] = None) -> Dict:
        """Record voice from microphone with gain control"""
        return self.voice_cloner.record_voice_from_microphone(
            duration=duration,
            output_path=output_path,
            gain_multiplier=gain_multiplier,
            device_index=device_index,
            progress_callback=progress_callback
        )
    
    def create_voice_samples(self, audio_path: str, output_dir: str) -> Dict:
        """Create voice samples for cloning"""
        return self.voice_cloner.create_voice_samples(audio_path, output_dir)
    
    def get_available_microphones(self) -> List[Dict]:
        """Get available microphones"""
        return self.voice_cloner.get_available_microphones()
    
    def test_microphone(self, device_index: Optional[int] = None) -> Dict:
        """Test microphone functionality"""
        return self.voice_cloner.test_microphone(device_index)
    
    def get_available_providers(self) -> list:
        """Get list of available TTS providers"""
        providers = []
        if self.voice_cloner_available:
            providers.append("cloned")
        if self.elevenlabs_available:
            providers.append("elevenlabs")
        if self.azure_available:
            providers.append("azure")
        providers.append("basic")  # Always available as fallback
        return providers
    
    def start_audio_monitoring(self, device_index: Optional[int] = None, 
                             gain_multiplier: float = 1.0) -> Dict:
        """Start real-time audio level monitoring"""
        return self.voice_cloner.start_audio_monitoring(
            device_index=device_index,
            gain_multiplier=gain_multiplier
        )
    
    def stop_audio_monitoring(self) -> Dict:
        """Stop audio monitoring"""
        return self.voice_cloner.stop_audio_monitoring()
    
    def get_current_audio_level(self) -> Dict:
        """Get current audio level from monitoring thread"""
        return self.voice_cloner.get_current_audio_level()
    
    def get_audio_level_preview(self, device_index: Optional[int] = None, 
                              gain_multiplier: float = 1.0, 
                              duration: float = 0.1) -> Dict:
        """Get a quick audio level preview"""
        return self.voice_cloner.get_audio_level_preview(
            device_index=device_index,
            gain_multiplier=gain_multiplier,
            duration=duration
        ) 