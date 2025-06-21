#!/usr/bin/env python3
"""
AutoAvatar Demo Script
Test the video generation functionality without the Streamlit interface
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
    img = Image.new('RGB', (800, 600), color='navy')
    
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
    text = "DEMO\nIMAGE"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (800 - text_width) // 2
    y = (600 - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font, align='center')
    
    # Save demo image
    demo_path = "demo_image.jpg"
    img.save(demo_path)
    return demo_path

def run_demo():
    """Run a complete demo of the video generation system"""
    print("🎬 AutoAvatar - Demo Mode")
    print("=" * 50)
    
    # Initialize the generator
    try:
        generator = AutoVideoGenerator()
        print("✅ Video generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False
    
    # Validate setup
    print("\n🔍 Validating system setup...")
    validation = generator.validate_setup()
    
    if not validation['valid']:
        print("⚠️ Setup issues found:")
        for issue in validation['issues']:
            print(f"  • {issue}")
        print("\n💡 To fix:")
        print("  1. Copy env_template.txt to .env")
        print("  2. Add your API keys to the .env file")
        print("  3. Install required dependencies: pip install -r requirements.txt")
        return False
    else:
        print("✅ System validation passed")
    
    # Show available voice providers
    voice_info = generator.get_available_voices()
    print(f"\n🎤 Available voice providers: {', '.join(voice_info['providers'])}")
    
    # Create demo image
    print("\n📸 Creating demo image...")
    demo_image_path = create_demo_image()
    print(f"✅ Demo image created: {demo_image_path}")
    
    # Test topics
    demo_topics = [
        "Breaking: AI revolutionizes video creation",
        "Technology breakthrough enables instant video generation",
        "New system creates professional videos from single photos"
    ]
    
    print(f"\n📝 Demo topics available:")
    for i, topic in enumerate(demo_topics, 1):
        print(f"  {i}. {topic}")
    
    # Use first topic for demo
    selected_topic = demo_topics[0]
    print(f"\n🚀 Generating video for: '{selected_topic}'")
    
    # Generate video
    result = generator.generate_video(
        image_path=demo_image_path,
        news_topic=selected_topic,
        duration=25,  # Shorter for demo
        style="modern",
        voice_provider="auto"
    )
    
    if result['success']:
        print(f"\n🎉 SUCCESS! Video generated successfully!")
        print(f"📁 Video saved to: {result['video_path']}")
        print(f"⏱️ Duration: {result['actual_duration']:.1f} seconds")
        print(f"🎨 Style: {result['style'].title()}")
        print(f"🗣️ Voice: {result['voice_provider'].title()}")
        
        # Show script
        if result.get('script'):
            print(f"\n📝 Generated script:")
            print("-" * 40)
            print(result['script'])
            print("-" * 40)
        
        # Show file info
        video_info = generator.get_video_info(result['video_path'])
        if video_info['exists']:
            print(f"\n📊 Video file info:")
            print(f"  • Size: {video_info['size_mb']} MB")
            print(f"  • Filename: {video_info['filename']}")
    
    else:
        print(f"\n❌ FAILED: {result['error']}")
        return False
    
    # Cleanup demo image
    try:
        os.remove(demo_image_path)
        print(f"\n🧹 Cleaned up demo image")
    except:
        pass
    
    print(f"\n🎬 Demo completed successfully!")
    print(f"🚀 To run the full interface: streamlit run app.py")
    
    return True

if __name__ == "__main__":
    success = run_demo()
    sys.exit(0 if success else 1) 