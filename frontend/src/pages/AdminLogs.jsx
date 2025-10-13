import { useEffect, useState } from 'react'
import api from '../services/api'

const AdminLogs = () => {
  const [activeTab, setActiveTab] = useState('events')
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filters, setFilters] = useState({
    event_type: '',
    user_id: '',
    video_id: ''
  })

  useEffect(() => {
    if (activeTab === 'events') {
      fetchEventLogs()
    }
  }, [page, activeTab])

  const fetchEventLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '50',
        ...filters
      })
      
      const response = await api.get(`/logs/events?${params}`)
      setLogs(response.data.logs)
      setTotalPages(response.data.pages)
    } catch (err) {
      console.error('Failed to fetch logs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (type) => {
    try {
      const params = new URLSearchParams(filters)
      const response = await api.get(
        `/logs/${type === 'events' ? 'events' : 'chat-sessions'}/export?${params}`,
        { responseType: 'blob' }
      )
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${type}_${new Date().toISOString()}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('다운로드에 실패했습니다')
    }
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '30px' }}>로그 관리</h1>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('events')}
          className={`btn ${activeTab === 'events' ? 'btn-primary' : 'btn-secondary'}`}
        >
          이벤트 로그
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`btn ${activeTab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
        >
          채팅 로그
        </button>
      </div>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>필터</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          {activeTab === 'events' && (
            <div className="form-group">
              <label className="form-label">이벤트 타입</label>
              <input
                type="text"
                className="form-input"
                value={filters.event_type}
                onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
                placeholder="video_play, chat_message 등"
              />
            </div>
          )}
          
          <div className="form-group">
            <label className="form-label">사용자 ID</label>
            <input
              type="number"
              className="form-input"
              value={filters.user_id}
              onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">비디오 ID</label>
            <input
              type="number"
              className="form-input"
              value={filters.video_id}
              onChange={(e) => setFilters({ ...filters, video_id: e.target.value })}
            />
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
          <button onClick={fetchEventLogs} className="btn btn-primary">필터 적용</button>
          <button
            onClick={() => {
              setFilters({ event_type: '', user_id: '', video_id: '' })
              setPage(1)
            }}
            className="btn btn-secondary"
          >
            필터 초기화
          </button>
        </div>
      </div>
      
      {/* Export Buttons */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        <button
          onClick={() => handleExport('events')}
          className="btn btn-primary"
        >
          이벤트 로그 CSV 다운로드
        </button>
        <button
          onClick={() => handleExport('chat')}
          className="btn btn-primary"
        >
          채팅 로그 CSV 다운로드
        </button>
      </div>
      
      {/* Logs Table */}
      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      ) : (
        <>
          <div className="card" style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ddd' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>ID</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>사용자</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>비디오</th>
                  {activeTab === 'events' && (
                    <th style={{ padding: '12px', textAlign: 'left' }}>이벤트 타입</th>
                  )}
                  <th style={{ padding: '12px', textAlign: 'left' }}>데이터</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>생성일시</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '12px' }}>{log.id}</td>
                    <td style={{ padding: '12px' }}>{log.user_id}</td>
                    <td style={{ padding: '12px' }}>{log.video_id || '-'}</td>
                    {activeTab === 'events' && (
                      <td style={{ padding: '12px' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '3px',
                          backgroundColor: '#e3f2fd',
                          fontSize: '12px'
                        }}>
                          {log.event_type}
                        </span>
                      </td>
                    )}
                    <td style={{ padding: '12px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {log.event_data?.substring(0, 50) || '-'}
                    </td>
                    <td style={{ padding: '12px', fontSize: '14px' }}>
                      {new Date(log.created_at).toLocaleString('ko-KR')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {logs.length === 0 && (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                로그가 없습니다
              </div>
            )}
          </div>
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '20px' }}>
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="btn btn-secondary"
              >
                이전
              </button>
              <span style={{ padding: '10px 20px' }}>
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className="btn btn-secondary"
              >
                다음
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default AdminLogs

