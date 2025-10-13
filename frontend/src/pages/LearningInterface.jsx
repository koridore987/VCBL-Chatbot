import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import YouTube from 'react-youtube'
import api from '../services/api'
import ChatInterface from '../components/ChatInterface'
import ScaffoldingInterface from '../components/ScaffoldingInterface'

const LearningInterface = () => {
  const { videoId } = useParams()
  const [video, setVideo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('scaffolding')

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
    } catch (err) {
      setError('비디오를 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleVideoEvent = (eventType, eventData) => {
    api.post(`/videos/${videoId}/event`, {
      event_type: eventType,
      event_data: eventData
    }).catch(err => console.error('Failed to log event:', err))
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  if (error || !video) {
    return (
      <div className="container">
        <div className="alert alert-error">{error || '비디오를 찾을 수 없습니다'}</div>
      </div>
    )
  }

  const youtubeOpts = {
    height: '100%',
    width: '100%',
    playerVars: {
      autoplay: 0,
    },
  }

  const showScaffolding = video.scaffolding_mode === 'prompt' || video.scaffolding_mode === 'both'
  const showChat = video.scaffolding_mode === 'chat' || video.scaffolding_mode === 'both'

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 80px)' }}>
      {/* Video Section - 2/3 */}
      <div style={{ flex: '2', padding: '20px', overflow: 'auto' }}>
        <h1 style={{ marginBottom: '20px' }}>{video.title}</h1>
        
        {video.description && (
          <p style={{ marginBottom: '20px', color: '#666' }}>{video.description}</p>
        )}
        
        <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', backgroundColor: '#000' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
            <YouTube
              videoId={video.youtube_id}
              opts={youtubeOpts}
              onPlay={() => handleVideoEvent('video_play', {})}
              onPause={() => handleVideoEvent('video_pause', {})}
              onEnd={() => handleVideoEvent('video_end', {})}
            />
          </div>
        </div>
      </div>
      
      {/* Scaffolding Section - 1/3 */}
      <div style={{ flex: '1', borderLeft: '1px solid #ddd', backgroundColor: '#f9f9f9', display: 'flex', flexDirection: 'column' }}>
        {/* Tabs */}
        {video.scaffolding_mode === 'both' && (
          <div style={{ display: 'flex', borderBottom: '1px solid #ddd' }}>
            {showScaffolding && (
              <button
                onClick={() => setActiveTab('scaffolding')}
                style={{
                  flex: 1,
                  padding: '15px',
                  border: 'none',
                  backgroundColor: activeTab === 'scaffolding' ? 'white' : '#f0f0f0',
                  cursor: 'pointer',
                  fontWeight: activeTab === 'scaffolding' ? 'bold' : 'normal',
                  borderBottom: activeTab === 'scaffolding' ? '2px solid #4CAF50' : 'none'
                }}
              >
                학습 질문
              </button>
            )}
            {showChat && (
              <button
                onClick={() => setActiveTab('chat')}
                style={{
                  flex: 1,
                  padding: '15px',
                  border: 'none',
                  backgroundColor: activeTab === 'chat' ? 'white' : '#f0f0f0',
                  cursor: 'pointer',
                  fontWeight: activeTab === 'chat' ? 'bold' : 'normal',
                  borderBottom: activeTab === 'chat' ? '2px solid #4CAF50' : 'none'
                }}
              >
                AI 대화
              </button>
            )}
          </div>
        )}
        
        {/* Content */}
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {activeTab === 'scaffolding' && showScaffolding && (
            <ScaffoldingInterface video={video} />
          )}
          {activeTab === 'chat' && showChat && (
            <ChatInterface videoId={videoId} />
          )}
        </div>
      </div>
    </div>
  )
}

export default LearningInterface

