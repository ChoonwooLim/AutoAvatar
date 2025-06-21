import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys - 동적으로 설정됨
    OPENAI_API_KEY = None
    ELEVENLABS_API_KEY = None
    AZURE_SPEECH_KEY = None
    AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION', 'eastus')
    
    @classmethod
    def update_from_manager(cls, config_manager):
        """ConfigManager에서 API 키 업데이트"""
        cls.OPENAI_API_KEY = config_manager.get_api_key('openai')
        cls.ELEVENLABS_API_KEY = config_manager.get_api_key('elevenlabs')
        cls.AZURE_SPEECH_KEY = config_manager.get_api_key('azure_speech')
    
    @classmethod
    def get_fallback_keys(cls):
        """환경변수에서 기본 키 가져오기"""
        return {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ELEVENLABS_API_KEY': os.getenv('ELEVENLABS_API_KEY'),
            'AZURE_SPEECH_KEY': os.getenv('AZURE_SPEECH_KEY')
        }
    
    # Video Settings
    VIDEO_WIDTH = 1920
    VIDEO_HEIGHT = 1080
    VIDEO_FPS = 30
    VIDEO_DURATION_BUFFER = 1.0  # Extra seconds for transitions
    
    # Audio Settings
    AUDIO_SAMPLE_RATE = 44100
    AUDIO_CHANNELS = 2
    
    # TTS Settings
    ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    AZURE_VOICE_NAME = "en-US-AriaNeural"
    
    # Directories
    UPLOAD_DIR = "uploads"
    OUTPUT_DIR = "outputs"
    TEMP_DIR = "temp"
    ASSETS_DIR = "assets"
    
    # File Extensions
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    OUTPUT_VIDEO_FORMAT = '.mp4'
    
    @classmethod
    def validate_keys(cls):
        """Validate that required API keys are present"""
        missing_keys = []
        
        if not cls.OPENAI_API_KEY:
            missing_keys.append('OPENAI_API_KEY')
        
        if not cls.ELEVENLABS_API_KEY and not cls.AZURE_SPEECH_KEY:
            missing_keys.append('ELEVENLABS_API_KEY or AZURE_SPEECH_KEY')
        
        return missing_keys 