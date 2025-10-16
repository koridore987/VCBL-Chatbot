// API 엔드포인트 상수
export const API_ENDPOINTS = {
    AUTH: {
        REGISTER: '/auth/register',
        LOGIN: '/auth/login',
        ME: '/auth/me',
        CHANGE_PASSWORD: '/auth/change-password',
        PASSWORD_RESET_REQUEST: '/auth/password-reset-request',
    },
    VIDEOS: {
        LIST: '/videos',
        DETAIL: (videoId) => `/videos/${videoId}`,
        EVENT: (videoId) => `/videos/${videoId}/event`,
        SCAFFOLDING_RESPOND: (videoId, scaffoldingId) =>
            `/videos/${videoId}/scaffoldings/${scaffoldingId}/respond`,
    },
    CHAT: {
        SESSIONS: '/chat/sessions',
        SESSION_DETAIL: (sessionId) => `/chat/sessions/${sessionId}`,
        MESSAGES: (sessionId) => `/chat/sessions/${sessionId}/messages`,
    },
    ADMIN: {
        USERS: '/admin/users',
        USER_ROLE: (userId) => `/admin/users/${userId}/role`,
        USER_ACTIVATE: (userId) => `/admin/users/${userId}/activate`,
        USER_RESET_PASSWORD: (userId) => `/admin/users/${userId}/reset-password`,
        VIDEOS: '/admin/videos',
        VIDEO_DETAIL: (videoId) => `/admin/videos/${videoId}`,
        SCAFFOLDINGS: (videoId) => `/admin/videos/${videoId}/scaffoldings`,
        SCAFFOLDING_DETAIL: (scaffoldingId) => `/admin/scaffoldings/${scaffoldingId}`,
        PROMPTS: '/admin/prompts',
        PROMPT_DETAIL: (promptId) => `/admin/prompts/${promptId}`,
    },
    LOGS: {
        EVENTS: '/logs/events',
        EVENTS_EXPORT: '/logs/events/export',
        CHAT_SESSIONS_EXPORT: '/logs/chat-sessions/export',
        STATS: '/logs/stats',
    },
}

// 앱 설정
export const APP_CONFIG = {
    MAX_MESSAGE_LENGTH: 2000,
    MAX_NAME_LENGTH: 100,
    MAX_STUDENT_ID_LENGTH: 50,
    MIN_PASSWORD_LENGTH: 8,
    PAGINATION_SIZE: 20,
    DEBOUNCE_DELAY: 300, // ms
}

// 사용자 역할
export const USER_ROLES = {
    USER: 'user',
    ADMIN: 'admin',
    SUPER: 'super',
}

// 이벤트 타입
export const EVENT_TYPES = {
    VIDEO_VIEW: 'video_view',
    VIDEO_PLAY: 'video_play',
    VIDEO_PAUSE: 'video_pause',
    VIDEO_COMPLETE: 'video_complete',
    SCAFFOLDING_RESPONSE: 'scaffolding_response',
}

// 에러 메시지
export const ERROR_MESSAGES = {
    NETWORK_ERROR: '네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.',
    UNAUTHORIZED: '인증이 필요합니다. 다시 로그인해주세요.',
    FORBIDDEN: '접근 권한이 없습니다.',
    NOT_FOUND: '요청한 리소스를 찾을 수 없습니다.',
    SERVER_ERROR: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
    VALIDATION_ERROR: '입력 값이 올바르지 않습니다.',
    RATE_LIMIT: '요청 횟수 제한을 초과했습니다. 잠시 후 다시 시도해주세요.',
}