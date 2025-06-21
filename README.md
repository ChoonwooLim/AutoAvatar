# 🎬 AutoAvatar - AI News Video Generator

An intelligent, automated program that transforms a single photo and news topic into a polished video with professional voiceover, dynamic subtitles, background music, and studio-quality visual design.

## ✨ Features

### 🧠 Core AI Components
- **Smart Script Generation**: Uses GPT-4 to write professional news scripts
- **Premium Voice Synthesis**: ElevenLabs & Azure TTS for realistic voiceovers
- **Dynamic Subtitle Generation**: Auto-synced subtitles with visual styling
- **Intelligent Video Composition**: Automated scene creation with effects

### 🎨 Visual Styles
- **Modern**: Clean gradients with subtle animations
- **Classic**: Professional news broadcast appearance
- **Dramatic**: Bold colors with cinematic effects

### 🎵 Audio Features
- High-quality text-to-speech generation
- Background music integration
- Professional audio mixing
- Multiple voice provider support

### 📤 Export Options
- HD 1080p video output
- MP4 format for universal compatibility
- Optimized file sizes
- Built-in video player and download

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AutoAvatar.git
cd AutoAvatar

# Install dependencies
pip install -r requirements.txt
```

### 2. API Configuration

Copy the environment template and add your API keys:

```bash
# Copy template
cp env_template.txt .env

# Edit .env file with your API keys
```

**Required API Keys:**
- **OpenAI API**: For script generation ([Get here](https://platform.openai.com/api-keys))
- **ElevenLabs** OR **Azure Speech**: For voice generation
  - ElevenLabs: [Get here](https://elevenlabs.io/)
  - Azure: [Get here](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/)

### 3. Run the Application

```bash
# Start the Streamlit web interface
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📱 How to Use

### Step 1: Upload Your Image
- Click "Choose an image file" 
- Upload a portrait or any image (JPG, PNG, etc.)
- Preview appears instantly

### Step 2: Enter News Topic
- Type your news headline or topic
- Use example topics for inspiration
- Examples: "Son Heung-min transfer to Real Madrid", "AI breakthrough in medicine"

### Step 3: Configure Settings
- **Duration**: 15-120 seconds
- **Style**: Modern, Classic, or Dramatic
- **Voice Provider**: Auto-select or choose specific provider
- **Background Music**: Optional audio file upload

### Step 4: Generate Video
- Click "🚀 Generate Video"
- Watch real-time progress
- Preview generated video
- Download your creation

## 🛠️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Image Input   │    │   News Topic     │    │  Configuration  │
│                 │    │                  │    │                 │
│ • Portrait      │    │ • Headline       │    │ • Duration      │
│ • Any image     │    │ • Description    │    │ • Style         │
│ • Auto-resize   │    │ • Keywords       │    │ • Voice         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │     Script Generator    │
                    │                         │
                    │ • GPT-4 Integration     │
                    │ • Professional Writing │
                    │ • Timing Analysis       │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      TTS Engine         │
                    │                         │
                    │ • ElevenLabs API        │
                    │ • Azure Speech          │
                    │ • Fallback Options      │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Video Composer       │
                    │                         │
                    │ • MoviePy Integration   │
                    │ • Dynamic Subtitles     │
                    │ • Visual Effects        │
                    │ • Background Music      │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Final Video         │
                    │                         │
                    │ • HD Quality (1080p)    │
                    │ • Professional Look     │
                    │ • Ready for Sharing     │
                    └─────────────────────────┘
