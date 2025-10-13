#!/bin/bash

echo "Creating default prompt template..."

cd backend

python << END
from app import create_app, db
from app.models.chat_prompt_template import ChatPromptTemplate

app = create_app()

with app.app_context():
    # Check if default prompt exists
    existing = ChatPromptTemplate.query.filter_by(is_default=True).first()
    
    if existing:
        print("Default prompt already exists")
        exit(0)
    
    # Create default prompt
    default_prompt = ChatPromptTemplate(
        name="기본 학습 AI 조교",
        description="학습을 돕는 기본 AI 조교 프롬프트",
        system_prompt="""당신은 학습을 돕는 AI 조교입니다.

역할:
- 학생들의 질문에 친절하고 명확하게 답변합니다
- 직접적인 답을 주기보다는 스스로 생각할 수 있도록 유도합니다
- 학습 내용과 관련된 추가 정보와 예시를 제공합니다
- 학생의 이해도를 확인하며 대화를 진행합니다

제약사항:
- 과제나 시험 문제의 직접적인 답은 제공하지 않습니다
- 학습 주제와 무관한 대화는 정중히 거절합니다
- 항상 존댓말을 사용합니다""",
        constraints='{"max_response_length": 1000, "forbidden_topics": ["정치", "종교", "성인 콘텐츠"]}',
        is_default=True,
        is_active=True
    )
    
    db.session.add(default_prompt)
    db.session.commit()
    
    print(f"Default prompt created: {default_prompt.name}")
END

