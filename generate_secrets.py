#!/usr/bin/env python3
"""
Flask Secret Key와 JWT Secret Key 생성 및 해시 도구
"""

import secrets
import hashlib
import base64
import os
from datetime import datetime

def generate_flask_secret_key():
    """Flask Secret Key 생성 (32바이트 랜덤)"""
    return secrets.token_urlsafe(32)

def generate_jwt_secret_key():
    """JWT Secret Key 생성 (64바이트 랜덤)"""
    return secrets.token_urlsafe(64)

def generate_strong_secret_key(length=32):
    """강력한 시크릿키 생성"""
    return secrets.token_urlsafe(length)

def hash_secret(secret_key, algorithm='sha256'):
    """시크릿키를 해시화"""
    if algorithm == 'sha256':
        return hashlib.sha256(secret_key.encode()).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(secret_key.encode()).hexdigest()
    elif algorithm == 'blake2b':
        return hashlib.blake2b(secret_key.encode()).hexdigest()
    else:
        raise ValueError("지원하지 않는 해시 알고리즘입니다.")

def generate_base64_secret(length=32):
    """Base64 인코딩된 시크릿키 생성"""
    return base64.b64encode(secrets.token_bytes(length)).decode()

def main():
    print("=" * 60)
    print("🔐 Flask & JWT Secret Key Generator")
    print("=" * 60)
    print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Flask Secret Key 생성
    flask_secret = generate_flask_secret_key()
    print("📝 Flask Secret Key:")
    print(f"   {flask_secret}")
    print()
    
    # JWT Secret Key 생성
    jwt_secret = generate_jwt_secret_key()
    print("🔑 JWT Secret Key:")
    print(f"   {jwt_secret}")
    print()
    
    # 추가 강력한 시크릿키들
    strong_secret_32 = generate_strong_secret_key(32)
    strong_secret_64 = generate_strong_secret_key(64)
    
    print("💪 강력한 시크릿키 (32바이트):")
    print(f"   {strong_secret_32}")
    print()
    
    print("💪 강력한 시크릿키 (64바이트):")
    print(f"   {strong_secret_64}")
    print()
    
    # Base64 인코딩된 시크릿키
    base64_secret = generate_base64_secret(32)
    print("🔒 Base64 인코딩된 시크릿키:")
    print(f"   {base64_secret}")
    print()
    
    # 해시화된 시크릿키들
    print("🔐 해시화된 시크릿키들:")
    print(f"   SHA256: {hash_secret(flask_secret, 'sha256')}")
    print(f"   SHA512: {hash_secret(flask_secret, 'sha512')}")
    print(f"   BLAKE2B: {hash_secret(flask_secret, 'blake2b')}")
    print()
    
    # 환경변수 설정 예시
    print("🌍 환경변수 설정 예시:")
    print(f"   export FLASK_SECRET_KEY='{flask_secret}'")
    print(f"   export JWT_SECRET_KEY='{jwt_secret}'")
    print()
    
    # .env 파일 생성 예시
    print("📄 .env 파일 예시:")
    print("   FLASK_SECRET_KEY=" + flask_secret)
    print("   JWT_SECRET_KEY=" + jwt_secret)
    print("   DATABASE_URL=sqlite:///instance/vcbl_chatbot.db")
    print()
    
    print("=" * 60)
    print("⚠️  보안 주의사항:")
    print("   - 이 키들을 안전한 곳에 보관하세요")
    print("   - 프로덕션에서는 환경변수로 관리하세요")
    print("   - Git에 커밋하지 마세요")
    print("   - 정기적으로 키를 교체하세요")
    print("=" * 60)

if __name__ == "__main__":
    main()
