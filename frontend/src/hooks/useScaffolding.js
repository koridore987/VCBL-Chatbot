/**
 * 스캐폴딩 관련 커스텀 훅
 */
import {
    useState,
    useCallback
} from 'react'
import api from '../services/api'
import {
    API_ENDPOINTS
} from '../constants'

export const useScaffolding = () => {
    const [responses, setResponses] = useState({})
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    /**
     * 스캐폴딩 응답 저장
     */
    const saveResponse = useCallback(async (moduleId, scaffoldingId, responseText) => {
        try {
            setLoading(true)
            setError(null)

            await api.post(
                API_ENDPOINTS.MODULES.SCAFFOLDING_RESPOND(moduleId, scaffoldingId), {
                    response_text: responseText
                }
            )

            // 로컬 상태 업데이트
            setResponses(prev => ({
                ...prev,
                [scaffoldingId]: responseText
            }))

            return true
        } catch (err) {
            const errorMessage = err.userMessage || err.response?.data?.error || '응답 저장 실패'
            setError(errorMessage)
            throw err
        } finally {
            setLoading(false)
        }
    }, [])

    /**
     * 응답 초기화
     */
    const setInitialResponses = useCallback((scaffoldings) => {
        const initialResponses = {}
        scaffoldings.forEach(scaffolding => {
            if (scaffolding.user_response) {
                initialResponses[scaffolding.id] = scaffolding.user_response.response_text
            }
        })
        setResponses(initialResponses)
    }, [])

    /**
     * 특정 스캐폴딩 응답 가져오기
     */
    const getResponse = useCallback((scaffoldingId) => {
        return responses[scaffoldingId] || ''
    }, [responses])

    return {
        responses,
        loading,
        error,
        saveResponse,
        setInitialResponses,
        getResponse,
        setError,
    }
}

export default useScaffolding