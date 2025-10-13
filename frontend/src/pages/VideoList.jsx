import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

const VideoList = () => {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    try {
      const response = await api.get('/videos')
      setVideos(response.data)
    } catch (err) {
      setError('비디오 목록을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
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
      <h1 style={{ marginBottom: '30px' }}>학습 비디오</h1>
      
      {error && <div className="alert alert-error">{error}</div>}
      
      {videos.length === 0 ? (
        <div className="card">
          <p style={{ textAlign: 'center', color: '#666' }}>
            아직 등록된 비디오가 없습니다.
          </p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
          {videos.map((video) => (
            <Link
              key={video.id}
              to={`/videos/${video.id}`}
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <div className="card" style={{ cursor: 'pointer', transition: 'transform 0.2s' }}
                   onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
                   onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
                {video.thumbnail_url && (
                  <img
                    src={video.thumbnail_url}
                    alt={video.title}
                    style={{ width: '100%', borderRadius: '5px', marginBottom: '15px' }}
                  />
                )}
                <h3 style={{ marginBottom: '10px' }}>{video.title}</h3>
                {video.description && (
                  <p style={{ color: '#666', fontSize: '14px' }}>
                    {video.description.substring(0, 100)}
                    {video.description.length > 100 ? '...' : ''}
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default VideoList