```

## 📁 Project Structure

```
AutoAvatar/
├── app.py                 # Streamlit web interface
├── video_generator.py     # Main video generation orchestrator
├── config.py             # Configuration and settings
├── requirements.txt      # Python dependencies
├── env_template.txt     # Environment variables template
├── README.md            # This file
│
├── utils/               # Core modules
│   ├── script_generator.py    # AI script generation
│   ├── tts_engine.py         # Text-to-speech handling
│   └── video_composer.py     # Video creation and effects
│
├── uploads/             # Temporary uploaded files
├── outputs/             # Generated videos
├── temp/               # Temporary processing files
└── assets/             # Static assets (backgrounds, music)
```

## 🔧 Advanced Configuration

### Video Settings
```python
# In config.py
VIDEO_WIDTH = 1920          # Full HD width
VIDEO_HEIGHT = 1080         # Full HD height  
VIDEO_FPS = 30             # 30 frames per second
```

### Voice Customization
```bash
# In .env file
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Voice selection
AZURE_VOICE_NAME=en-US-AriaNeural         # Azure voice
```

### Style Customization
- Modify `video_composer.py` for visual styles
- Add custom fonts in subtitle generation
- Adjust timing and animation parameters

## 🎯 Use Cases

### 📺 Content Creation
- **YouTube Shorts**: Vertical format support
- **Social Media**: Quick news updates  
- **Personal Branding**: Professional video presence
- **News Reporting**: Rapid story visualization

### 🏢 Business Applications
- **Corporate Updates**: Internal communications
- **Product Announcements**: Marketing videos
- **Training Materials**: Educational content
- **Social Media Marketing**: Engaging posts

### 🎓 Educational Projects
- **News Reporting**: Journalism students
- **Presentation Tools**: Academic projects
- **Language Learning**: Script practice
- **Media Studies**: Video production learning

## 🚨 Troubleshooting

### Common Issues

**1. API Key Errors**
```
Error: OpenAI API key is required
```
- Ensure `.env` file exists with valid `OPENAI_API_KEY`
- Check API key format and permissions

**2. Video Generation Fails**
```
Error: Failed to create video
```
- Verify image file format (JPG, PNG supported)
- Check available disk space
- Ensure FFmpeg is installed

**3. Voice Generation Issues**
```
Warning: Using fallback TTS
```
- Add ElevenLabs or Azure API keys
- Check API quota/billing status
- Verify internet connection

### Performance Tips

1. **Image Optimization**: Use smaller images (< 5MB) for faster processing
2. **Script Length**: Keep scripts under 200 words for optimal timing
3. **Background Music**: Use MP3 files under 10MB
4. **Cleanup**: Regularly clean old files to free disk space

## 🔮 Future Enhancements

### 🎬 Advanced Video Features
- [ ] Face animation (D-ID/SadTalker integration)
- [ ] Multiple image transitions
- [ ] Advanced motion graphics
- [ ] Custom logo/watermark support

### 🎨 Visual Improvements
- [ ] More style templates
- [ ] Custom color schemes
- [ ] Advanced typography options
- [ ] Particle effects and animations

### 🗣️ Audio Enhancements
- [ ] Voice cloning capabilities
- [ ] Multiple speaker support
- [ ] Advanced audio effects
- [ ] Music auto-generation

### 📱 Platform Features
- [ ] Batch video generation
- [ ] Cloud storage integration
- [ ] Social media auto-posting
- [ ] Template marketplace

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI**: GPT-4 for intelligent script generation
- **ElevenLabs**: Premium voice synthesis
- **Microsoft Azure**: Speech services
- **MoviePy**: Video processing library
- **Streamlit**: Beautiful web interface framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/AutoAvatar/issues)
- **Documentation**: [Project Wiki](https://github.com/yourusername/AutoAvatar/wiki)
- **Community**: [Discussions](https://github.com/yourusername/AutoAvatar/discussions)

---

<div align="center">

**🎬 AutoAvatar - Where AI Meets Creativity**

*Transform your ideas into professional videos with the power of artificial intelligence*

[⭐ Star this project](https://github.com/yourusername/AutoAvatar) | [🐛 Report Bug](https://github.com/yourusername/AutoAvatar/issues) | [💡 Request Feature](https://github.com/yourusername/AutoAvatar/issues)

</div> 