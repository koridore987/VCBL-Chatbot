import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import YouTube from 'react-youtube'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../services/api'
import { formatters } from '../utils'
import ChatInterface from '../components/ChatInterface'
import ScaffoldingInterface from '../components/ScaffoldingInterface'
import { 
  HiChat, 
  HiClipboardList, 
  HiPlay, 
  HiCheckCircle, 
  HiAcademicCap,
  HiX,
  HiChevronLeft,
  HiChevronRight,
  HiInformationCircle,
  HiSparkles
} from 'react-icons/hi'

const LearningInterface = () => {
  const { videoId } = useParams()
  const navigate = useNavigate()
  const [video, setVideo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('scaffolding')
  const [currentStep, setCurrentStep] = useState(1) // 1: 안내, 2: 학습, 3: 설문
  const [showSurveyModal, setShowSurveyModal] = useState(false)
  const [surveyCompleted, setSurveyCompleted] = useState(false)
  const playerRef = useRef(null)
  const lastPlayTimeRef = useRef(0)
  const previousCompletionRef = useRef(false)
  const celebrationTimeoutRef = useRef(null)
  const [surveySubmitting, setSurveySubmitting] = useState(false)
  const [isFinishing, setIsFinishing] = useState(false)
  const [showCelebration, setShowCelebration] = useState(false)

  useEffect(() => {
    fetchVideo()
  }, [videoId])

  useEffect(() => {
    return () => {
      if (celebrationTimeoutRef.current) {
        clearTimeout(celebrationTimeoutRef.current)
      }
    }
  }, [])

  const fetchVideo = async () => {
    try {
      const response = await api.get(`/videos/${videoId}`)
      const videoPayload = response.data
      setVideo(videoPayload)
      
      if (videoPayload.scaffolding_mode === 'prompt') {
        setActiveTab('scaffolding')
      } else if (videoPayload.scaffolding_mode === 'chat') {
        setActiveTab('chat')
      }
      
      const progress = videoPayload.learning_progress
      const surveyAlreadyCompleted = progress?.survey_completed ?? !videoPayload.survey_url
      setSurveyCompleted(surveyAlreadyCompleted)
      const isNewlyCompleted = progress?.is_completed && !previousCompletionRef.current
      
      if (isNewlyCompleted && videoPayload.survey_url && !surveyAlreadyCompleted) {
        setShowSurveyModal(true)
        handleVideoEvent('survey_modal_shown', {
          survey_url: videoPayload.survey_url
        })
      }
      
      if (progress?.is_completed) {
        previousCompletionRef.current = true
      }

      if (progress?.status === 'completed') {
        previousCompletionRef.current = true
      }
    } catch (err) {
      setError('비디오를 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }
  
  const handleSurveyOpen = () => {
    if (!video?.survey_url) return
    handleVideoEvent('survey_opened', {
      survey_url: video.survey_url
    })
  }
  
  const handleSurveyComplete = async () => {
    if (surveySubmitting) return
    
    if (!video?.survey_url) {
      setSurveyCompleted(true)
      setShowSurveyModal(false)
      return
    }
    
    if (surveyCompleted) {
      setShowSurveyModal(false)
      return
    }
    
    try {
      setSurveySubmitting(true)
      const response = await api.post(`/videos/${videoId}/survey-complete`)
      
      handleVideoEvent('survey_completed', {
        survey_url: video.survey_url
      })
      
      const updatedProgress = response.data.learning_progress || response.data?.data?.learning_progress
      if (updatedProgress) {
        setVideo(prev => {
          if (!prev) return prev
          return {
            ...prev,
            learning_progress: {
              ...(prev.learning_progress || {}),
              ...updatedProgress
            }
          }
        })
      }
      
      setSurveyCompleted(true)
    } catch (err) {
      console.error('Failed to mark survey complete', err)
      alert('설문 완료 처리에 실패했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setSurveySubmitting(false)
      setShowSurveyModal(false)
    }
  }
  

  const handleVideoEvent = (eventType, eventData) => {
    console.log(`Video Event: ${eventType}`, eventData)
    api.post(`/videos/${videoId}/event`, {
      event_type: eventType,
      event_data: eventData
    }).catch(err => console.error('Failed to log event:', err))
  }

  const handleFinishLearning = async () => {
    if (isFinishing) return
    
    const surveyConfirmed = surveyCompleted || !video?.survey_url
    
    try {
      setIsFinishing(true)
      const response = await api.post(`/videos/${videoId}/complete`, {
        survey_confirmed: surveyConfirmed
      })
      
      const updatedProgress = response.data.learning_progress || response.data?.data?.learning_progress
      if (updatedProgress) {
        setVideo(prev => {
          if (!prev) return prev
          return {
            ...prev,
            learning_progress: {
              ...(prev.learning_progress || {}),
              ...updatedProgress
            }
          }
        })
        if (updatedProgress.survey_completed) {
          setSurveyCompleted(true)
        }
      } else if (surveyConfirmed) {
        setSurveyCompleted(true)
      }
      
      previousCompletionRef.current = true
      handleVideoEvent('learning_finish_triggered', {
        survey_confirmed: surveyConfirmed
      })
      
      setShowSurveyModal(false)
      if (celebrationTimeoutRef.current) {
        clearTimeout(celebrationTimeoutRef.current)
      }
      setShowCelebration(true)
      celebrationTimeoutRef.current = setTimeout(() => {
        setShowCelebration(false)
        navigate('/')
      }, 2500)
    } catch (err) {
      console.error('Failed to complete learning', err)
      alert('학습 종료 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setIsFinishing(false)
    }
  }

  const handlePlayerReady = (event) => {
    playerRef.current = event.target
  }

  const handlePlay = (event) => {
    const currentTime = event.target.getCurrentTime()
    handleVideoEvent('video_play', { 
      timestamp: currentTime,
      duration: event.target.getDuration()
    })
    lastPlayTimeRef.current = currentTime
  }

  const handlePause = (event) => {
    const currentTime = event.target.getCurrentTime()
    handleVideoEvent('video_pause', { 
      timestamp: currentTime,
      duration: event.target.getDuration()
    })
  }

  const handleEnd = (event) => {
    const duration = event.target.getDuration()
    handleVideoEvent('video_complete', { 
      timestamp: duration,
      duration: duration
    })
  }

  const handleStateChange = (event) => {
    const currentTime = event.target.getCurrentTime()
    const lastTime = lastPlayTimeRef.current

    if (Math.abs(currentTime - lastTime) > 2 && event.data === 1) {
      handleVideoEvent('video_seek', {
        from_timestamp: lastTime,
        to_timestamp: currentTime,
        duration: event.target.getDuration()
      })
    }

    lastPlayTimeRef.current = currentTime
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="spinner mx-auto mb-4" />
          <p className="text-gray-600 font-medium">비디오를 불러오는 중...</p>
        </motion.div>
      </div>
    )
  }

  if (error || !video) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="alert alert-error max-w-lg"
        >
          <span className="font-medium">{error || '비디오를 찾을 수 없습니다'}</span>
        </motion.div>
      </div>
    )
  }

  const learningProgress = video.learning_progress || {}
  const learningStatus = learningProgress.status || 'not_started'
  const isLearningCompleted = learningStatus === 'completed'
  const isSurveyRequired = Boolean(video.survey_url)
  const canFinishLearning = isLearningCompleted || surveyCompleted || !isSurveyRequired
  const latestProgressActivity = learningProgress.completed_at || learningProgress.last_activity_at || learningProgress.started_at

  const youtubeOpts = {
    height: '100%',
    width: '100%',
    playerVars: {
      autoplay: 0,
      modestbranding: 1,
      rel: 0,
      showinfo: 0,
      iv_load_policy: 3,
      disablekb: 1,
      fs: 0,
    },
  }

  const celebrationConfettiOffsets = [
    { className: '-top-16 -left-10', emoji: '🎉' },
    { className: '-top-12 right-0', emoji: '🎊' },
    { className: '-bottom-14 -left-6', emoji: '🎉' },
    { className: '-bottom-16 right-4', emoji: '🎊' },
  ]

  const showScaffolding = video.scaffolding_mode === 'prompt' || video.scaffolding_mode === 'both'
  const showChat = video.scaffolding_mode === 'chat' || video.scaffolding_mode === 'both'
  const hasRightPanel = showScaffolding || showChat

  const totalSteps = 3
  
  const handleNextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
      handleVideoEvent('step_navigation', { from: currentStep, to: currentStep + 1 })
    }
  }
  
  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
      handleVideoEvent('step_navigation', { from: currentStep, to: currentStep - 1 })
    }
  }

  return (
    <>
      <AnimatePresence>
        {showSurveyModal && (
          <motion.div
            key="survey-modal"
            className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="glass-card w-full max-w-md p-6 relative"
            >
              <button
                type="button"
                onClick={() => setShowSurveyModal(false)}
                className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
                aria-label="Close"
              >
                <HiX className="text-xl" />
              </button>
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg text-white">
                  <HiClipboardList className="text-xl" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-800">설문이 준비되었어요!</h3>
                  <p className="text-sm text-gray-600">
                    설문을 완료한 뒤 학습 종료 버튼을 눌러 마무리해주세요.
                  </p>
                </div>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                설문이 새 창에서 열리지 않았다면 아래 버튼을 눌러 설문 단계로 이동해 주세요.
              </p>
              <button
                type="button"
                onClick={() => {
                  setCurrentStep(3)
                  setShowSurveyModal(false)
                }}
                className="btn btn-primary w-full mt-6"
              >
                설문 단계로 이동
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showCelebration && (
          <motion.div
            key="celebration-overlay"
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className="relative">
              {celebrationConfettiOffsets.map((item, index) => (
                <motion.span
                  key={index}
                  className={`absolute ${item.className} text-3xl drop-shadow-lg`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  {item.emoji}
                </motion.span>
              ))}
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="glass-card text-center px-10 py-8 max-w-md w-full"
              >
                <motion.div
                  className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-accent-500 text-white"
                  animate={{ rotate: [0, 10, -10, 0], scale: [1, 1.08, 1] }}
                  transition={{ duration: 1.4, repeat: Infinity }}
                >
                  <HiSparkles className="text-3xl" />
                </motion.div>
                <h3 className="text-2xl font-bold text-gray-800 mb-2">학습 완료!</h3>
                <p className="text-sm text-gray-600">
                  잠시 후 홈 화면으로 이동합니다. 수고하셨어요 🎉
                </p>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-col lg:flex-row min-h-[calc(100dvh-5rem)] bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
        className={`w-full p-4 sm:p-6 overflow-auto ${hasRightPanel && currentStep === 2 ? 'lg:flex-[2]' : ''}`}
      >
        <div className={`mx-auto space-y-4 ${hasRightPanel && currentStep === 2 ? 'max-w-4xl' : 'max-w-6xl'}`}>
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg">
                  <HiAcademicCap className="text-white text-xl" />
                </div>
                <div>
                  <div className="text-sm text-gray-500">학습 진행 단계</div>
                  <div className="text-lg font-bold text-gray-800">
                    {currentStep === 1 && '안내 및 준비'}
                    {currentStep === 2 && '비디오 학습'}
                    {currentStep === 3 && '설문조사'}
                  </div>
                </div>
              </div>
              <div className="text-sm font-semibold text-primary-600">
                {currentStep} / {totalSteps}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex-1 flex items-center gap-2">
                  <div className="flex-1 flex items-center gap-2">
                    <div className={`w-full h-2 rounded-full transition-all ${
                      step <= currentStep 
                        ? 'bg-gradient-to-r from-primary-500 to-primary-600' 
                        : 'bg-gray-200'
                    }`} />
                  </div>
                </div>
              ))}
            </div>
            
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
              <motion.button
                whileHover={{ scale: currentStep > 1 ? 1.05 : 1 }}
                whileTap={{ scale: currentStep > 1 ? 0.95 : 1 }}
                onClick={handlePrevStep}
                disabled={currentStep === 1}
                className={`btn flex items-center gap-2 ${
                  currentStep === 1 
                    ? 'btn-secondary opacity-50 cursor-not-allowed' 
                    : 'btn-primary'
                }`}
              >
                <HiChevronLeft className="text-xl" />
                이전
              </motion.button>
              
              <motion.button
                whileHover={{ scale: currentStep < totalSteps ? 1.05 : 1 }}
                whileTap={{ scale: currentStep < totalSteps ? 0.95 : 1 }}
                onClick={handleNextStep}
                disabled={currentStep === totalSteps}
                className={`btn flex items-center gap-2 ${
                  currentStep === totalSteps 
                    ? 'btn-secondary opacity-50 cursor-not-allowed' 
                    : 'btn-primary'
                }`}
              >
                다음
                <HiChevronRight className="text-xl" />
              </motion.button>
            </div>
          </motion.div>
          
          <AnimatePresence mode="wait">
            {currentStep === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="glass-card p-8"
              >
                <div className="flex items-start gap-4 mb-6">
                  <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl">
                    <HiInformationCircle className="text-3xl text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-2">학습 시작 안내</h2>
                    <p className="text-sm text-gray-600">학습을 시작하기 전에 다음 내용을 확인해주세요</p>
                  </div>
                </div>
                
                <div className="prose prose-lg max-w-none">
                  {video.intro_text !== undefined && video.intro_text !== null && video.intro_text !== '' ? (
                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                      {video.intro_text}
                    </div>
                  ) : null}
                </div>
                
                <div className="mt-8 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                  <p className="text-sm text-blue-800">
                    <strong>💡 Tip:</strong> 준비가 되었다면 '다음' 버튼을 눌러 학습을 시작하세요!
                  </p>
                </div>
              </motion.div>
            )}
            
            {currentStep === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="glass-card p-6 mb-4">
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">{video.title}</h1>
                  {video.description && (
                    <p className="text-gray-600 leading-relaxed">{video.description}</p>
                  )}
                </div>
                
                <div className="relative pb-[56.25%] h-0 overflow-hidden bg-black rounded-2xl shadow-2xl">
                  <div className="absolute top-0 left-0 w-full h-full">
                    <YouTube
                      videoId={video.youtube_id}
                      opts={youtubeOpts}
                      onReady={handlePlayerReady}
                      onPlay={handlePlay}
                      onPause={handlePause}
                      onEnd={handleEnd}
                      onStateChange={handleStateChange}
                      className="w-full h-full"
                    />
                  </div>
                </div>
              </motion.div>
            )}
            
            {currentStep === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="glass-card p-6 h-[calc(100vh-20rem)] flex flex-col"
              >
                <div className="flex items-center justify-between gap-4 mb-4">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl">
                      <HiCheckCircle className="text-3xl text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-800">
                        🎉 학습을 마무리할 시간이에요!
                      </h2>
                      <p className="text-sm text-gray-600">
                        설문을 제출한 뒤 아래 버튼으로 학습을 종료하세요.
                      </p>
                    </div>
                  </div>
                  {isLearningCompleted && (
                    <span className="px-3 py-1 text-sm font-semibold rounded-full bg-emerald-100 text-emerald-600">
                      완료됨
                    </span>
                  )}
                </div>
                
                <div className="relative flex-1 rounded-2xl overflow-hidden shadow-inner bg-white border border-gray-100">
                  {video.survey_url ? (
                    <>
                      <iframe
                        src={video.survey_url}
                        className="w-full h-full border-0"
                        title="설문조사"
                        loading="lazy"
                      />
                      <div className="absolute top-4 right-4">
                        <button
                          onClick={() => {
                            handleSurveyOpen()
                            if (typeof window !== 'undefined') {
                              window.open(video.survey_url, '_blank', 'noopener,noreferrer')
                            }
                          }}
                          className="btn btn-secondary text-sm px-4 py-2"
                          type="button"
                        >
                          새 창에서 열기
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="flex h-full items-center justify-center bg-gray-50 px-6 text-center text-gray-600">
                      <div>
                        <HiCheckCircle className="text-6xl mx-auto mb-4 text-green-500" />
                        <p className="text-xl font-semibold">학습을 완료했습니다!</p>
                        <p className="mt-2">이 학습은 별도의 설문 없이 바로 종료할 수 있습니다.</p>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="mt-6 space-y-4">
                  <div
                    className={`p-4 rounded-xl border ${
                      surveyCompleted || !isSurveyRequired
                        ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                        : 'bg-blue-50 border-blue-200 text-blue-800'
                    }`}
                  >
                    <p className="font-semibold">
                      {surveyCompleted || !isSurveyRequired
                        ? '설문 확인이 완료되었어요!'
                        : '설문지를 제출한 뒤 "설문 완료" 버튼을 눌러주세요.'}
                    </p>
                    <p className="text-sm mt-1">
                      {isSurveyRequired
                        ? surveyCompleted
                          ? '이제 학습 종료 버튼을 눌러 홈 화면으로 돌아갑니다.'
                          : '설문 제출 후 아래 버튼을 눌러 학습 종료 버튼을 활성화하세요.'
                        : '이 학습에는 별도의 설문이 없어 바로 학습을 종료할 수 있습니다.'}
                    </p>
                    {latestProgressActivity && (
                      <p className="text-xs mt-2 opacity-80">
                        마지막 업데이트: {formatters.formatRelativeTime(latestProgressActivity)}
                      </p>
                    )}
                  </div>
                  
                  <div className="flex flex-wrap gap-3">
                    {isSurveyRequired && (
                      <button
                        onClick={handleSurveyComplete}
                        disabled={surveyCompleted || surveySubmitting}
                        className={`btn flex items-center gap-2 ${
                          surveyCompleted ? 'btn-secondary' : 'btn-primary'
                        }`}
                        type="button"
                      >
                        {surveyCompleted
                          ? '설문 완료됨'
                          : surveySubmitting
                            ? '확인 중...'
                            : '설문 완료'}
                      </button>
                    )}
                    <button
                      onClick={handleFinishLearning}
                      disabled={!canFinishLearning || isFinishing}
                      className={`btn flex items-center gap-2 ${
                        canFinishLearning ? 'btn-primary' : 'btn-secondary opacity-60 cursor-not-allowed'
                      }`}
                      type="button"
                    >
                      {isFinishing
                        ? '종료 처리 중...'
                        : isLearningCompleted
                          ? '홈으로 돌아가기'
                          : '학습 종료'}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
      
      {currentStep === 2 && hasRightPanel && (
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="w-full lg:flex-1 flex flex-col shadow-2xl"
        >
          <div className="glass-card lg:rounded-tl-3xl lg:rounded-bl-3xl h-full flex flex-col overflow-hidden">
          {video.scaffolding_mode === 'both' && (
            <div className="flex border-b border-gray-200/50">
              {showScaffolding && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveTab('scaffolding')}
                  className={`flex-1 flex items-center justify-center space-x-2 px-4 py-4 transition-all relative ${
                    activeTab === 'scaffolding'
                      ? 'text-primary-600 font-semibold'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  <HiClipboardList className="text-xl" />
                  <span>학습 질문</span>
                  {activeTab === 'scaffolding' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-600 to-primary-500"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </motion.button>
              )}
              {showChat && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setActiveTab('chat')}
                  className={`flex-1 flex items-center justify-center space-x-2 px-4 py-4 transition-all relative ${
                    activeTab === 'chat'
                      ? 'text-primary-600 font-semibold'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  <HiChat className="text-xl" />
                  <span>AI 대화</span>
                  {activeTab === 'chat' && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary-600 to-primary-500"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                </motion.button>
              )}
            </div>
          )}
          
          {video.scaffolding_mode !== 'both' && (
            <div className="flex border-b border-gray-200/50 px-6 py-4 bg-gradient-to-r from-primary-50/50 to-accent-50/50">
              {showScaffolding && (
                <div className="flex items-center space-x-2 text-primary-600 font-semibold">
                  <HiClipboardList className="text-xl" />
                  <span>학습 질문</span>
                </div>
              )}
              {showChat && (
                <div className="flex items-center space-x-2 text-primary-600 font-semibold">
                  <HiChat className="text-xl" />
                  <span>AI 대화</span>
                </div>
              )}
            </div>
          )}
          
          <div className="flex-1 overflow-hidden">
            <AnimatePresence mode="wait">
              {activeTab === 'scaffolding' && showScaffolding && (
                <motion.div
                  key="scaffolding"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <ScaffoldingInterface video={video} onResponseSaved={fetchVideo} />
                </motion.div>
              )}
              {activeTab === 'chat' && showChat && (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <ChatInterface videoId={videoId} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        </motion.div>
      )}
      </div>
    </>
  )
}

export default LearningInterface
