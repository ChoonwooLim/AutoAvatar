from openai import OpenAI
from typing import Optional
import re
from config import Config

class ScriptGenerator:
    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API 키가 필요합니다")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_news_script(self, topic: str, duration_seconds: int = 30, style: str = "professional") -> str:
        """
        Generate a professional news script based on the topic
        
        Args:
            topic: The news topic/headline
            duration_seconds: Target duration in seconds
            style: Script style (professional, casual, dramatic)
        
        Returns:
            Generated script text
        """
        # Calculate approximate word count (average speaking rate: 150-160 words per minute)
        target_words = int((duration_seconds * 155) / 60)
        
        style_prompts = {
            "professional": "전문적인 뉴스 앵커 스타일, 격식 있고 권위적인 톤",
            "casual": "대화적이고 매력적인 스타일, 친근한 톤",
            "dramatic": "극적이고 설득력 있는 스타일, 강조와 감정이 담긴 톤",
            "modern": "현대적이고 세련된 스타일, 젊은 세대에게 어필하는 톤",
            "classic": "클래식하고 전통적인 스타일, 신뢰감 있는 톤"
        }
        
        style_instruction = style_prompts.get(style, style_prompts["professional"])
        
        prompt = f"""
        다음 주제에 대한 {style_instruction}의 한국어 뉴스 스크립트를 작성해주세요: "{topic}"
        
        요구사항:
        - 약 {target_words}단어 분량 ({duration_seconds}초 분량의 발화)
        - 첫 문장에 흥미로운 도입부 포함
        - 전문적인 뉴스 형식
        - 핵심 사실과 배경 정보 포함
        - 강력한 결론
        - 자연스러운 발화 리듬과 적절한 휴지
        - 복잡한 전문용어 피하기
        - 한국어로 작성
        
        스크립트:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 매력적이고 정확하며 잘 구성된 한국어 뉴스 스크립트를 작성하는 전문 뉴스 작가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            script = response.choices[0].message.content.strip()
            return self._clean_script(script)
            
        except Exception as e:
            print(f"스크립트 생성 오류: {e}")
            return self._generate_fallback_script(topic, target_words)
    
    def _clean_script(self, script: str) -> str:
        """Clean and format the generated script"""
        # Remove any script formatting markers
        script = re.sub(r'^Script:\s*', '', script, flags=re.IGNORECASE)
        script = re.sub(r'\[.*?\]', '', script)  # Remove stage directions
        script = re.sub(r'\(.*?\)', '', script)  # Remove parenthetical notes
        
        # Clean up spacing
        script = re.sub(r'\s+', ' ', script)
        script = script.strip()
        
        return script
    
    def _generate_fallback_script(self, topic: str, target_words: int) -> str:
        """API 실패 시 간단한 대체 스크립트 생성"""
        return f"""
        속보입니다: {topic}. 
        이 발전하고 있는 이야기는 전 세계의 관심을 받고 있습니다. 
        저희 팀은 최신 업데이트를 추적하고 있으며, 더 자세한 내용이 확인되는 대로 전해드리겠습니다. 
        이 중요한 소식의 지속적인 보도를 위해 계속 시청해 주십시오.
        """
    
    def analyze_script_timing(self, script: str, words_per_minute: int = 155) -> dict:
        """
        Analyze script timing and provide metrics
        
        Returns:
            Dictionary with timing information
        """
        word_count = len(script.split())
        estimated_duration = (word_count / words_per_minute) * 60
        
        return {
            'word_count': word_count,
            'estimated_duration_seconds': round(estimated_duration, 1),
            'estimated_duration_minutes': round(estimated_duration / 60, 2),
            'words_per_minute': words_per_minute
        } 