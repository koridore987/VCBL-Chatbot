import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { formatters } from '../utils'

const AdminDashboard = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [progress, setProgress] = useState(null)
  const [progressLoading, setProgressLoading] = useState(true)

  const fetchStats = async () => {
    try {
      const response = await api.get('/logs/stats')
      setStats(response.data.data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchProgress = async () => {
    try {
      const response = await api.get('/admin/progress?limit=25')
      setProgress(response.data.data)
    } catch (err) {
      console.error('Failed to fetch progress:', err)
    } finally {
      setProgressLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    setProgressLoading(true)
    fetchProgress()
    const intervalId = setInterval(fetchProgress, 10000)
    return () => clearInterval(intervalId)
  }, [])

  const statusMeta = {
    completed: { label: '완료', color: '#2E7D32', background: '#E8F5E9' },
    in_progress: { label: '진행 중', color: '#1565C0', background: '#E3F2FD' },
    not_started: { label: '미시작', color: '#616161', background: '#F5F5F5' }
  }

  const progressCounts = progress?.status_counts || {}
  const recentProgress = progress?.recent || []

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
              {Math.round((stats.tokens.total || 0) / 1000)}K
            </p>
            <p style={{ color: '#666' }}>
              오늘: {Math.round((stats.tokens.daily || 0) / 1000)}K
            </p>
            {stats.tokens.from_messages !== undefined && (
              <p style={{ fontSize: '11px', color: '#999', marginTop: '8px' }}>
                메시지: {Math.round((stats.tokens.from_messages || 0) / 1000)}K / 
                사용자: {Math.round((stats.tokens.from_users || 0) / 1000)}K
              </p>
            )}
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

      <div className="card" style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>실시간 학습 현황</h2>
          <button
            className="btn btn-secondary"
            style={{ minWidth: '110px' }}
            onClick={() => {
              setProgressLoading(true)
              fetchProgress()
            }}
          >
            새로고침
          </button>
        </div>
        {progressLoading ? (
          <div className="loading" style={{ padding: '20px 0' }}>
            <div className="spinner"></div>
          </div>
        ) : !progress ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#777' }}>
            진행 상황 데이터를 불러오지 못했습니다.
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', marginBottom: '20px' }}>
              {Object.entries(statusMeta).map(([key, meta]) => (
                <div key={key} style={{ flex: '1 1 160px', background: meta.background, borderRadius: '12px', padding: '14px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: meta.color, textTransform: 'uppercase' }}>{meta.label}</div>
                  <div style={{ fontSize: '28px', fontWeight: 'bold', color: meta.color, marginTop: '6px' }}>
                    {progressCounts[key] || 0}
                  </div>
                </div>
              ))}
            </div>

            {recentProgress.length > 0 ? (
              <div style={{ display: 'grid', gap: '12px' }}>
                {recentProgress.map((entry) => {
                  const activityTimestamp = entry.last_activity_at || entry.updated_at
                  const completionTimestamp = entry.completed_at
                  const status = statusMeta[entry.status] || statusMeta.not_started
                  return (
                    <div
                      key={entry.id}
                      style={{
                        padding: '16px',
                        border: '1px solid #ececec',
                        borderRadius: '12px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        background: '#fafafa'
                      }}
                    >
                      <div style={{ flex: 1, marginRight: '16px' }}>
                        <div style={{ fontWeight: 600, fontSize: '15px', marginBottom: '4px' }}>
                          {entry.user?.name || '알 수 없음'}
                          {entry.user?.student_id && (
                            <span style={{ fontSize: '12px', color: '#888', marginLeft: '8px' }}>
                              ({entry.user.student_id})
                            </span>
                          )}
                        </div>
                        <div style={{ color: '#555', fontSize: '14px', marginBottom: '6px' }}>
                          {entry.video?.title || '제목 없음'}
                        </div>
                        <div style={{ fontSize: '12px', color: '#999' }}>
                          업데이트: {activityTimestamp ? formatters.formatRelativeTime(activityTimestamp) : '-'}
                          {activityTimestamp && (
                            <span style={{ marginLeft: '6px' }}>
                              ({formatters.formatDate(activityTimestamp)})
                            </span>
                          )}
                          {completionTimestamp && (
                            <span style={{ marginLeft: '8px', color: '#2E7D32' }}>
                              완료: {formatters.formatRelativeTime(completionTimestamp)}
                            </span>
                          )}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span
                          style={{
                            display: 'inline-block',
                            padding: '6px 12px',
                            borderRadius: '999px',
                            fontSize: '12px',
                            fontWeight: 600,
                            color: status.color,
                            background: status.background
                          }}
                        >
                          {status.label}
                        </span>
                        {entry.survey_completed && (
                          <div style={{ fontSize: '11px', color: '#2E7D32', marginTop: '6px' }}>설문 완료</div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: '#777', fontSize: '14px' }}>
                최근 학습 활동이 없습니다.
              </div>
            )}
          </>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>관리 메뉴</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <Link to="/admin/students" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              학생 관리
            </button>
          </Link>
          
          <Link to="/admin/content" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              콘텐츠 관리
            </button>
          </Link>
          
          <Link to="/admin/logs" style={{ textDecoration: 'none' }}>
            <button className="btn btn-primary" style={{ width: '100%' }}>
              활동 로그
            </button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
