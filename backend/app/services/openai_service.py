from openai import OpenAI
from app.models.chat_message import ChatMessage
import tiktoken

class OpenAIService:
    def __init__(self, config):
        self.client = OpenAI(api_key=config['OPENAI_API_KEY'])
        self.model_name = config['MODEL_NAME']
        self.summary_trigger_tokens = config['SUMMARY_TRIGGER_TOKENS']
        self.max_tokens_per_request = config['MAX_TOKENS_PER_REQUEST']
        self.max_tokens_output = config['MAX_TOKENS_OUTPUT']
        
        # Token encoding
        try:
            self.encoding = tiktoken.encoding_for_model(self.model_name)
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text):
        """Count tokens in a text string"""
        return len(self.encoding.encode(text))
    
    def chat_completion(self, session, user_message, system_prompt):
        """
        Process chat completion with summary carry-over strategy
        """
        # Get recent messages
        recent_messages = session.messages[-8:] if len(session.messages) > 8 else session.messages
        
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
        
        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=self.max_tokens_output,
            temperature=0.7
        )
        
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
        """Generate a summary of conversation messages"""
        conversation_text = ""
        
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
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=summary_messages,
            max_tokens=300,
            temperature=0.5
        )
        
        return response.choices[0].message.content

