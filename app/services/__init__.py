"""
비즈니스 로직 서비스
"""
import openai
from app import config
from app.models import DatabaseManager
from app.models.chatbot import ChatbotTypeManager

class ChatService:
    """채팅 서비스 클래스"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.chatbot_manager = ChatbotTypeManager()
        openai.api_key = config.OPENAI_API_KEY
    
    def generate_response(self, user_id: int, user_message: str) -> str:
        """사용자 메시지에 대한 봇 응답 생성"""
        try:
            # 사용자의 챗봇 타입 ID 조회
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT chatbot_type_id FROM user WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            chatbot_type_id = result[0] if result else 1
            
            # 챗봇 타입의 시스템 프롬프트 가져오기
            chatbot_type = self.chatbot_manager.get_chatbot_type(chatbot_type_id)
            system_prompt = chatbot_type[3] if chatbot_type else "You are a helpful AI assistant."
            
            # 최근 대화 기록 가져오기
            recent_messages = self.db_manager.get_recent_messages(user_id, limit=10)
            
            # OpenAI 포맷으로 변환 (시스템 프롬프트 포함)
            messages_for_openai = [{'role': 'system', 'content': system_prompt}]
            
            for sender, content in recent_messages:
                if sender == 'user':
                    messages_for_openai.append({'role': 'user', 'content': content})
                else:
                    messages_for_openai.append({'role': 'assistant', 'content': content})
            
            # 현재 사용자 메시지 추가
            messages_for_openai.append({'role': 'user', 'content': user_message})
            
            # OpenAI API 호출
            response = openai.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages_for_openai
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # OpenAI API 오류 시 기본 응답
            return f"죄송합니다. 일시적인 오류가 발생했습니다: {str(e)}"
