import axios from 'axios'
import {
    ERROR_MESSAGES
} from '../constants'
import {
    errorHandler,
    storage
} from '../utils'

const resolveBaseURL = () => {
    try {
        const origin = window?.location?.origin || ''
        // 개발 서버(3000)에서는 Vite 프록시를 사용해 동일 출처 요청으로 처리
        if (origin.includes('localhost:3000')) {
            return '/api'
        }
    } catch (_) {}
    return import.meta.env.VITE_API_URL || '/api'
}

const api = axios.create({
    baseURL: resolveBaseURL(),
    headers: {
        'Content-Type': 'application/json'
    },
    timeout: 30000, // 30초
})

// 요청 인터셉터 - 토큰 추가
api.interceptors.request.use(
    (config) => {
        const token = storage.get('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        console.error('Request error:', error)
        return Promise.reject(error)
    }
)

// 응답 인터셉터 - 에러 처리
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // 네트워크 오류
        if (!error.response) {
            console.error('Network error:', error)
            error.userMessage = ERROR_MESSAGES.NETWORK_ERROR
            return Promise.reject(error)
        }

        const {
            status
        } = error.response

        // 상태 코드별 처리
        switch (status) {
            case 401:
                // 인증 실패: 글로벌 강제 로그아웃/리다이렉트는 하지 않고 화면에서 처리
                // (일시적 토큰 지연, 권한 없는 리소스 등으로 인한 사용자 경험 보호)
                error.userMessage = ERROR_MESSAGES.UNAUTHORIZED
                break

            case 403:
                error.userMessage = ERROR_MESSAGES.FORBIDDEN
                break

            case 404:
                error.userMessage = ERROR_MESSAGES.NOT_FOUND
                break

            case 429:
                error.userMessage = ERROR_MESSAGES.RATE_LIMIT
                break

            case 500:
            case 502:
            case 503:
                error.userMessage = ERROR_MESSAGES.SERVER_ERROR
                break

            default:
                error.userMessage = errorHandler.getErrorMessage(error)
        }

        console.error('API error:', {
            status,
            url: error.config?.url,
            message: error.userMessage,
            data: error.response?.data,
        })

        return Promise.reject(error)
    }
)

// ============================================================================
// 설문조사 API
// ============================================================================

/**
 * 회원가입 후 표시할 설문 목록 조회
 */
export const getRegistrationSurveys = async () => {
    const response = await api.get('/surveys/registration')
    return response.data
}

/**
 * 설문 상세 조회
 */
export const getSurvey = async (surveyId) => {
    const response = await api.get(`/surveys/${surveyId}`)
    return response.data
}

/**
 * 설문 응답 제출
 */
export const submitSurveyResponses = async (surveyId, responses) => {
    const response = await api.post(`/surveys/${surveyId}/responses`, {
        responses
    })
    return response.data
}

/**
 * 내 설문 응답 조회
 */
export const getMySurveyResponses = async (surveyId) => {
    const response = await api.get(`/surveys/${surveyId}/responses/my`)
    return response.data
}

// ============================================================================
// 관리자 - 설문 관리 API
// ============================================================================

/**
 * 모든 설문 조회 (관리자)
 */
export const getAllSurveys = async (activeOnly = false) => {
    const response = await api.get('/surveys/', {
        params: {
            active_only: activeOnly
        }
    })
    return response.data
}

/**
 * 설문 생성 (관리자)
 */
export const createSurvey = async (surveyData) => {
    const response = await api.post('/surveys/', surveyData)
    return response.data
}

/**
 * 설문 수정 (관리자)
 */
export const updateSurvey = async (surveyId, surveyData) => {
    const response = await api.put(`/surveys/${surveyId}`, surveyData)
    return response.data
}

/**
 * 설문 삭제 (관리자)
 */
export const deleteSurvey = async (surveyId) => {
    const response = await api.delete(`/surveys/${surveyId}`)
    return response.data
}

/**
 * 설문 문항 추가 (관리자)
 */
export const addSurveyQuestion = async (surveyId, questionData) => {
    const response = await api.post(`/surveys/${surveyId}/questions`, questionData)
    return response.data
}

/**
 * 설문 문항 수정 (관리자)
 */
export const updateSurveyQuestion = async (surveyId, questionId, questionData) => {
    const response = await api.put(`/surveys/${surveyId}/questions/${questionId}`, questionData)
    return response.data
}

/**
 * 설문 문항 삭제 (관리자)
 */
export const deleteSurveyQuestion = async (surveyId, questionId) => {
    const response = await api.delete(`/surveys/${surveyId}/questions/${questionId}`)
    return response.data
}

/**
 * 설문 문항 순서 변경 (관리자)
 */
export const reorderSurveyQuestions = async (surveyId, questionOrders) => {
    const response = await api.post(`/surveys/${surveyId}/questions/reorder`, {
        question_orders: questionOrders
    })
    return response.data
}

/**
 * 설문 통계 조회 (관리자)
 */
export const getSurveyStatistics = async (surveyId) => {
    const response = await api.get(`/surveys/${surveyId}/statistics`)
    return response.data
}

/**
 * 설문 응답 조회 (관리자)
 */
export const getSurveyResponses = async (surveyId) => {
    const response = await api.get(`/surveys/${surveyId}/responses`)
    return response.data
}

export default api