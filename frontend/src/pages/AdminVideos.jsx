import { useEffect, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { javascript } from '@codemirror/lang-javascript'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import {
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../services/api'

// 재사용 가능한 2-Column 레이아웃 컴포넌트
const TwoColumnLayout = ({ 
  leftPanel, 
  rightPanel, 
  showRightPanel, 
  onCloseRightPanel,
  rightPanelTitle,
  rightPanelContent 
}) => {
  return (
    <div style={{ 
      display: 'flex', 
      gap: '20px', 
      height: '80vh',
      minHeight: '600px',
      maxHeight: '800px'
    }}>
      {/* Left Panel */}
      <div style={{ 
        flex: showRightPanel ? '0 0 40%' : '1', 
        display: 'flex', 
        flexDirection: 'column',
        borderRight: showRightPanel ? '1px solid #e5e7eb' : 'none',
        paddingRight: showRightPanel ? '20px' : '0',
        transition: 'all 0.4s ease-in-out'
      }}>
        {leftPanel}
      </div>
      
      {/* Right Panel */}
      <AnimatePresence>
        {showRightPanel && (
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 50 }}
            transition={{ 
              duration: 0.4, 
              ease: "easeInOut"
            }}
            style={{ 
              flex: '0 0 60%', 
              display: 'flex', 
              flexDirection: 'column',
              paddingLeft: '20px',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              backgroundColor: '#fafafa',
              overflow: 'hidden'
            }}
          >
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              marginBottom: '20px',
              padding: '20px 20px 0 20px'
            }}>
              <h3>{rightPanelTitle}</h3>
              <button
                onClick={onCloseRightPanel}
                className="btn btn-secondary"
                style={{ fontSize: '14px', padding: '8px 16px' }}
              >
                닫기
              </button>
            </div>
            
            <div style={{ 
              flex: 1, 
              overflowY: 'auto',
              padding: '0 20px 20px 20px'
            }}>
              {rightPanelContent}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// 드롭 인디케이터 컴포넌트
const DropIndicator = ({ isVisible }) => (
  <div
    style={{
      height: '3px',
      backgroundColor: '#3b82f6',
      borderRadius: '2px',
      margin: '8px 0',
      opacity: isVisible ? 1 : 0,
      transition: 'opacity 0.2s ease',
      boxShadow: '0 0 8px rgba(59, 130, 246, 0.5)'
    }}
  />
)

// 드래그 핸들 아이콘 컴포넌트
const DragHandle = () => (
  <svg 
    width="20" 
    height="20" 
    viewBox="0 0 20 20" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    style={{ 
      cursor: 'grab',
      color: '#9ca3af',
      transition: 'all 0.2s ease'
    }}
  >
    <circle cx="7" cy="5" r="1.5" fill="currentColor" opacity="0.6"/>
    <circle cx="13" cy="5" r="1.5" fill="currentColor" opacity="0.6"/>
    <circle cx="7" cy="10" r="1.5" fill="currentColor" opacity="0.6"/>
    <circle cx="13" cy="10" r="1.5" fill="currentColor" opacity="0.6"/>
    <circle cx="7" cy="15" r="1.5" fill="currentColor" opacity="0.6"/>
    <circle cx="13" cy="15" r="1.5" fill="currentColor" opacity="0.6"/>
  </svg>
)

// 정렬 가능한 질문 아이템 컴포넌트
const SortableScaffoldingItem = ({ scaffolding, index, isActive, isSelected, onEdit, onDelete }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
    isOver,
  } = useSortable({ id: scaffolding.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isDragging ? 'none' : transition,
    opacity: isDragging ? 0.8 : 1,
    zIndex: isDragging ? 1000 : 'auto',
    boxShadow: isDragging ? '0 8px 25px rgba(0,0,0,0.15)' : 'none',
    borderRadius: isDragging ? '8px' : '4px',
    border: isDragging ? '2px solid #3b82f6' : '1px solid #e5e7eb',
    backgroundColor: isDragging ? '#f8fafc' : 'white',
    scale: isDragging ? '1.02' : '1',
  }

  return (
    <div
      ref={setNodeRef}
      style={{
        ...style,
        border: isSelected ? '2px solid #3b82f6' : style.border,
        backgroundColor: isSelected ? '#f0f9ff' : style.backgroundColor,
        boxShadow: isSelected ? '0 4px 12px rgba(59, 130, 246, 0.15)' : style.boxShadow
      }}
      className="card"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', minHeight: '60px' }}>
        {/* 드래그 핸들 - 중앙에 위치 */}
        <div
          {...attributes}
          {...listeners}
          style={{ 
            display: 'flex', 
            alignItems: 'center',
            justifyContent: 'center',
            cursor: isDragging ? 'grabbing' : 'grab',
            padding: '8px',
            marginRight: '12px',
            borderRadius: '6px',
            backgroundColor: isDragging ? '#e0f2fe' : 'transparent',
            border: isDragging ? '1px solid #0ea5e9' : '1px solid transparent',
            transition: 'all 0.2s ease',
            minWidth: '32px',
            minHeight: '32px'
          }}
          onMouseEnter={(e) => {
            if (!isDragging) {
              e.target.style.backgroundColor = '#f1f5f9'
              e.target.style.borderColor = '#cbd5e1'
              e.target.style.transform = 'scale(1.05)'
            }
          }}
          onMouseLeave={(e) => {
            if (!isDragging) {
              e.target.style.backgroundColor = 'transparent'
              e.target.style.borderColor = 'transparent'
              e.target.style.transform = 'scale(1)'
            }
          }}
        >
          <DragHandle />
        </div>
        
        <div style={{ flex: 1 }}>
          <h4>질문 {index + 1}: {scaffolding.title}</h4>
          <p style={{ color: '#666', marginTop: '10px', whiteSpace: 'pre-wrap' }}>
            {scaffolding.prompt_text}
          </p>
          <p style={{ fontSize: '14px', color: '#999', marginTop: '5px' }}>
            순서: {scaffolding.order_index}
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => onEdit(scaffolding)}
            className="btn btn-secondary"
          >
            수정
          </button>
          <button
            onClick={() => onDelete(scaffolding.id)}
            className="btn btn-danger"
          >
            삭제
          </button>
        </div>
      </div>
    </div>
  )
}

const AdminVideos = () => {
  const [activeTab, setActiveTab] = useState('videos')
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingVideo, setEditingVideo] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [selectedVideo, setSelectedVideo] = useState(null)
  const [scaffoldings, setScaffoldings] = useState([])
  const [prompts, setPrompts] = useState([])
  const [editingPrompt, setEditingPrompt] = useState(null)
  const [showPromptForm, setShowPromptForm] = useState(false)

  useEffect(() => {
    fetchVideos()
    fetchPrompts()
  }, [])

  const fetchVideos = async () => {
    try {
      const response = await api.get('/admin/videos')
      const videoData = response.data.data || []
      setVideos(videoData)
    } catch (err) {
      console.error('Failed to fetch videos:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchScaffoldings = async (videoId) => {
    try {
      const response = await api.get(`/videos/${videoId}`)
      const videoData = response.data.data || response.data
      setScaffoldings(videoData.scaffoldings || [])
    } catch (err) {
      console.error('Failed to fetch scaffoldings:', err)
    }
  }

  const handleSaveVideo = async (videoData) => {
    try {
      if (editingVideo) {
        await api.put(`/admin/videos/${editingVideo.id}`, videoData)
      } else {
        await api.post('/admin/videos', videoData)
      }
      setShowForm(false)
      setEditingVideo(null)
      fetchVideos()
    } catch (err) {
      alert('저장에 실패했습니다')
    }
  }

  const handleDeleteVideo = async (videoId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      await api.delete(`/admin/videos/${videoId}`)
      fetchVideos()
    } catch (err) {
      alert('삭제에 실패했습니다')
    }
  }

  const handleToggleLearning = async (video) => {
    try {
      await api.put(`/admin/videos/${video.id}`, {
        learning_enabled: !video.learning_enabled
      })
      fetchVideos()
    } catch (err) {
      alert('학습 권한 변경에 실패했습니다')
    }
  }

  const handleChangeMode = async (video, newMode) => {
    try {
      await api.put(`/admin/videos/${video.id}`, {
        scaffolding_mode: newMode
      })
      fetchVideos()
    } catch (err) {
      alert('학습 모드 변경에 실패했습니다')
    }
  }

  const handleSaveScaffolding = async (scaffoldingData) => {
    try {
      if (scaffoldingData.id) {
        await api.put(`/admin/scaffoldings/${scaffoldingData.id}`, scaffoldingData)
      } else {
        await api.post(`/admin/videos/${selectedVideo.id}/scaffoldings`, scaffoldingData)
      }
      fetchScaffoldings(selectedVideo.id)
    } catch (err) {
      alert('저장에 실패했습니다')
    }
  }

  const handleDeleteScaffolding = async (scaffoldingId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      await api.delete(`/admin/scaffoldings/${scaffoldingId}`)
      fetchScaffoldings(selectedVideo.id)
    } catch (err) {
      alert('삭제에 실패했습니다')
    }
  }

  const handleReorderScaffoldings = async (reorderData) => {
    try {
      await api.put(`/admin/videos/${selectedVideo.id}/scaffoldings/reorder`, {
        scaffoldings: reorderData
      })
      fetchScaffoldings(selectedVideo.id)
    } catch (err) {
      alert('순서 변경에 실패했습니다')
    }
  }

  const fetchPrompts = async () => {
    try {
      const response = await api.get('/admin/prompts')
      const promptData = response.data.data || []
      setPrompts(promptData)
    } catch (err) {
      console.error('Failed to fetch prompts:', err)
    }
  }

  const handleSavePrompt = async (promptData) => {
    try {
      if (editingPrompt) {
        await api.put(`/admin/prompts/${editingPrompt.id}`, promptData)
      } else {
        await api.post('/admin/prompts', promptData)
      }
      setShowPromptForm(false)
      setEditingPrompt(null)
      fetchPrompts()
    } catch (err) {
      alert('저장에 실패했습니다')
    }
  }

  const handleDeletePrompt = async (promptId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      await api.delete(`/admin/prompts/${promptId}`)
      fetchPrompts()
    } catch (err) {
      alert(err.response?.data?.error || '삭제에 실패했습니다')
    }
  }

  const handleTogglePromptActive = async (promptId, isActive) => {
    try {
      await api.put(`/admin/prompts/${promptId}`, { is_active: !isActive })
      fetchPrompts()
    } catch (err) {
      alert('상태 변경에 실패했습니다')
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '30px' }}>콘텐츠 관리</h1>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '2px solid #e0e0e0' }}>
        <button
          onClick={() => {
            setActiveTab('videos')
            setSelectedVideo(null)
          }}
          className={`btn ${activeTab === 'videos' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0' }}
        >
          비디오 관리
        </button>
        <button
          onClick={() => setActiveTab('questions')}
          className={`btn ${activeTab === 'questions' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0' }}
        >
          학습질문 관리
        </button>
        <button
          onClick={() => {
            setActiveTab('prompts')
            setSelectedVideo(null)
          }}
          className={`btn ${activeTab === 'prompts' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: '8px 8px 0 0' }}
        >
          프롬프트 엔지니어링
        </button>
      </div>
      
      {/* Video Management Tab */}
      {activeTab === 'videos' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
            <button
              onClick={() => {
                setEditingVideo(null)
                setShowForm(true)
              }}
              className="btn btn-primary"
            >
              비디오 추가
            </button>
          </div>
          
          {showForm ? (
            <VideoForm
              video={editingVideo}
              onSave={handleSaveVideo}
              onCancel={() => {
                setShowForm(false)
                setEditingVideo(null)
              }}
            />
          ) : (
            <div style={{ display: 'grid', gap: '20px' }}>
              {videos.map((video) => (
                <div key={video.id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <h3>
                        {video.title}
                        {!video.is_active && (
                          <span style={{
                            marginLeft: '10px',
                            padding: '4px 8px',
                            backgroundColor: '#f44336',
                            color: 'white',
                            borderRadius: '3px',
                            fontSize: '12px'
                          }}>
                            비활성
                          </span>
                        )}
                        {video.learning_enabled ? (
                          <span style={{
                            marginLeft: '10px',
                            padding: '4px 8px',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            borderRadius: '3px',
                            fontSize: '12px'
                          }}>
                            학습 가능
                          </span>
                        ) : (
                          <span style={{
                            marginLeft: '10px',
                            padding: '4px 8px',
                            backgroundColor: '#FF9800',
                            color: 'white',
                            borderRadius: '3px',
                            fontSize: '12px'
                          }}>
                            학습 잠김
                          </span>
                        )}
                      </h3>
                      <p style={{ color: '#666', margin: '10px 0' }}>{video.description}</p>
                      <p style={{ fontSize: '14px', color: '#666' }}>
                        YouTube ID: {video.youtube_id} | 순서: {video.order_index}
                      </p>
                      <div style={{ marginTop: '10px' }}>
                        <label style={{ fontSize: '14px', color: '#666', marginRight: '8px' }}>학습 모드:</label>
                        <select
                          value={video.scaffolding_mode}
                          onChange={(e) => handleChangeMode(video, e.target.value)}
                          className="form-input"
                          style={{ 
                            display: 'inline-block', 
                            width: 'auto', 
                            padding: '4px 8px',
                            fontSize: '14px'
                          }}
                        >
                          <option value="none">없음</option>
                          <option value="prompt">질문만</option>
                          <option value="chat">채팅만</option>
                        </select>
                        <small style={{ color: '#666', fontSize: '12px', marginLeft: '8px', display: 'block', marginTop: '4px' }}>
                          하나의 모드만 선택 가능합니다
                        </small>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => handleToggleLearning(video)}
                        className="btn btn-secondary"
                        style={{ fontSize: '14px' }}
                      >
                        {video.learning_enabled ? '학습 잠금' : '학습 열기'}
                      </button>
                    {video.survey_url && (
                      <a
                        href={video.survey_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-secondary"
                        style={{ fontSize: '14px' }}
                      >
                        설문 열기
                      </a>
                    )}
                      <button
                        onClick={() => {
                          setEditingVideo(video)
                          setShowForm(true)
                        }}
                        className="btn btn-secondary"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => handleDeleteVideo(video.id)}
                        className="btn btn-danger"
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                {(video.survey_url || video.intro_text) && (
                  <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #eee' }}>
                    {video.survey_url && (
                      <p style={{ fontSize: '13px', color: '#555', wordBreak: 'break-all', marginBottom: '6px' }}>
                        <strong>설문:</strong> {video.survey_url}
                      </p>
                    )}
                    {video.intro_text && (
                      <p style={{ fontSize: '13px', color: '#555', whiteSpace: 'pre-wrap', maxHeight: '6em', overflow: 'hidden' }}>
                        <strong>안내:</strong> {video.intro_text}
                      </p>
                    )}
                  </div>
                )}
                </div>
              ))}
            </div>
          )}
        </>
      )}
      
      {/* Questions Management Tab */}
      {activeTab === 'questions' && (
        <div>
          {!selectedVideo ? (
            <div>
              <h2 style={{ marginBottom: '20px' }}>비디오를 선택하세요</h2>
              <div style={{ display: 'grid', gap: '15px' }}>
                {videos.map((video) => (
                  <div
                    key={video.id}
                    className="card"
                    style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                    onClick={() => {
                      setSelectedVideo(video)
                      fetchScaffoldings(video.id)
                    }}
                  >
                    <h3>{video.title}</h3>
                    <p style={{ fontSize: '14px', color: '#666', marginTop: '5px' }}>
                      모드: {video.scaffolding_mode}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <ScaffoldingManager
              video={selectedVideo}
              scaffoldings={scaffoldings}
              onSave={handleSaveScaffolding}
              onDelete={handleDeleteScaffolding}
              onBack={() => setSelectedVideo(null)}
              onReorder={handleReorderScaffoldings}
            />
          )}
        </div>
      )}

      {/* Prompt Engineering Tab */}
      {activeTab === 'prompts' && (
        <TwoColumnLayout
          leftPanel={
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h3>프롬프트 목록</h3>
                <button
                  onClick={() => {
                    setEditingPrompt(null)
                    setShowPromptForm(true)
                  }}
                  className="btn btn-primary"
                >
                  프롬프트 추가
                </button>
              </div>
              
              <div style={{ 
                flex: 1, 
                overflowY: 'auto', 
                display: 'flex', 
                flexDirection: 'column', 
                gap: '15px' 
              }}>
                {prompts.map((prompt) => (
                  <div 
                    key={prompt.id} 
                    className="card"
                    style={{ 
                      cursor: 'pointer',
                      border: editingPrompt?.id === prompt.id ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                      backgroundColor: editingPrompt?.id === prompt.id ? '#f0f9ff' : 'white',
                      boxShadow: editingPrompt?.id === prompt.id ? '0 4px 12px rgba(59, 130, 246, 0.15)' : 'none',
                      transition: 'all 0.2s ease'
                    }}
                    onClick={() => {
                      setEditingPrompt(prompt)
                      setShowPromptForm(true)
                    }}
                  >
                    <div style={{ marginBottom: '10px' }}>
                      <h4 style={{ margin: '0 0 5px 0', fontSize: '16px' }}>
                        {prompt.name}
                        {prompt.is_default && (
                          <span style={{
                            marginLeft: '8px',
                            padding: '2px 6px',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            borderRadius: '3px',
                            fontSize: '11px'
                          }}>
                            기본
                          </span>
                        )}
                        {!prompt.is_active && (
                          <span style={{
                            marginLeft: '8px',
                            padding: '2px 6px',
                            backgroundColor: '#f44336',
                            color: 'white',
                            borderRadius: '3px',
                            fontSize: '11px'
                          }}>
                            비활성
                          </span>
                        )}
                      </h4>
                      <p style={{ color: '#666', margin: '0 0 8px 0', fontSize: '14px' }}>{prompt.description}</p>
                      <p style={{ fontSize: '12px', color: '#999', margin: '0' }}>
                        버전: {prompt.version} | 
                        {prompt.video_id && ` 비디오 ID: ${prompt.video_id} |`}
                        {prompt.user_role && ` 권한: ${prompt.user_role}`}
                      </p>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '8px', marginTop: '10px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleTogglePromptActive(prompt.id, prompt.is_active)
                        }}
                        className="btn btn-secondary"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                      >
                        {prompt.is_active ? '비활성화' : '활성화'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeletePrompt(prompt.id)
                        }}
                        className="btn btn-danger"
                        style={{ fontSize: '12px', padding: '4px 8px' }}
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          }
          showRightPanel={showPromptForm}
          onCloseRightPanel={() => {
            setShowPromptForm(false)
            setEditingPrompt(null)
          }}
          rightPanelTitle={editingPrompt ? '프롬프트 수정' : '프롬프트 추가'}
          rightPanelContent={
            <PromptForm
              prompt={editingPrompt}
              onSave={handleSavePrompt}
              onCancel={() => {
                setShowPromptForm(false)
                setEditingPrompt(null)
              }}
            />
          }
        />
      )}
    </div>
  )
}

const VideoForm = ({ video, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    title: video?.title || '',
    youtube_url: video?.youtube_url || '',
    youtube_id: video?.youtube_id || '',
    description: video?.description || '',
    scaffolding_mode: video?.scaffolding_mode || 'both',
    order_index: video?.order_index || 0,
    is_active: video?.is_active !== undefined ? video.is_active : true,
    learning_enabled: video?.learning_enabled !== undefined ? video.learning_enabled : false,
    survey_url: video?.survey_url || '',
    intro_text: video?.intro_text || ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="card">
      <h2>{video ? '비디오 수정' : '비디오 추가'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">제목</label>
          <input
            type="text"
            className="form-input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">YouTube URL</label>
          <input
            type="url"
            className="form-input"
            value={formData.youtube_url}
            onChange={(e) => setFormData({ ...formData, youtube_url: e.target.value })}
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">YouTube ID</label>
          <input
            type="text"
            className="form-input"
            value={formData.youtube_id}
            onChange={(e) => setFormData({ ...formData, youtube_id: e.target.value })}
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">설명</label>
          <textarea
            className="form-textarea"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">스캐폴딩 모드</label>
          <select
            className="form-input"
            value={formData.scaffolding_mode}
            onChange={(e) => setFormData({ ...formData, scaffolding_mode: e.target.value })}
          >
            <option value="none">없음</option>
            <option value="prompt">질문만</option>
            <option value="chat">채팅만</option>
          </select>
          <small style={{ color: '#666', fontSize: '13px', marginTop: '5px', display: 'block' }}>
            하나의 모드만 선택 가능합니다. 질문만 또는 채팅만 중 하나를 선택하세요.
          </small>
        </div>
        
        <div className="form-group">
          <label className="form-label">순서</label>
          <input
            type="number"
            className="form-input"
            value={formData.order_index}
            onChange={(e) => setFormData({ ...formData, order_index: parseInt(e.target.value) })}
            min="0"
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">설문조사 URL (선택사항)</label>
          <input
            type="url"
            className="form-input"
            value={formData.survey_url}
            onChange={(e) => setFormData({ ...formData, survey_url: e.target.value })}
            placeholder="https://docs.google.com/forms/d/e/..."
          />
          <small style={{ color: '#666', fontSize: '13px', marginTop: '5px', display: 'block' }}>
            구글 폼 등 설문조사 링크를 입력하세요. 학습 완료 후 <strong style={{ color: '#d32f2f' }}>필수로</strong> 진행됩니다.
          </small>
        </div>
        
        <div className="form-group">
          <label className="form-label">학습 시작 안내 텍스트 (선택사항)</label>
          <textarea
            className="form-input"
            value={formData.intro_text}
            onChange={(e) => setFormData({ ...formData, intro_text: e.target.value })}
            placeholder="학습을 시작하기 전에 학생들에게 보여줄 안내 메시지를 입력하세요..."
            rows="6"
            style={{ resize: 'vertical', fontFamily: 'inherit', lineHeight: '1.5' }}
          />
          <small style={{ color: '#666', fontSize: '13px', marginTop: '5px', display: 'block' }}>
            학습 단계 1에서 표시될 안내 메시지입니다. 학습 목표, 주의사항 등을 포함할 수 있습니다.
          </small>
        </div>
        
        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
            />
            <span>활성 상태</span>
          </label>
        </div>
        
        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.learning_enabled}
              onChange={(e) => setFormData({ ...formData, learning_enabled: e.target.checked })}
            />
            <span>학습 허용</span>
          </label>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary">저장</button>
          <button type="button" onClick={onCancel} className="btn btn-secondary">취소</button>
        </div>
      </form>
    </div>
  )
}

const ScaffoldingManager = ({ video, scaffoldings, onSave, onDelete, onBack, onReorder }) => {
  const [editing, setEditing] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [localScaffoldings, setLocalScaffoldings] = useState(scaffoldings)
  const [activeId, setActiveId] = useState(null)

  // scaffoldings가 변경될 때 로컬 상태 업데이트
  useEffect(() => {
    setLocalScaffoldings(scaffoldings)
  }, [scaffoldings])

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragStart = (event) => {
    setActiveId(event.active.id)
  }

  const handleDragEnd = (event) => {
    const { active, over } = event
    setActiveId(null)

    if (active.id !== over.id) {
      const oldIndex = localScaffoldings.findIndex(item => item.id === active.id)
      const newIndex = localScaffoldings.findIndex(item => item.id === over.id)
      
      const newScaffoldings = arrayMove(localScaffoldings, oldIndex, newIndex)
      setLocalScaffoldings(newScaffoldings)
      
      // 순서 재정렬 API 호출
      const reorderData = newScaffoldings.map((item, index) => ({
        id: item.id,
        order_index: index + 1
      }))
      
      onReorder(reorderData)
    }
  }

  const leftPanel = (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3>질문 목록</h3>
        <button
          onClick={() => {
            setEditing(null)
            setShowForm(true)
          }}
          className="btn btn-primary"
        >
          질문 추가
        </button>
      </div>
      
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '15px' 
      }}>
        {localScaffoldings.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            아직 등록된 학습질문이 없습니다
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={localScaffoldings.map(item => item.id)}
              strategy={verticalListSortingStrategy}
            >
              {localScaffoldings.map((scaffolding, index) => (
                <SortableScaffoldingItem
                  key={scaffolding.id}
                  scaffolding={scaffolding}
                  index={index}
                  isActive={activeId === scaffolding.id}
                  isSelected={editing?.id === scaffolding.id}
                  onEdit={(scaffolding) => {
                    setEditing(scaffolding)
                    setShowForm(true)
                  }}
                  onDelete={onDelete}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}
      </div>
    </>
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <button onClick={onBack} className="btn btn-secondary" style={{ marginBottom: '10px' }}>
            ← 뒤로가기
          </button>
          <h2>{video.title} - 학습질문 관리</h2>
        </div>
      </div>

      <TwoColumnLayout
        leftPanel={leftPanel}
        showRightPanel={showForm}
        onCloseRightPanel={() => {
          setShowForm(false)
          setEditing(null)
        }}
        rightPanelTitle={editing ? '질문 수정' : '질문 추가'}
        rightPanelContent={
          <ScaffoldingForm
            scaffolding={editing}
            onSave={(data) => {
              onSave(data)
              setShowForm(false)
              setEditing(null)
            }}
            onCancel={() => {
              setShowForm(false)
              setEditing(null)
            }}
          />
        }
      />
    </div>
  )
}

const ScaffoldingForm = ({ scaffolding, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    title: scaffolding?.title || '',
    prompt_text: scaffolding?.prompt_text || ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (scaffolding) {
      onSave({ ...formData, id: scaffolding.id })
    } else {
      onSave(formData)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">질문 제목 (관리자용)</label>
        <input
          type="text"
          className="form-input"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          placeholder="예: 이 영상에서 가장 인상 깊었던 장면은?"
          required
        />
      </div>
      
      <div className="form-group">
        <label className="form-label">질문 내용 (학습자에게 표시)</label>
        <textarea
          className="form-textarea"
          value={formData.prompt_text}
          onChange={(e) => setFormData({ ...formData, prompt_text: e.target.value })}
          placeholder="학습자가 답변할 질문을 입력하세요"
          rows="5"
          required
        />
      </div>
      
      <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
        <button type="submit" className="btn btn-primary">저장</button>
        <button type="button" onClick={onCancel} className="btn btn-secondary">취소</button>
      </div>
    </form>
  )
}

const PromptForm = ({ prompt, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: prompt?.name || '',
    description: prompt?.description || '',
    system_prompt: prompt?.system_prompt || '',
    constraints: prompt?.constraints || '',
    video_id: prompt?.video_id || '',
    user_role: prompt?.user_role || '',
    is_default: prompt?.is_default || false
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(formData)
  }

  return (
    <div className="card">
      <h2>{prompt ? '프롬프트 수정' : '프롬프트 추가'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">이름</label>
          <input
            type="text"
            className="form-input"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">설명</label>
          <textarea
            className="form-textarea"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            style={{ minHeight: '80px' }}
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">시스템 프롬프트</label>
          <CodeMirror
            value={formData.system_prompt}
            height="300px"
            extensions={[javascript()]}
            onChange={(value) => setFormData({ ...formData, system_prompt: value })}
            theme="light"
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">제약 조건 (JSON 형식)</label>
          <textarea
            className="form-textarea"
            value={formData.constraints}
            onChange={(e) => setFormData({ ...formData, constraints: e.target.value })}
            placeholder='{"max_length": 500, "forbidden_topics": ["정치", "종교"]}'
            style={{ minHeight: '100px', fontFamily: 'monospace' }}
          />
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
          <div className="form-group">
            <label className="form-label">비디오 ID (선택사항)</label>
            <input
              type="number"
              className="form-input"
              value={formData.video_id}
              onChange={(e) => setFormData({ ...formData, video_id: e.target.value })}
              placeholder="특정 비디오에만 적용"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">사용자 권한 (선택사항)</label>
            <select
              className="form-input"
              value={formData.user_role}
              onChange={(e) => setFormData({ ...formData, user_role: e.target.value })}
            >
              <option value="">모든 권한</option>
              <option value="user">User</option>
              <option value="admin">Admin</option>
              <option value="super">Super</option>
            </select>
          </div>
        </div>
        
        <div className="form-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={formData.is_default}
              onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
            />
            <span>기본 프롬프트로 설정</span>
          </label>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary">저장</button>
          <button type="button" onClick={onCancel} className="btn btn-secondary">취소</button>
        </div>
      </form>
    </div>
  )
}

export default AdminVideos
