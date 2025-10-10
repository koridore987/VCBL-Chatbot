"""
보안 미들웨어
"""
from flask import request, redirect, url_for, session, g
import time
from functools import wraps

def rate_limit(max_requests=100, window=3600):
    """API 호출 제한 미들웨어"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 실제 환경에서는 Redis 등 사용
            client_ip = request.remote_addr
            current_time = time.time()
            
            # 여기서는 간단한 메모리 기반 구현
            if not hasattr(g, 'rate_limit_data'):
                g.rate_limit_data = {}
            
            if client_ip not in g.rate_limit_data:
                g.rate_limit_data[client_ip] = []
            
            # 오래된 요청 제거
            g.rate_limit_data[client_ip] = [
                req_time for req_time in g.rate_limit_data[client_ip]
                if current_time - req_time < window
            ]
            
            # 요청 수 확인
            if len(g.rate_limit_data[client_ip]) >= max_requests:
                return redirect(url_for('auth.login_page', error='요청이 너무 많습니다. 잠시 후 다시 시도해주세요.'))
            
            # 현재 요청 기록
            g.rate_limit_data[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def security_headers():
    """보안 헤더 추가"""
    from flask import make_response
    
    @wraps(security_headers)
    def after_request(response):
        # XSS 방지
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS (HTTPS 환경에서만)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP (Content Security Policy)
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:;"
        
        return response
    
    return after_request

def validate_session():
    """세션 유효성 검증"""
    if 'user_id' in session:
        # 세션 타임아웃 확인
        if 'last_activity' in session:
            last_activity = session['last_activity']
            if time.time() - last_activity > 3600:  # 1시간
                session.clear()
                return False
        
        # 활동 시간 업데이트
        session['last_activity'] = time.time()
        return True
    
    return False

def require_authentication(f):
    """인증 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_session():
            return redirect(url_for('auth.login_page', error='로그인이 필요합니다.'))
        return f(*args, **kwargs)
    return decorated_function
