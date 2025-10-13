"""
애플리케이션 상수
"""

# API 엔드포인트
API_ENDPOINTS = {
    'AUTH': {
        'REGISTER': '/auth/register',
        'LOGIN': '/auth/login',
        'ME': '/auth/me',
        'CHANGE_PASSWORD': '/auth/change-password',
        'PASSWORD_RESET_REQUEST': '/auth/password-reset-request',
    },
    'VIDEOS': {
        'LIST': '/videos',
        'DETAIL': '/videos/{video_id}',
        'EVENT': '/videos/{video_id}/event',
        'SCAFFOLDING_RESPOND': '/videos/{video_id}/scaffoldings/{scaffolding_id}/respond',
    },
    'CHAT': {
        'SESSIONS': '/chat/sessions',
        'SESSION_DETAIL': '/chat/sessions/{session_id}',
        'MESSAGES': '/chat/sessions/{session_id}/messages',
    },
    'ADMIN': {
        'USERS': '/admin/users',
        'USER_ROLE': '/admin/users/{user_id}/role',
        'USER_ACTIVATE': '/admin/users/{user_id}/activate',
        'USER_RESET_PASSWORD': '/admin/users/{user_id}/reset-password',
        'VIDEOS': '/admin/videos',
        'VIDEO_DETAIL': '/admin/videos/{video_id}',
        'SCAFFOLDINGS': '/admin/videos/{video_id}/scaffoldings',
        'SCAFFOLDING_DETAIL': '/admin/scaffoldings/{scaffolding_id}',
        'PROMPTS': '/admin/prompts',
        'PROMPT_DETAIL': '/admin/prompts/{prompt_id}',
    },
    'LOGS': {
        'EVENTS': '/logs/events',
        'EVENTS_EXPORT': '/logs/events/export',
        'CHAT_SESSIONS_EXPORT': '/logs/chat-sessions/export',
        'STATS': '/logs/stats',
    }
}

# 앱 설정
APP_CONFIG = {
    'MAX_MESSAGE_LENGTH': 2000,
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'PAGINATION_SIZE': 20,
    'DEBOUNCE_DELAY': 300,  # ms
}

# 사용자 역할
USER_ROLES = {
    'USER': 'user',
    'ADMIN': 'admin',
    'SUPER': 'super',
}

# Super 관리자 설정
SUPER_ADMIN_CREDENTIALS = {
    'STUDENT_ID': 'super',
    'PASSWORD': 'super1234',
    'NAME': 'Super Administrator'
}

# 이벤트 타입
EVENT_TYPES = {
    'VIDEO_VIEW': 'video_view',
    'VIDEO_PLAY': 'video_play',
    'VIDEO_PAUSE': 'video_pause',
    'VIDEO_COMPLETE': 'video_complete',
    'SCAFFOLDING_RESPONSE': 'scaffolding_response',
}

