import os
import tempfile
import numpy as np
from typing import Optional, Dict, List, Tuple
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import split_on_silence
import whisper
import torch
import torchaudio
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    VideoFileClip = None
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not available. Video processing will be disabled.")
import pyaudio
import wave
import threading
import time
from config import Config


class VoiceCloner:
    def __init__(self):
        """Initialize voice cloning system"""
        self.sample_rate = 22050
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.whisper_model = None
        self.recording_active = False
        self.audio_buffer = []
        
        # Initialize Whisper for transcription
        try:
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper model loaded for transcription")
        except Exception as e:
            print(f"⚠️ Whisper model loading failed: {e}")
    
    def extract_voice_from_video(self, video_path: str, output_path: str) -> Dict:
        """
        Extract audio track from video file
        
        Args:
            video_path: Path to video file
            output_path: Path to save extracted audio
            
        Returns:
            Dictionary with extraction results
        """
        if not MOVIEPY_AVAILABLE:
            return {"success": False, "error": "MoviePy not available. Cannot process video files."}
        
        try:
            # Load video and extract audio
            video = VideoFileClip(video_path)
            audio = video.audio
            
            if audio is None:
                return {"success": False, "error": "Video has no audio track"}
            
            # Save audio to temporary file
            temp_audio = tempfile.mktemp(suffix='.wav')
            audio.write_audiofile(temp_audio, verbose=False, logger=None)
            
            # Process and clean audio
            processed_audio = self._process_audio_file(temp_audio)
            
            # Save final processed audio
            sf.write(output_path, processed_audio, self.sample_rate)
            
            # Get audio info
            duration = len(processed_audio) / self.sample_rate
            
            # Cleanup
            video.close()
            audio.close()
            os.remove(temp_audio)
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": duration,
                "sample_rate": self.sample_rate,
                "channels": 1 if processed_audio.ndim == 1 else processed_audio.shape[1]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_voice_from_audio(self, audio_path: str, output_path: str) -> Dict:
        """
        Process and clean audio file for voice cloning
        
        Args:
            audio_path: Path to input audio file
            output_path: Path to save processed audio
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Process audio file
            processed_audio = self._process_audio_file(audio_path)
            
            # Save processed audio
            sf.write(output_path, processed_audio, self.sample_rate)
            
            # Get audio info
            duration = len(processed_audio) / self.sample_rate
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": duration,
                "sample_rate": self.sample_rate,
                "quality_score": self._assess_audio_quality(processed_audio)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def record_voice_from_microphone(self, duration: int, output_path: str) -> Dict:
        """
        Record voice from microphone
        
        Args:
            duration: Recording duration in seconds
            output_path: Path to save recorded audio
            
        Returns:
            Dictionary with recording results
        """
        try:
            # Audio recording parameters
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open stream
            stream = p.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            print(f"🎤 Recording for {duration} seconds...")
            frames = []
            
            # Record audio
            for i in range(0, int(rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            # Stop recording
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save raw recording
            temp_wav = tempfile.mktemp(suffix='.wav')
            wf = wave.open(temp_wav, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            # Process recorded audio
            processed_audio = self._process_audio_file(temp_wav)
            sf.write(output_path, processed_audio, self.sample_rate)
            
            # Cleanup
            os.remove(temp_wav)
            
            return {
                "success": True,
                "output_path": output_path,
                "duration": duration,
                "quality_score": self._assess_audio_quality(processed_audio)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_voice_samples(self, audio_path: str, output_dir: str, 
                           min_duration: float = 3.0, max_duration: float = 10.0) -> Dict:
        """
        Create voice samples from audio for training
        
        Args:
            audio_path: Path to input audio
            output_dir: Directory to save voice samples
            min_duration: Minimum sample duration
            max_duration: Maximum sample duration
            
        Returns:
            Dictionary with sample creation results
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Convert to AudioSegment for easier manipulation
            audio_segment = AudioSegment.from_file(audio_path)
            
            # Split on silence to get speech segments
            chunks = split_on_silence(
                audio_segment,
                min_silence_len=500,  # 0.5 seconds
                silence_thresh=audio_segment.dBFS - 16,
                keep_silence=250
            )
            
            # Filter and save valid samples
            valid_samples = []
            for i, chunk in enumerate(chunks):
                duration = len(chunk) / 1000.0  # Convert to seconds
                
                if min_duration <= duration <= max_duration:
                    sample_path = os.path.join(output_dir, f"sample_{i:03d}.wav")
                    chunk.export(sample_path, format="wav")
                    valid_samples.append({
                        "path": sample_path,
                        "duration": duration,
                        "quality": self._assess_chunk_quality(chunk)
                    })
            
            # Sort by quality and keep best samples
            valid_samples.sort(key=lambda x: x['quality'], reverse=True)
            best_samples = valid_samples[:min(10, len(valid_samples))]
            
            # Generate transcriptions for samples
            transcriptions = []
            if self.whisper_model:
                for sample in best_samples:
                    try:
                        result = self.whisper_model.transcribe(sample['path'])
                        transcriptions.append({
                            "path": sample['path'],
                            "text": result['text'].strip(),
                            "confidence": result.get('confidence', 0.0)
                        })
                    except:
                        transcriptions.append({
                            "path": sample['path'],
                            "text": "",
                            "confidence": 0.0
                        })
            
            return {
                "success": True,
                "total_samples": len(valid_samples),
                "best_samples": best_samples,
                "transcriptions": transcriptions,
                "output_dir": output_dir
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clone_voice_with_text(self, voice_samples_dir: str, text: str, 
                             output_path: str) -> Dict:
        """
        Generate speech using cloned voice
        
        Args:
            voice_samples_dir: Directory containing voice samples
            text: Text to synthesize
            output_path: Output audio path
            
        Returns:
            Dictionary with synthesis results
        """
        try:
            # This is a placeholder for voice cloning
            # In a real implementation, you would use:
            # - Coqui TTS for voice cloning
            # - RVC (Retrieval-based Voice Conversion)
            # - SpeechT5 or similar models
            
            # For now, we'll create a simple voice synthesis
            # that modulates the voice based on the samples
            
            # Load reference samples
            reference_samples = []
            for filename in os.listdir(voice_samples_dir):
                if filename.endswith('.wav'):
                    sample_path = os.path.join(voice_samples_dir, filename)
                    audio, _ = librosa.load(sample_path, sr=self.sample_rate)
                    reference_samples.append(audio)
            
            if not reference_samples:
                return {"success": False, "error": "No voice samples found"}
            
            # Simple voice characteristics extraction
            voice_characteristics = self._extract_voice_characteristics(reference_samples)
            
            # Generate speech with voice characteristics
            # This is a simplified implementation
            # In production, you would use a proper voice cloning model
            
            # For demonstration, we'll create a modulated audio
            # that represents the cloned voice concept
            synthesized_audio = self._synthesize_with_characteristics(
                text, voice_characteristics
            )
            
            # Save synthesized audio
            sf.write(output_path, synthesized_audio, self.sample_rate)
            
            return {
                "success": True,
                "output_path": output_path,
                "text": text,
                "voice_similarity": voice_characteristics.get('similarity_score', 0.7)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _process_audio_file(self, audio_path: str) -> np.ndarray:
        """Process audio file for voice cloning"""
        # Load audio
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Normalize audio
        audio = librosa.util.normalize(audio)
        
        # Remove silence
        audio, _ = librosa.effects.trim(audio, top_db=20)
        
        # Apply noise reduction (simple version)
        audio = self._reduce_noise(audio)
        
        return audio
    
    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Simple noise reduction"""
        # Apply spectral subtraction for noise reduction
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise (from first 0.5 seconds)
        noise_frames = int(0.5 * self.sample_rate / 512)
        noise_magnitude = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Spectral subtraction
        alpha = 2.0  # Over-subtraction factor
        clean_magnitude = magnitude - alpha * noise_magnitude
        clean_magnitude = np.maximum(clean_magnitude, 0.1 * magnitude)
        
        # Reconstruct audio
        clean_stft = clean_magnitude * np.exp(1j * phase)
        clean_audio = librosa.istft(clean_stft)
        
        return clean_audio
    
    def _assess_audio_quality(self, audio: np.ndarray) -> float:
        """Assess audio quality for voice cloning"""
        # Calculate SNR
        signal_power = np.mean(audio ** 2)
        noise_power = np.mean((audio - np.mean(audio)) ** 2) * 0.1
        snr = 10 * np.log10(signal_power / (noise_power + 1e-10))
        
        # Calculate spectral centroid (voice clarity)
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate))
        
        # Normalize to 0-1 score
        quality_score = min(1.0, max(0.0, (snr / 30.0 + spectral_centroid / 5000.0) / 2.0))
        
        return quality_score
    
    def _assess_chunk_quality(self, chunk: AudioSegment) -> float:
        """Assess quality of audio chunk"""
        # Convert to numpy array
        samples = np.array(chunk.get_array_of_samples())
        if chunk.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        
        # Normalize
        samples = samples.astype(np.float32) / 32768.0
        
        # Calculate quality metrics
        rms = np.sqrt(np.mean(samples ** 2))
        peak = np.max(np.abs(samples))
        
        # Quality score based on dynamic range and level
        quality = min(1.0, rms * 5.0) * min(1.0, peak * 2.0)
        
        return quality
    
    def _extract_voice_characteristics(self, samples: List[np.ndarray]) -> Dict:
        """Extract voice characteristics from samples"""
        characteristics = {}
        
        # Combine all samples
        combined_audio = np.concatenate(samples)
        
        # Extract features
        characteristics['fundamental_freq'] = np.mean(
            librosa.piptrack(y=combined_audio, sr=self.sample_rate)[0]
        )
        
        characteristics['spectral_centroid'] = np.mean(
            librosa.feature.spectral_centroid(y=combined_audio, sr=self.sample_rate)
        )
        
        characteristics['mfcc'] = np.mean(
            librosa.feature.mfcc(y=combined_audio, sr=self.sample_rate, n_mfcc=13),
            axis=1
        )
        
        characteristics['similarity_score'] = 0.8  # Placeholder
        
        return characteristics
    
    def _synthesize_with_characteristics(self, text: str, characteristics: Dict) -> np.ndarray:
        """Synthesize audio with voice characteristics"""
        # This is a placeholder implementation
        # In a real system, you would use a proper voice cloning model
        
        # Generate a simple tone that represents the cloned voice
        # This is just for demonstration
        duration = max(3.0, len(text) * 0.1)  # Rough estimate
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        
        # Create a voice-like waveform using characteristics
        fundamental_freq = characteristics.get('fundamental_freq', 150)
        
        # Generate synthetic voice
        voice = np.sin(2 * np.pi * fundamental_freq * t)
        voice += 0.3 * np.sin(2 * np.pi * fundamental_freq * 2 * t)
        voice += 0.1 * np.sin(2 * np.pi * fundamental_freq * 3 * t)
        
        # Apply envelope
        envelope = np.exp(-t * 0.5)
        voice *= envelope
        
        # Add some speech-like modulation
        modulation = 1 + 0.1 * np.sin(2 * np.pi * 5 * t)  # 5Hz modulation
        voice *= modulation
        
        # Normalize
        voice = voice / np.max(np.abs(voice)) * 0.8
        
        return voice.astype(np.float32)
    
    def get_available_microphones(self) -> List[Dict]:
        """Get list of available microphones"""
        try:
            p = pyaudio.PyAudio()
            microphones = []
            
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    microphones.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
            
            p.terminate()
            return microphones
            
        except Exception as e:
            print(f"Error getting microphones: {e}")
            return []
    
    def test_microphone(self, device_index: Optional[int] = None) -> Dict:
        """Test microphone functionality"""
        try:
            p = pyaudio.PyAudio()
            
            # Test recording for 2 seconds
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            duration = 2
            
            stream = p.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk
            )
            
            frames = []
            for _ in range(0, int(rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Analyze recorded audio
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            level = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
            
            return {
                "success": True,
                "microphone_working": True,
                "audio_level": float(level),
                "quality": "Good" if level > 1000 else "Low"
            }
            
        except Exception as e:
            return {
                "success": False,
                "microphone_working": False,
                "error": str(e)
            } 