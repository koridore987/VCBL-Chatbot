import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'

const AdminDashboard = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await api.get('/logs/stats')
      setStats(response.data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
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
      <h1 style={{ marginBottom: '30px' }}>관리자 대시보드</h1>
      
      {/* Stats Cards */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div className="card">
            <h3>사용자</h3>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#4CAF50', marginTop: '10px' }}>
              {stats.users.total}
            </p>
            <p style={{ color: '#666' }}>활성: {stats.users.active}</p>
          </div>
          
          <div className="card">
            <h3>채팅 세션</h3>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#2196F3', marginTop: '10px' }}>
              {stats.chat.sessions}
            </p>
            <p style={{ color: '#666' }}>메시지: {stats.chat.messages}</p>
          </div>
          
          <div className="card">
            <h3>토큰 사용량</h3>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#FF9800', marginTop: '10px' }}>
              {Math.round(stats.tokens.total / 1000)}K
            </p>
            <p style={{ color: '#666' }}>전체 토큰</p>
          </div>
          
          <div className="card">
            <h3>이벤트 로그</h3>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#9C27B0', marginTop: '10px' }}>
              {stats.events.total}
            </p>
            <p style={{ color: '#666' }}>총 이벤트</p>
          </div>
        </div>
      )}
      
      {/* Quick Links */}
      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>관리 메뉴</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <Link to="/admin/users" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              사용자 관리
            </button>
          </Link>
          
          <Link to="/admin/videos" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              비디오 관리
            </button>
          </Link>
          
          <Link to="/admin/prompts" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              프롬프트 관리
            </button>
          </Link>
          
          <Link to="/admin/logs" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              로그 관리
            </button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard

