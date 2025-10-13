import { useState, useEffect } from 'react'
import { X, AlertCircle, CheckCircle } from 'lucide-react'
import { submitSurveyResponses } from '../services/api'

/**
 * 설문조사 모달 컴포넌트
 */
export default function SurveyModal({ survey, onClose, onComplete }) {
    const [responses, setResponses] = useState({})
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [submitError, setSubmitError] = useState(null)

    // 설문이 변경되면 응답 초기화
    useEffect(() => {
        if (survey) {
            const initialResponses = {}
            survey.questions?.forEach((question) => {
                initialResponses[question.id] = ''
            })
            setResponses(initialResponses)
            setErrors({})
            setSubmitError(null)
        }
    }, [survey])

    if (!survey) return null

    // 응답 변경 핸들러
    const handleResponseChange = (questionId, value) => {
        setResponses((prev) => ({
            ...prev,
            [questionId]: value,
        }))
        // 에러 제거
        if (errors[questionId]) {
            setErrors((prev) => {
                const newErrors = { ...prev }
                delete newErrors[questionId]
                return newErrors
            })
        }
    }

    // 유효성 검사
    const validateResponses = () => {
        const newErrors = {}
        let isValid = true

        survey.questions?.forEach((question) => {
            if (question.is_required && !responses[question.id]?.trim()) {
                newErrors[question.id] = '필수 문항입니다.'
                isValid = false
            }
        })

        setErrors(newErrors)
        return isValid
    }

    // 제출 핸들러
    const handleSubmit = async (e) => {
        e.preventDefault()
        setSubmitError(null)

        if (!validateResponses()) {
            return
        }

        setIsSubmitting(true)

        try {
            // API 형식에 맞게 변환
            const formattedResponses = Object.entries(responses)
                .filter(([_, value]) => value?.trim())
                .map(([questionId, responseText]) => ({
                    question_id: parseInt(questionId),
                    response_text: responseText,
                }))

            await submitSurveyResponses(survey.id, formattedResponses)

            // 성공 처리
            if (onComplete) {
                onComplete(survey.id)
            }
        } catch (error) {
            console.error('설문 제출 실패:', error)
            setSubmitError(
                error.response?.data?.message ||
                    error.userMessage ||
                    '설문 제출에 실패했습니다.'
            )
        } finally {
            setIsSubmitting(false)
        }
    }

    // 건너뛰기 핸들러
    const handleSkip = () => {
        if (!survey.is_required) {
            onClose()
        }
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* 헤더 */}
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900">
                            {survey.title}
                        </h2>
                        {survey.description && (
                            <p className="text-sm text-gray-600 mt-1">
                                {survey.description}
                            </p>
                        )}
                    </div>
                    {!survey.is_required && (
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    )}
                </div>

                {/* 본문 */}
                <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-4">
                    {submitError && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                            <p className="text-sm text-red-800">{submitError}</p>
                        </div>
                    )}

                    <div className="space-y-6">
                        {survey.questions?.map((question, index) => (
                            <div key={question.id} className="border-b border-gray-100 pb-6 last:border-b-0">
                                <label className="block">
                                    <div className="flex items-start gap-2 mb-3">
                                        <span className="text-sm font-medium text-gray-500">
                                            Q{index + 1}.
                                        </span>
                                        <div className="flex-1">
                                            <span className="text-base font-medium text-gray-900">
                                                {question.question_text}
                                            </span>
                                            {question.is_required && (
                                                <span className="text-red-500 ml-1">*</span>
                                            )}
                                        </div>
                                    </div>

                                    {/* 객관식 */}
                                    {question.question_type === 'multiple_choice' && (
                                        <div className="ml-8 space-y-2">
                                            {question.options?.map((option, optionIndex) => (
                                                <label
                                                    key={optionIndex}
                                                    className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
                                                >
                                                    <input
                                                        type="radio"
                                                        name={`question-${question.id}`}
                                                        value={option}
                                                        checked={responses[question.id] === option}
                                                        onChange={(e) =>
                                                            handleResponseChange(
                                                                question.id,
                                                                e.target.value
                                                            )
                                                        }
                                                        className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                                                    />
                                                    <span className="text-sm text-gray-700">
                                                        {option}
                                                    </span>
                                                </label>
                                            ))}
                                        </div>
                                    )}

                                    {/* 단답형 */}
                                    {question.question_type === 'text' && (
                                        <input
                                            type="text"
                                            value={responses[question.id] || ''}
                                            onChange={(e) =>
                                                handleResponseChange(question.id, e.target.value)
                                            }
                                            className="ml-8 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                            placeholder="답변을 입력하세요"
                                        />
                                    )}

                                    {/* 장문형 */}
                                    {question.question_type === 'textarea' && (
                                        <textarea
                                            value={responses[question.id] || ''}
                                            onChange={(e) =>
                                                handleResponseChange(question.id, e.target.value)
                                            }
                                            rows={4}
                                            className="ml-8 w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                                            placeholder="답변을 입력하세요"
                                        />
                                    )}

                                    {errors[question.id] && (
                                        <p className="ml-8 mt-2 text-sm text-red-600">
                                            {errors[question.id]}
                                        </p>
                                    )}
                                </label>
                            </div>
                        ))}
                    </div>
                </form>

                {/* 푸터 */}
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between bg-gray-50">
                    <div className="text-sm text-gray-500">
                        {survey.is_required ? (
                            <span className="text-red-600 font-medium">
                                * 필수 설문입니다
                            </span>
                        ) : (
                            <button
                                type="button"
                                onClick={handleSkip}
                                className="text-gray-600 hover:text-gray-800"
                            >
                                나중에 하기
                            </button>
                        )}
                    </div>

                    <button
                        type="submit"
                        onClick={handleSubmit}
                        disabled={isSubmitting}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
                    >
                        {isSubmitting ? '제출 중...' : '제출하기'}
                    </button>
                </div>
            </div>
        </div>
    )
}

