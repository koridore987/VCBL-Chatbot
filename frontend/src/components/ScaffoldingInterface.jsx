import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../services/api'
import { 
  HiChevronLeft, 
  HiChevronRight, 
  HiSave, 
  HiCheckCircle, 
  HiXCircle, 
  HiLightBulb,
  HiPencilAlt 
} from 'react-icons/hi'

const ScaffoldingInterface = ({ video, onResponseSaved }) => {
  const [scaffoldings, setScaffoldings] = useState([])
  const [responses, setResponses] = useState({})
  const [activeIndex, setActiveIndex] = useState(0)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [allAnswered, setAllAnswered] = useState(false)

  useEffect(() => {
    if (video.scaffoldings) {
      setScaffoldings(video.scaffoldings)
      
      // Initialize responses
      const initialResponses = {}
      video.scaffoldings.forEach(scaffolding => {
        if (scaffolding.user_response) {
          initialResponses[scaffolding.id] = scaffolding.user_response.response_text
        } else {
          initialResponses[scaffolding.id] = ''
        }
      })
      setResponses(initialResponses)
    }
  }, [video])

  // Check if all questions are answered
  useEffect(() => {
    if (scaffoldings.length === 0) {
      setAllAnswered(false)
      return
    }
    
    const answered = scaffoldings.every(scaffolding => {
      const response = responses[scaffolding.id]
      return response && response.trim() !== ''
    })
    setAllAnswered(answered)
  }, [responses, scaffoldings])

  const handleSaveAll = async () => {
    setSaving(true)
    setMessage('')
    
    try {
      // Prepare all responses
      const responsesToSave = scaffoldings.map(scaffolding => ({
        scaffolding_id: scaffolding.id,
        response_text: responses[scaffolding.id] || ''
      }))
      
      // Save all responses at once
      await api.post(
        `/modules/${video.id}/scaffoldings/respond-bulk`,
        { responses: responsesToSave }
      )
      
      setMessage('success')
      setTimeout(() => setMessage(''), 3000)
      
      // 부모 컴포넌트에 저장 완료 알림
      if (onResponseSaved) {
        onResponseSaved()
      }
    } catch (err) {
      setMessage('error')
      setTimeout(() => setMessage(''), 3000)
    } finally {
      setSaving(false)
    }
  }

  if (!scaffoldings || scaffoldings.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center h-full p-8 text-center"
      >
        <div className="w-20 h-20 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl flex items-center justify-center mb-4 shadow-lg">
          <HiLightBulb className="text-4xl text-gray-400" />
        </div>
        <p className="text-gray-600 font-medium">아직 등록된 학습 질문이 없습니다.</p>
      </motion.div>
    )
  }

  const currentScaffolding = scaffoldings[activeIndex]

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-50/50 to-white/50">
      {/* Navigation Header */}
      <div className="flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm border-b border-gray-200/50">
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setActiveIndex(Math.max(0, activeIndex - 1))}
          disabled={activeIndex === 0}
          className={`flex items-center space-x-1 px-4 py-2 rounded-xl transition-all shadow-md ${
            activeIndex === 0
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-primary-50 to-accent-50 text-primary-700 hover:shadow-lg border border-primary-200'
          }`}
        >
          <HiChevronLeft className="text-lg" />
          <span className="text-sm font-semibold">이전</span>
        </motion.button>
        
        <div className="flex items-center space-x-2">
          <span className="px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-500 text-white rounded-xl text-sm font-bold shadow-md">
            {activeIndex + 1} / {scaffoldings.length}
          </span>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setActiveIndex(Math.min(scaffoldings.length - 1, activeIndex + 1))}
          disabled={activeIndex === scaffoldings.length - 1}
          className={`flex items-center space-x-1 px-4 py-2 rounded-xl transition-all shadow-md ${
            activeIndex === scaffoldings.length - 1
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-primary-50 to-accent-50 text-primary-700 hover:shadow-lg border border-primary-200'
          }`}
        >
          <span className="text-sm font-semibold">다음</span>
          <HiChevronRight className="text-lg" />
        </motion.button>
      </div>
      
      {/* Content with AnimatePresence */}
      <div className="flex-1 overflow-auto p-6 space-y-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            {/* Question Number */}
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-600 to-primary-500 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-md">
                  {activeIndex + 1}
                </div>
              </div>
            </div>
            
            {/* Question Prompt - only show if prompt_text is not empty */}
            {currentScaffolding.prompt_text && currentScaffolding.prompt_text.trim() !== '' && (
              <div className="glass-card bg-gradient-to-br from-blue-50/80 to-indigo-50/80 border-l-4 border-blue-500 p-5 rounded-2xl">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-md">
                    <HiLightBulb className="text-2xl text-white" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-blue-900 mb-2 text-base">학습 질문</h4>
                    <p className="text-blue-800 whitespace-pre-wrap leading-relaxed text-sm">
                      {currentScaffolding.prompt_text}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Answer Textarea */}
            <div>
              <label className="flex items-center space-x-2 text-sm font-bold text-gray-700 mb-3">
                <HiPencilAlt className="text-primary-600" />
                <span>답변 작성</span>
              </label>
              <textarea
                className="w-full px-5 py-4 bg-white/80 backdrop-blur-sm border-2 border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none transition-all text-sm shadow-md"
                value={responses[currentScaffolding.id] || ''}
                onChange={(e) => setResponses({
                  ...responses,
                  [currentScaffolding.id]: e.target.value
                })}
                placeholder="여기에 답변을 작성하세요..."
                rows={10}
              />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Fixed Bottom Save Button */}
      <div className="p-4 bg-white/80 backdrop-blur-sm border-t border-gray-200/50">
        <motion.button
          whileHover={{ scale: allAnswered ? 1.02 : 1 }}
          whileTap={{ scale: allAnswered ? 0.98 : 1 }}
          onClick={handleSaveAll}
          disabled={!allAnswered || saving}
          className={`w-full flex items-center justify-center space-x-2 px-6 py-4 rounded-2xl font-bold transition-all shadow-lg ${
            !allAnswered || saving
              ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-primary-600 to-primary-500 text-white hover:shadow-xl'
          }`}
        >
          <HiSave className="text-xl" />
          <span>
            {saving 
              ? '저장 중...' 
              : allAnswered 
                ? '모든 답변 저장하기' 
                : `답변 완료 (${scaffoldings.filter(s => responses[s.id]?.trim()).length}/${scaffoldings.length})`
            }
          </span>
        </motion.button>
        
        {/* Success/Error Message */}
        <AnimatePresence>
          {message && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`mt-3 flex items-center space-x-3 p-4 rounded-2xl shadow-lg ${
                message === 'success'
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 text-green-700 border border-green-200'
                  : 'bg-gradient-to-r from-red-50 to-pink-50 text-red-700 border border-red-200'
              }`}
            >
              {message === 'success' ? (
                <>
                  <HiCheckCircle className="text-3xl flex-shrink-0" />
                  <span className="font-semibold">모든 답변이 성공적으로 저장되었습니다!</span>
                </>
              ) : (
                <>
                  <HiXCircle className="text-3xl flex-shrink-0" />
                  <span className="font-semibold">저장에 실패했습니다. 다시 시도해주세요.</span>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default ScaffoldingInterface
