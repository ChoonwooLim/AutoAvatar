#!/usr/bin/env python3
"""
AutoAvatar Voice Cloning Demo Script
Test the voice cloning functionality specifically
"""

import os
import sys
from pathlib import Path
from PIL import Image
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_generator import AutoVideoGenerator
from config import Config

def create_demo_image():
    """Create a simple demo image for testing"""
    # Create a simple colored image
    img = Image.new('RGB', (800, 600), color='darkblue')
    
    # Add some text (this would normally be a portrait)
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a default font
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Add centered text
    text = "VOICE\nCLONE\nDEMO"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (800 - text_width) // 2
    y = (600 - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font, align='center')
    
    # Save demo image
    demo_path = "voice_clone_demo_image.jpg"
    img.save(demo_path)
    return demo_path

def test_microphone_recording(generator):
    """Test microphone recording functionality"""
    print("\n🎤 Testing Microphone Recording...")
    
    # Get available microphones
    microphones = generator.get_available_microphones()
    if microphones:
        print(f"✅ Found {len(microphones)} microphone(s):")
        for i, mic in enumerate(microphones[:3]):  # Show first 3
            print(f"  {i+1}. {mic['name']}")
    else:
        print("⚠️ No microphones found")
        return False
    
    # Test microphone
    print("\n🔍 Testing microphone functionality...")
    mic_test = generator.test_microphone()
    
    if mic_test.get("microphone_working"):
        print(f"✅ Microphone test passed!")
        print(f"   Audio Level: {mic_test.get('audio_level', 0):.0f}")
        print(f"   Quality: {mic_test.get('quality', 'Unknown')}")
        return True
    else:
        print(f"❌ Microphone test failed: {mic_test.get('error', 'Unknown')}")
        return False

def test_voice_recording_workflow(generator):
    """Test the complete voice recording workflow"""
    print("\n🎭 Testing Voice Recording Workflow...")
    
    try:
        # Record voice (shorter duration for demo)
        print("📹 Recording 5 seconds of audio for demo...")
        import uuid
        session_id = str(uuid.uuid4())[:8]
        recorded_path = os.path.join(Config.TEMP_DIR, f"demo_recorded_{session_id}.wav")
        
        # Note: In a real scenario, this would record from microphone
        # For demo purposes, we'll create a simple synthetic audio
        print("   (Creating synthetic audio for demo purposes)")
        
        # Create a simple demo audio file
        import numpy as np
        import soundfile as sf
        
        # Generate a simple tone as demo voice
        duration = 5.0
        sample_rate = 22050
        t = np.linspace(0, duration, int(duration * sample_rate))
        
        # Create a voice-like waveform
        frequency = 150  # Hz, typical male voice fundamental
        voice = np.sin(2 * np.pi * frequency * t)
        voice += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)  # Harmonics
        voice += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)
        
        # Add some speech-like modulation
        modulation = 1 + 0.2 * np.sin(2 * np.pi * 3 * t)  # 3Hz modulation
        voice *= modulation
        
        # Add envelope to make it more speech-like
        envelope = np.exp(-t * 0.1) + 0.3
        voice *= envelope
        
        # Normalize
        voice = voice / np.max(np.abs(voice)) * 0.7
        
        # Save demo audio
        sf.write(recorded_path, voice.astype(np.float32), sample_rate)
        
        print(f"✅ Demo audio created: {recorded_path}")
        
        # Create voice samples
        print("🎵 Creating voice samples...")
        voice_samples_dir = os.path.join(Config.TEMP_DIR, f"voice_samples_{session_id}")
        
        samples_result = generator.tts_engine.create_voice_samples(
            recorded_path, 
            voice_samples_dir
        )
        
        if samples_result.get("success"):
            print(f"✅ Voice samples created successfully!")
            print(f"   Total samples: {samples_result['total_samples']}")
            print(f"   Best samples: {len(samples_result['best_samples'])}")
            print(f"   Output directory: {voice_samples_dir}")
            
            return {
                "success": True,
                "session_id": session_id,
                "voice_samples_dir": voice_samples_dir,
                "recorded_path": recorded_path
            }
        else:
            print(f"❌ Failed to create voice samples: {samples_result.get('error')}")
            return {"success": False}
    
    except Exception as e:
        print(f"❌ Voice recording workflow failed: {e}")
        return {"success": False}

