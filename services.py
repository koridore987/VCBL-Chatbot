"""
비즈니스 로직 서비스
"""
import openai
from config import OPENAI_API_KEY
from models import DatabaseManager

class ChatService:
    """채팅 서비스 클래스"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        openai.api_key = OPENAI_API_KEY
    
    def generate_response(self, user_id: int, user_message: str) -> str:
        """사용자 메시지에 대한 봇 응답 생성"""
        try:
            # 최근 대화 기록 가져오기
            recent_messages = self.db_manager.get_recent_messages(user_id, limit=10)
            
            # OpenAI 포맷으로 변환
            messages_for_openai = []
            for sender, content in recent_messages:
                if sender == 'user':
                    messages_for_openai.append({'role': 'user', 'content': content})
                else:
                    messages_for_openai.append({'role': 'assistant', 'content': content})
            
            # 현재 사용자 메시지 추가
            messages_for_openai.append({'role': 'user', 'content': user_message})
            
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_openai
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # OpenAI API 오류 시 기본 응답
            return f"죄송합니다. 일시적인 오류가 발생했습니다: {str(e)}"
