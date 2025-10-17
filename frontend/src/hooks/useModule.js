/**
 * 모듈 관련 커스텀 훅
 */
import {
    useState,
    useCallback
} from 'react'
import api from '../services/api'
import {
    API_ENDPOINTS
} from '../constants'

export const useModule = () => {
    const [modules, setModules] = useState([])
    const [currentModule, setCurrentModule] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    /**
     * 모든 모듈 조회
     */
    const fetchModules = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            const response = await api.get(API_ENDPOINTS.MODULES.LIST)
            // 백엔드는 { data: [...] } 형태로 반환
            const moduleData = response.data.data || []
            setModules(moduleData)

            return moduleData
        } catch (err) {
            const errorMessage = err.userMessage || err.response?.data?.error || '모듈 목록 조회 실패'
            setError(errorMessage)
            throw err
        } finally {
            setLoading(false)
        }
    }, [])

    /**
     * 특정 모듈 조회
     */
    const fetchModule = useCallback(async (moduleId) => {
        try {
            setLoading(true)
            setError(null)

            const response = await api.get(API_ENDPOINTS.MODULES.DETAIL(moduleId))
            // 백엔드는 success_response(module_data)로 반환 - dict는 merge되므로 직접 접근
            setCurrentModule(response.data)

            return response.data
        } catch (err) {
            const errorMessage = err.userMessage || err.response?.data?.error || '모듈 정보 조회 실패'
            setError(errorMessage)
            throw err
        } finally {
            setLoading(false)
        }
    }, [])

    /**
     * 모듈 이벤트 로그
     */
    const logEvent = useCallback(async (moduleId, eventType, eventData = {}) => {
        try {
            await api.post(API_ENDPOINTS.MODULES.EVENT(moduleId), {
                event_type: eventType,
                event_data: eventData
            })
        } catch (err) {
            console.error('Failed to log module event:', err)
        }
    }, [])

    /**
     * 설문 완료 처리
     */
    const markSurveyCompleted = useCallback(async (moduleId) => {
        try {
            const response = await api.post(`/modules/${moduleId}/survey-complete`)
            return response.data
        } catch (err) {
            const errorMessage = err.userMessage || err.response?.data?.error || '설문 완료 처리 실패'
            setError(errorMessage)
            throw err
        }
    }, [])

    /**
     * 학습 완료 처리
     */
    const completeLearning = useCallback(async (moduleId) => {
        try {
            const response = await api.post(`/modules/${moduleId}/complete`)
            return response.data
        } catch (err) {
            const errorMessage = err.userMessage || err.response?.data?.error || '학습 완료 처리 실패'
            setError(errorMessage)
            throw err
        }
    }, [])

    return {
        modules,
        currentModule,
        loading,
        error,
        fetchModules,
        fetchModule,
        logEvent,
        markSurveyCompleted,
        completeLearning,
        setError
    }
}




