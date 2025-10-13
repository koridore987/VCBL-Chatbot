import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import YouTube from 'react-youtube'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../services/api'
import ChatInterface from '../components/ChatInterface'
import ScaffoldingInterface from '../components/ScaffoldingInterface'
import { 
  HiChat, 
  HiClipboardList, 
  HiPlay, 
  HiCheckCircle, 
  HiClock,
  HiAcademicCap,
  HiX,
  HiExternalLink,
  HiChevronLeft,
  HiChevronRight,
  HiInformationCircle
} from 'react-icons/hi'

const LearningInterface = () => {
  const { videoId } = useParams()
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

  useEffect(() => {
    fetchVideo()
  }, [videoId])

  const fetchVideo = async () => {
    try {
      const response = await api.get(`/videos/${videoId}`)
      setVideo(response.data)
      
      // Set default tab based on scaffolding mode
      if (response.data.scaffolding_mode === 'prompt') {
        setActiveTab('scaffolding')
      } else if (response.data.scaffolding_mode === 'chat') {
        setActiveTab('chat')
      }
      
      // 학습 완료 체크 및 설문조사 모달 표시
      const progress = response.data.learning_progress
      const isNewlyCompleted = progress?.is_completed && !previousCompletionRef.current
      
      if (isNewlyCompleted && response.data.survey_url && !surveyCompleted) {
        setShowSurveyModal(true)
        // 설문조사 모달 표시 이벤트 로깅
        handleVideoEvent('survey_modal_shown', {
          survey_url: response.data.survey_url
        })
      }
      
      if (progress?.is_completed) {
        previousCompletionRef.current = true
      }
    } catch (err) {
      setError('비디오를 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }
  
  const handleSurveyOpen = () => {
    // 설문조사 열람 이벤트 로깅
    handleVideoEvent('survey_opened', {
      survey_url: video.survey_url
    })
  }
  
  const handleSurveyComplete = () => {
    // 설문조사 완료 이벤트 로깅
    handleVideoEvent('survey_completed', {
      survey_url: video.survey_url
    })
    
    setSurveyCompleted(true)
    setShowSurveyModal(false)
  }
  

  const handleVideoEvent = (eventType, eventData) => {
    console.log(`Video Event: ${eventType}`, eventData)
    api.post(`/videos/${videoId}/event`, {
      event_type: eventType,
      event_data: eventData
    }).catch(err => console.error('Failed to log event:', err))
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
    // YouTube player states:
    // -1 (unstarted), 0 (ended), 1 (playing), 2 (paused), 3 (buffering), 5 (video cued)
    const currentTime = event.target.getCurrentTime()
    const lastTime = lastPlayTimeRef.current

    // Seek 감지: 재생 중 시간이 2초 이상 차이나면 탐색으로 간주
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

  const youtubeOpts = {
    height: '100%',
    width: '100%',
    playerVars: {
      autoplay: 0,
      modestbranding: 1,    // YouTube 로고 최소화
      rel: 0,               // 관련 동영상 최소화 (같은 채널의 것만)
      showinfo: 0,          // 비디오 정보 숨김 (구버전 파라미터지만 유지)
      iv_load_policy: 3,    // 주석(annotations) 기본적으로 숨김
      disablekb: 1,         // 키보드 컨트롤 비활성화
      fs: 0,                // 전체화면 버튼 제거
    },
  }

  const showScaffolding = video.scaffolding_mode === 'prompt' || video.scaffolding_mode === 'both'
  const showChat = video.scaffolding_mode === 'chat' || video.scaffolding_mode === 'both'

  const totalSteps = 3 // 1: 안내, 2: 학습, 3: 설문
  
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
      <div className="flex flex-col lg:flex-row min-h-[calc(100dvh-5rem)] bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Video Section - 2/3 on desktop, full width on mobile */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full lg:flex-[2] p-4 sm:p-6 overflow-auto"
      >
        <div className="max-w-4xl mx-auto space-y-4">
          {/* Step Progress Bar */}
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
            
            {/* Step Indicators */}
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
            
            {/* Navigation Buttons */}
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
          
          {/* Step Content */}
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
                  {video.intro_text ? (
                    <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                      {video.intro_text}
                    </div>
                  ) : (
                    <div className="text-gray-600 bg-gray-50 p-6 rounded-lg">
                      <p className="mb-3">
                        <strong className="text-gray-800">📚 학습 목표</strong><br />
                        이 비디오를 통해 핵심 개념을 이해하고 실습할 수 있습니다.
                      </p>
                      <p className="mb-3">
                        <strong className="text-gray-800">✅ 학습 방법</strong><br />
                        1. 비디오를 주의깊게 시청하세요<br />
                        2. 학습 질문에 답변하면서 이해도를 점검하세요<br />
                        3. AI 대화를 통해 궁금한 점을 해결하세요
                      </p>
                      <p>
                        <strong className="text-gray-800">⏱️ 예상 소요 시간</strong><br />
                        약 {Math.ceil((video.duration || 600) / 60)}분 (비디오 시청 + 학습 활동)
                      </p>
                    </div>
                  )}
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
                {/* Video Title */}
                <div className="glass-card p-6 mb-4">
                  <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">{video.title}</h1>
                  {video.description && (
                    <p className="text-gray-600 leading-relaxed">{video.description}</p>
                  )}
                </div>
                
                {/* Video Player */}
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
                className="glass-card p-6 h-[calc(100vh-20rem)]"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl">
                    <HiCheckCircle className="text-3xl text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800">🎉 학습 완료!</h2>
                    <p className="text-sm text-gray-600">
                      <span className="text-red-600 font-semibold">필수</span> · 설문조사를 완료해주세요
                    </p>
                  </div>
                </div>
                
                {video.survey_url ? (
                  <div className="h-[calc(100%-5rem)] rounded-xl overflow-hidden shadow-inner bg-white">
                    <iframe
                      src={video.survey_url}
                      className="w-full h-full border-0"
                      title="설문조사"
                      loading="lazy"
                    />
                  </div>
                ) : (
                  <div className="h-[calc(100%-5rem)] flex items-center justify-center bg-gray-50 rounded-xl">
                    <div className="text-center text-gray-600">
                      <HiCheckCircle className="text-6xl mx-auto mb-4 text-green-500" />
                      <p className="text-xl font-semibold">학습을 완료했습니다!</p>
                      <p className="mt-2">설문조사 URL이 설정되지 않았습니다.</p>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
      
      {/* Scaffolding Sidebar - Only show in Step 2 */}
      {currentStep === 2 && (
        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="w-full lg:flex-1 flex flex-col shadow-2xl"
        >
          <div className="glass-card lg:rounded-tl-3xl lg:rounded-bl-3xl h-full flex flex-col overflow-hidden">
          {/* Tabs */}
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
          
          {/* Single Tab Header */}
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
          
          {/* Content with AnimatePresence for smooth transitions */}
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
  )
}

export default LearningInterface
