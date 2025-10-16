from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from app.models.chat_message import ChatMessage
import tiktoken
import logging
import time

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self, config):
        """
        OpenAI 서비스 초기화
        
        Args:
            config: Flask 설정 객체
        """
        self.client = OpenAI(
            api_key=config['OPENAI_API_KEY'],
            timeout=config.get('OPENAI_TIMEOUT', 30),
            max_retries=config.get('OPENAI_MAX_RETRIES', 3)
        )
        self.model_name = config['MODEL_NAME']
        self.summary_trigger_tokens = config['SUMMARY_TRIGGER_TOKENS']
        self.max_tokens_per_request = config['MAX_TOKENS_PER_REQUEST']
        self.max_tokens_output = config['MAX_TOKENS_OUTPUT']
        
        # Token encoding
        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
        except Exception as e:
            logger.warning(f"Failed to get encoding for model {self.model_name}, using default: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text):
        """Count tokens in a text string"""
        return len(self.encoding.encode(text))
    
    def chat_completion(self, session, user_message, system_prompt, constraints=None):
        """
        채팅 완성 처리 (요약 전달 전략 포함)
        
        Args:
            session: 채팅 세션
            user_message: 사용자 메시지
            system_prompt: 시스템 프롬프트
            constraints: OpenAI API 파라미터 (dict)
            
        Returns:
            dict: 응답 데이터 (content, tokens, cost, new_summary)
            
        Raises:
            Exception: API 호출 실패 시
        """
        if constraints is None:
            constraints = {}
        try:
            # Get recent messages
            recent_messages = session.messages[-8:] if len(session.messages) > 8 else session.messages
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            recent_messages = []
        
        # Count tokens in recent messages
        recent_tokens = sum([self.count_tokens(msg.content) for msg in recent_messages])
        summary_tokens = self.count_tokens(session.summary) if session.summary else 0
        system_tokens = self.count_tokens(system_prompt)
        user_tokens = self.count_tokens(user_message)
        
        total_context_tokens = system_tokens + summary_tokens + recent_tokens + user_tokens
        
        # Check if we need to create a summary
        new_summary = None
        if session.total_tokens + total_context_tokens > self.summary_trigger_tokens:
            # Generate summary of all messages except the most recent ones
            messages_to_summarize = session.messages[:-5] if len(session.messages) > 5 else []
            
            if messages_to_summarize:
                new_summary = self._generate_summary(messages_to_summarize, session.summary)
                summary_tokens = self.count_tokens(new_summary)
                
                # Update recent messages to only include last 5 turns
                recent_messages = session.messages[-5:]
        
        # Build messages for API
        messages = []
        
        # System prompt
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Add summary if exists
        if new_summary:
            messages.append({
                "role": "system",
                "content": f"이전 대화 요약:\n{new_summary}"
            })
        elif session.summary:
            messages.append({
                "role": "system",
                "content": f"이전 대화 요약:\n{session.summary}"
            })
        
        # Add recent messages
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call OpenAI API with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"OpenAI API call attempt {attempt + 1}/{max_retries}")
                
                # API 파라미터 구성
                api_params = {
                    'model': self.model_name,
                    'messages': messages,
                    'max_tokens': constraints.get('max_tokens', self.max_tokens_output),
                    'temperature': constraints.get('temperature', 0.7)
                }
                
                # 추가 constraints 적용
                if 'top_p' in constraints:
                    api_params['top_p'] = constraints['top_p']
                if 'frequency_penalty' in constraints:
                    api_params['frequency_penalty'] = constraints['frequency_penalty']
                if 'presence_penalty' in constraints:
                    api_params['presence_penalty'] = constraints['presence_penalty']
                if 'stop' in constraints:
                    api_params['stop'] = constraints['stop']
                if 'response_format' in constraints:
                    api_params['response_format'] = constraints['response_format']
                
                response = self.client.chat.completions.create(**api_params)
                break
                
            except RateLimitError as e:
                logger.warning(f"Rate limit error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before retry")
                    time.sleep(wait_time)
                else:
                    raise Exception('OpenAI API 속도 제한을 초과했습니다. 잠시 후 다시 시도해주세요.')
            
            except APITimeoutError as e:
                logger.error(f"Timeout error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise Exception('OpenAI API 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.')
            
            except APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise Exception('OpenAI API 호출 중 오류가 발생했습니다.')
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                raise Exception(f'예상치 못한 오류가 발생했습니다: {str(e)}')
        
        # Extract response
        assistant_message = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # Calculate cost (gpt-4o-mini pricing: $0.15/$0.60 per 1M tokens)
        cost = (prompt_tokens / 1_000_000 * 0.15) + (completion_tokens / 1_000_000 * 0.60)
        
        return {
            'content': assistant_message,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'cost': cost,
            'new_summary': new_summary
        }
    
    def _generate_summary(self, messages, previous_summary=None):
        """
        대화 메시지 요약 생성
        
        Args:
            messages: 요약할 메시지 목록
            previous_summary: 이전 요약 (있는 경우)
            
        Returns:
            str: 생성된 요약
        """
        try:
            conversation_text = ""
        except Exception as e:
            logger.error(f"Error in generate_summary: {e}")
            return ""
        
        if previous_summary:
            conversation_text += f"이전 요약:\n{previous_summary}\n\n"
        
        conversation_text += "대화 내용:\n"
        for msg in messages:
            role_ko = "사용자" if msg.role == "user" else "AI"
            conversation_text += f"{role_ko}: {msg.content}\n"
        
        summary_messages = [
            {
                "role": "system",
                "content": "다음 대화 내용을 간결하게 요약해주세요. 중요한 질문, 답변, 개념을 중심으로 요약하되 300토큰 이내로 작성해주세요."
            },
            {
                "role": "user",
                "content": conversation_text
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=summary_messages,
                max_tokens=300,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content
            logger.info("Summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # 요약 생성 실패 시 fallback
            return "이전 대화 내용이 요약되었습니다."

