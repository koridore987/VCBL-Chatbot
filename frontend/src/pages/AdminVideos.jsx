import { useEffect, useState } from 'react'
import api from '../services/api'

const AdminVideos = () => {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingVideo, setEditingVideo] = useState(null)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    try {
      const response = await api.get('/videos')
      setVideos(response.data)
    } catch (err) {
      console.error('Failed to fetch videos:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (videoData) => {
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

  const handleDelete = async (videoId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      await api.delete(`/admin/videos/${videoId}`)
      fetchVideos()
    } catch (err) {
      alert('삭제에 실패했습니다')
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>비디오 관리</h1>
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
          onSave={handleSave}
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
                  <h3>{video.title}</h3>
                  <p style={{ color: '#666', margin: '10px 0' }}>{video.description}</p>
                  <p style={{ fontSize: '14px', color: '#666' }}>
                    YouTube ID: {video.youtube_id} | 모드: {video.scaffolding_mode}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
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
                    onClick={() => handleDelete(video.id)}
                    className="btn btn-danger"
                  >
                    삭제
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
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
    order_index: video?.order_index || 0
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
            <option value="both">둘 다</option>
          </select>
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

