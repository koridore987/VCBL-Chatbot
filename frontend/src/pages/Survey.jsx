import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardList, CheckCircle, AlertCircle } from 'lucide-react'
import SurveyModal from '../components/SurveyModal'
import { getRegistrationSurveys } from '../services/api'

/**
 * 설문조사 페이지 (회원가입 후)
 */
export default function Survey() {
    const navigate = useNavigate()
    const [surveys, setSurveys] = useState([])
    const [currentSurvey, setCurrentSurvey] = useState(null)
    const [completedSurveys, setCompletedSurveys] = useState(new Set())
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // 설문 목록 로드
    useEffect(() => {
        loadSurveys()
    }, [])

    const loadSurveys = async () => {
        try {
            setLoading(true)
            const response = await getRegistrationSurveys()
            const surveyList = response.data || []
            setSurveys(surveyList)

            // 이미 완료된 설문 체크
            const completed = new Set(
                surveyList.filter((s) => s.is_completed).map((s) => s.id)
            )
            setCompletedSurveys(completed)

            // 미완료 필수 설문이 있으면 자동으로 표시
            const requiredIncomplete = surveyList.find(
                (s) => s.is_required && !s.is_completed
            )
            if (requiredIncomplete) {
                setCurrentSurvey(requiredIncomplete)
            }
        } catch (err) {
            console.error('설문 목록 로드 실패:', err)
            setError(err.userMessage || '설문 목록을 불러오는데 실패했습니다.')
        } finally {
            setLoading(false)
        }
    }

    // 설문 시작
    const handleStartSurvey = (survey) => {
        setCurrentSurvey(survey)
    }

    // 설문 완료
    const handleSurveyComplete = (surveyId) => {
        setCompletedSurveys((prev) => new Set([...prev, surveyId]))
        setCurrentSurvey(null)

        // 모든 필수 설문이 완료되었는지 확인
        const allRequiredCompleted = surveys
            .filter((s) => s.is_required)
            .every((s) => s.id === surveyId || completedSurveys.has(s.id))

        // 필수 설문이 모두 완료되면 다음 페이지로 이동
        if (allRequiredCompleted) {
            // 잠시 후 홈으로 이동
            setTimeout(() => {
                navigate('/')
            }, 1500)
        }
    }

    // 설문 건너뛰기/닫기
    const handleCloseSurvey = () => {
        setCurrentSurvey(null)

        // 필수 설문이 남아있는지 확인
        const hasRequiredIncomplete = surveys.some(
            (s) => s.is_required && !completedSurveys.has(s.id)
        )

        // 필수 설문이 모두 완료되면 홈으로 이동
        if (!hasRequiredIncomplete) {
            navigate('/')
        }
    }

    // 모두 완료하고 계속하기
    const handleContinue = () => {
        navigate('/')
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">설문을 불러오는 중...</p>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
                <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center">
                    <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                        오류가 발생했습니다
                    </h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        홈으로 이동
                    </button>
                </div>
            </div>
        )
    }

    // 필수 설문이 모두 완료되었는지
    const allRequiredCompleted = surveys
        .filter((s) => s.is_required)
        .every((s) => completedSurveys.has(s.id))

    // 설문이 없는 경우
    if (surveys.length === 0) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
                <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center">
                    <ClipboardList className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                        설문이 없습니다
                    </h2>
                    <p className="text-gray-600 mb-6">
                        현재 진행 중인 설문이 없습니다.
                    </p>
                    <button
                        onClick={handleContinue}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        시작하기
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
            <div className="max-w-4xl mx-auto">
                {/* 헤더 */}
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                        설문조사
                    </h1>
                    <p className="text-lg text-gray-600">
                        학습 환경 개선을 위해 설문에 참여해주세요
                    </p>
                </div>

                {/* 진행 상황 */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">
                            진행 상황
                        </span>
                        <span className="text-sm text-gray-600">
                            {completedSurveys.size} / {surveys.length} 완료
                        </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{
                                width: `${(completedSurveys.size / surveys.length) * 100}%`,
                            }}
                        />
                    </div>
                </div>

                {/* 설문 목록 */}
                <div className="space-y-4">
                    {surveys.map((survey) => {
                        const isCompleted = completedSurveys.has(survey.id)
                        return (
                            <div
                                key={survey.id}
                                className={`bg-white rounded-lg shadow-md p-6 transition-all ${
                                    isCompleted ? 'opacity-75' : ''
                                }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <h3 className="text-xl font-semibold text-gray-900">
                                                {survey.title}
                                            </h3>
                                            {survey.is_required && (
                                                <span className="px-2 py-1 bg-red-100 text-red-600 text-xs font-medium rounded">
                                                    필수
                                                </span>
                                            )}
                                            {isCompleted && (
                                                <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-600 text-xs font-medium rounded">
                                                    <CheckCircle className="w-3 h-3" />
                                                    완료
                                                </span>
                                            )}
                                        </div>
                                        {survey.description && (
                                            <p className="text-gray-600 text-sm mb-3">
                                                {survey.description}
                                            </p>
                                        )}
                                        <p className="text-sm text-gray-500">
                                            문항 수: {survey.question_count}개
                                        </p>
                                    </div>

                                    {!isCompleted && (
                                        <button
                                            onClick={() => handleStartSurvey(survey)}
                                            className="ml-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium whitespace-nowrap"
                                        >
                                            시작하기
                                        </button>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>

                {/* 계속하기 버튼 (모든 필수 설문 완료 시) */}
                {allRequiredCompleted && (
                    <div className="mt-8 text-center">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-4">
                            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                모든 필수 설문을 완료하셨습니다!
                            </h3>
                            <p className="text-gray-600">
                                설문에 참여해주셔서 감사합니다.
                            </p>
                        </div>
                        <button
                            onClick={handleContinue}
                            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg"
                        >
                            학습 시작하기
                        </button>
                    </div>
                )}
            </div>

            {/* 설문 모달 */}
            {currentSurvey && (
                <SurveyModal
                    survey={currentSurvey}
                    onClose={handleCloseSurvey}
                    onComplete={handleSurveyComplete}
                />
            )}
        </div>
    )
}

