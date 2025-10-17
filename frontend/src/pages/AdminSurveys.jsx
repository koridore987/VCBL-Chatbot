import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
    HiPlus,
    HiPencil,
    HiTrash,
    HiChartBar,
    HiClipboardList,
    HiCheckCircle,
    HiXCircle,
} from 'react-icons/hi'
import {
    getAllSurveys,
    createSurvey,
    updateSurvey,
    deleteSurvey,
    addSurveyQuestion,
    updateSurveyQuestion,
    deleteSurveyQuestion,
    getSurveyStatistics,
} from '../services/api'

/**
 * 관리자 - 설문 관리 페이지
 */
export default function AdminSurveys() {
    const [surveys, setSurveys] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [selectedSurvey, setSelectedSurvey] = useState(null)
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [showEditModal, setShowEditModal] = useState(false)
    const [showStatsModal, setShowStatsModal] = useState(false)
    const [statistics, setStatistics] = useState(null)

    useEffect(() => {
        loadSurveys()
    }, [])

    const loadSurveys = async () => {
        try {
            setLoading(true)
            const response = await getAllSurveys()
            setSurveys(response.data.data || [])
            setError(null)
        } catch (err) {
            console.error('설문 목록 로드 실패:', err)
            setError(err.userMessage || '설문 목록을 불러오는데 실패했습니다.')
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteSurvey = async (surveyId) => {
        if (!confirm('정말로 이 설문을 삭제하시겠습니까?')) {
            return
        }

        try {
            await deleteSurvey(surveyId)
            await loadSurveys()
            alert('설문이 삭제되었습니다.')
        } catch (err) {
            alert(err.userMessage || '설문 삭제에 실패했습니다.')
        }
    }

    const handleViewStats = async (survey) => {
        try {
            const response = await getSurveyStatistics(survey.id)
            setStatistics(response.data.data)
            setSelectedSurvey(survey)
            setShowStatsModal(true)
        } catch (err) {
            alert(err.userMessage || '통계 조회에 실패했습니다.')
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="spinner"></div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* 헤더 */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-4xl font-bold text-gray-900">설문 관리</h1>
                        <p className="text-gray-600 mt-2">
                            설문조사를 생성하고 관리합니다
                        </p>
                    </div>
                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="btn btn-primary flex items-center gap-2"
                    >
                        <HiPlus className="text-xl" />
                        새 설문 만들기
                    </button>
                </div>

                {error && (
                    <div className="alert alert-error mb-6">
                        <p>{error}</p>
                    </div>
                )}

                {/* 설문 목록 */}
                <div className="space-y-4">
                    {surveys.length === 0 ? (
                        <div className="glass-card p-12 text-center">
                            <HiClipboardList className="text-6xl text-gray-400 mx-auto mb-4" />
                            <p className="text-gray-600">생성된 설문이 없습니다</p>
                        </div>
                    ) : (
                        surveys.map((survey) => (
                            <motion.div
                                key={survey.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="glass-card p-6"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-xl font-bold text-gray-900">
                                                {survey.title}
                                            </h3>
                                            <div className="flex items-center gap-2">
                                                {survey.is_active ? (
                                                    <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-600 text-xs font-medium rounded">
                                                        <HiCheckCircle />
                                                        활성
                                                    </span>
                                                ) : (
                                                    <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded">
                                                        <HiXCircle />
                                                        비활성
                                                    </span>
                                                )}
                                                {survey.is_required && (
                                                    <span className="px-2 py-1 bg-red-100 text-red-600 text-xs font-medium rounded">
                                                        필수
                                                    </span>
                                                )}
                                                {survey.show_after_registration && (
                                                    <span className="px-2 py-1 bg-blue-100 text-blue-600 text-xs font-medium rounded">
                                                        회원가입용
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        {survey.description && (
                                            <p className="text-gray-600 mb-3">
                                                {survey.description}
                                            </p>
                                        )}
                                        <div className="flex items-center gap-4 text-sm text-gray-500">
                                            <span>문항 수: {survey.question_count}개</span>
                                            <span>
                                                생성일:{' '}
                                                {new Date(
                                                    survey.created_at
                                                ).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 ml-4">
                                        <button
                                            onClick={() => handleViewStats(survey)}
                                            className="btn btn-secondary flex items-center gap-2"
                                            title="통계 보기"
                                        >
                                            <HiChartBar className="text-lg" />
                                            통계
                                        </button>
                                        <button
                                            onClick={() => {
                                                setSelectedSurvey(survey)
                                                setShowEditModal(true)
                                            }}
                                            className="btn btn-secondary"
                                            title="수정"
                                        >
                                            <HiPencil className="text-lg" />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteSurvey(survey.id)}
                                            className="btn btn-danger"
                                            title="삭제"
                                        >
                                            <HiTrash className="text-lg" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ))
                    )}
                </div>
            </div>

            {/* 통계 모달 */}
            {showStatsModal && statistics && (
                <StatsModal
                    statistics={statistics}
                    onClose={() => {
                        setShowStatsModal(false)
                        setStatistics(null)
                        setSelectedSurvey(null)
                    }}
                />
            )}
        </div>
    )
}

/**
 * 통계 모달 컴포넌트
 */
function StatsModal({ statistics, onClose }) {
    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            >
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900">
                        {statistics.survey_title} - 통계
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <HiXCircle className="text-2xl" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    <div className="mb-6">
                        <p className="text-lg text-gray-600">
                            총 응답자 수:{' '}
                            <span className="font-bold text-gray-900">
                                {statistics.total_respondents}명
                            </span>
                        </p>
                    </div>

                    <div className="space-y-8">
                        {statistics.questions?.map((question, index) => (
                            <div
                                key={question.question_id}
                                className="border-b border-gray-100 pb-6 last:border-b-0"
                            >
                                <h3 className="font-semibold text-gray-900 mb-3">
                                    Q{index + 1}. {question.question_text}
                                </h3>
                                <p className="text-sm text-gray-500 mb-4">
                                    응답 수: {question.response_count}개
                                </p>

                                {question.option_counts && (
                                    <div className="space-y-3">
                                        {Object.entries(question.option_counts).map(
                                            ([option, count]) => {
                                                const percentage =
                                                    statistics.total_respondents > 0
                                                        ? Math.round(
                                                              (count /
                                                                  statistics.total_respondents) *
                                                                  100
                                                          )
                                                        : 0

                                                return (
                                                    <div key={option}>
                                                        <div className="flex items-center justify-between mb-1">
                                                            <span className="text-sm text-gray-700">
                                                                {option}
                                                            </span>
                                                            <span className="text-sm text-gray-600">
                                                                {count}명 ({percentage}%)
                                                            </span>
                                                        </div>
                                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                                            <div
                                                                className="bg-blue-600 h-2 rounded-full transition-all"
                                                                style={{
                                                                    width: `${percentage}%`,
                                                                }}
                                                            />
                                                        </div>
                                                    </div>
                                                )
                                            }
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
                    <button onClick={onClose} className="btn btn-primary w-full">
                        닫기
                    </button>
                </div>
            </motion.div>
        </div>
    )
}