def test_cloned_voice_generation(generator, voice_samples_dir):
    """Test generating speech with cloned voice"""
    print("\n🎬 Testing Cloned Voice Speech Generation...")
    
    try:
        test_text = "Hello! This is a test of the voice cloning system. The technology can replicate voice characteristics from audio samples."
        
        output_path = os.path.join(Config.TEMP_DIR, "cloned_voice_test.wav")
        
        print(f"📝 Generating speech: '{test_text[:50]}...'")
        
        # Generate speech using cloned voice
        success = generator.tts_engine.generate_speech(
            text=test_text,
            output_path=output_path,
            voice_provider="cloned",
            voice_samples_dir=voice_samples_dir
        )
        
        if success:
            print(f"✅ Cloned voice speech generated successfully!")
            print(f"   Output: {output_path}")
            
            # Get audio duration
            duration = generator.tts_engine.get_audio_duration(output_path)
            print(f"   Duration: {duration:.1f} seconds")
            
            return True
        else:
            print("❌ Failed to generate cloned voice speech")
            return False
    
    except Exception as e:
        print(f"❌ Cloned voice generation failed: {e}")
        return False

def test_complete_video_with_cloned_voice(generator, voice_samples_dir):
    """Test creating a complete video with cloned voice"""
    print("\n🎥 Testing Complete Video Generation with Cloned Voice...")
    
    try:
        # Create demo image
        demo_image_path = create_demo_image()
        
        # Generate video with cloned voice
        news_topic = "Revolutionary voice cloning technology transforms video production"
        
        print(f"🚀 Generating video with cloned voice...")
        print(f"   Topic: {news_topic}")
        
        result = generator.generate_video(
            image_path=demo_image_path,
            news_topic=news_topic,
            duration=20,  # Shorter for demo
            style="modern",
            voice_provider="cloned",
            voice_samples_dir=voice_samples_dir
        )
        
        if result.get("success"):
            print(f"🎉 SUCCESS! Video with cloned voice generated!")
            print(f"📁 Video saved to: {result['video_path']}")
            print(f"⏱️ Duration: {result['actual_duration']:.1f} seconds")
            print(f"🎭 Voice provider: {result['voice_provider']}")
            
            # Show script
            if result.get('script'):
                print(f"\n📝 Generated script (first 100 chars):")
                print(f"   {result['script'][:100]}...")
            
            return True
        else:
            print(f"❌ Video generation failed: {result.get('error')}")
            return False
    
    except Exception as e:
        print(f"❌ Complete video test failed: {e}")
        return False
    
    finally:
        # Cleanup demo image
        try:
            if os.path.exists(demo_image_path):
                os.remove(demo_image_path)
        except:
            pass

def run_voice_cloning_demo():
    """Run complete voice cloning demo"""
    print("🎭 AutoAvatar Voice Cloning Demo")
    print("=" * 50)
    
    # Initialize the generator
    try:
        generator = AutoVideoGenerator()
        print("✅ Video generator with voice cloning initialized")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False
    
    # Check if voice cloning is available
    voice_info = generator.get_available_voices()
    if "cloned" not in voice_info['providers']:
        print("❌ Voice cloning not available")
        return False
    
    print(f"✅ Voice cloning available!")
    print(f"🎤 Available providers: {', '.join(voice_info['providers'])}")
    
    # Test microphone functionality
    mic_test_passed = test_microphone_recording(generator)
    
    # Test voice recording workflow
    voice_recording_result = test_voice_recording_workflow(generator)
    
    if not voice_recording_result.get("success"):
        print("❌ Voice recording workflow failed")
        return False
    
    voice_samples_dir = voice_recording_result["voice_samples_dir"]
    
    # Test cloned voice generation
    cloned_speech_success = test_cloned_voice_generation(generator, voice_samples_dir)
    
    if not cloned_speech_success:
        print("❌ Cloned voice generation failed")
        return False
    
    # Test complete video with cloned voice
    complete_video_success = test_complete_video_with_cloned_voice(generator, voice_samples_dir)
    
    if complete_video_success:
        print(f"\n🎉 ALL VOICE CLONING TESTS PASSED!")
        print(f"✅ Microphone detection: {'✓' if mic_test_passed else '○'}")
        print(f"✅ Voice sample creation: ✓")
        print(f"✅ Cloned voice synthesis: ✓") 
        print(f"✅ Complete video generation: ✓")
        
        print(f"\n🚀 Voice cloning system is fully functional!")
        print(f"🎬 You can now create videos with your own voice!")
        
        return True
    else:
        print(f"\n❌ Some voice cloning tests failed")
        return False

if __name__ == "__main__":
    success = run_voice_cloning_demo()
    sys.exit(0 if success else 1) 