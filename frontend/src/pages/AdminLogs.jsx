import { useEffect, useState } from 'react'
import api from '../services/api'

const AdminLogs = () => {
  const [activeTab, setActiveTab] = useState('timeline')
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [filters, setFilters] = useState({
    event_type: '',
    user_id: '',
    module_id: ''
  })
  const [expandedLog, setExpandedLog] = useState(null)
  const [users, setUsers] = useState([])
  const [videos, setVideos] = useState([])
  const [initialLoading, setInitialLoading] = useState(true)

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users')
      setUsers(response.data.data || [])
    } catch (err) {
      console.error('Failed to fetch users:', err)
      setUsers([])
    }
  }

  const fetchModules = async () => {
    try {
      const response = await api.get('/admin/modules')
      setVideos(response.data.data || [])
    } catch (err) {
      console.error('Failed to fetch modules:', err)
      setVideos([])
    }
  }

  const fetchEventLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '50',
        ...filters
      })
      
      const response = await api.get(`/logs/events?${params}`)
      setLogs(response.data.items || [])
      setTotalPages(response.data.pagination?.total_pages || 1)
    } catch (err) {
      console.error('Failed to fetch event logs:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchChatLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',  // 세션 단위이므로 더 적게
        user_id: filters.user_id || '',
        module_id: filters.module_id || ''
      })
      
      const response = await api.get(`/logs/chat-sessions-grouped?${params}`)
      setLogs(response.data.items || [])
      setTotalPages(response.data.pagination?.total_pages || 1)
    } catch (err) {
      console.error('Failed to fetch chat logs:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchTimelineLogs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '20',
        user_id: filters.user_id || '',
        module_id: filters.module_id || ''
      })
      
      const response = await api.get(`/logs/timeline?${params}`)
      setLogs(response.data.items || [])
      setTotalPages(response.data.pagination?.total_pages || 1)
    } catch (err) {
      console.error('Failed to fetch timeline logs:', err)
    } finally {
      setLoading(false)
    }
  }

  // 비디오 이벤트 타입을 한글로 변환
  const getEventTypeLabel = (eventType) => {
    const labels = {
      'video_view': '📺 비디오 접속',
      'video_play': '▶️ 재생',
      'video_pause': '⏸️ 일시정지',
      'video_seek': '⏩ 탐색',
      'video_complete': '✅ 완료',
      'scaffolding_response': '📝 스캐폴딩 응답'
    }
    return labels[eventType] || eventType
  }

  // 이벤트 데이터를 보기 좋게 포맷
  const formatEventData = (eventType, eventData) => {
    try {
      const data = typeof eventData === 'string' ? JSON.parse(eventData) : eventData
      
      if (eventType === 'video_play') {
        return `${Math.floor(data.timestamp || 0)}초에서 재생 시작`
      } else if (eventType === 'video_pause') {
        return `${Math.floor(data.timestamp || 0)}초에서 일시정지`
      } else if (eventType === 'video_seek') {
        return `${Math.floor(data.from_timestamp || 0)}초 → ${Math.floor(data.to_timestamp || 0)}초로 이동`
      } else if (eventType === 'video_complete') {
        return `비디오 시청 완료`
      }
      
      return JSON.stringify(data, null, 2)
    } catch (e) {
      return eventData || '데이터 없음'
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

  const toggleLogDetails = (logId) => {
    setExpandedLog(expandedLog === logId ? null : logId)
  }

  // 사용자 이름 찾기
  const getUserName = (userId) => {
    const user = users.find(u => u.id === userId)
    return user ? `${user.name} (${user.student_id})` : `ID: ${userId}`
  }

  // 비디오 제목 찾기
  const getModuleTitle = (moduleId) => {
    const module = videos.find(v => v.id === moduleId)
    return module ? module.title : `ID: ${moduleId}`
  }

  // 사용자 및 비디오 목록 가져오기
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        await Promise.all([fetchUsers(), fetchModules()])
      } catch (err) {
        console.error('Failed to load initial data:', err)
      } finally {
        setInitialLoading(false)
      }
    }
    loadInitialData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setPage(1)
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'events') {
      fetchEventLogs()
    } else if (activeTab === 'chat') {
      fetchChatLogs()
    } else if (activeTab === 'timeline') {
      fetchTimelineLogs()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, page])

  if (initialLoading) {
    return (
      <div className="container">
        <div className="loading">
          <div className="spinner"></div>
          <p>데이터를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '30px' }}>활동 로그</h1>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('timeline')}
          className={`btn ${activeTab === 'timeline' ? 'btn-primary' : 'btn-secondary'}`}
        >
          📊 통합 타임라인
        </button>
        <button
          onClick={() => setActiveTab('events')}
          className={`btn ${activeTab === 'events' ? 'btn-primary' : 'btn-secondary'}`}
        >
          🎬 이벤트 로그
        </button>
        <button
          onClick={() => setActiveTab('chat')}
          className={`btn ${activeTab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
        >
          💬 채팅 로그
        </button>
      </div>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>필터</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          {activeTab === 'events' && (
            <div className="form-group">
              <label className="form-label">이벤트 타입</label>
              <select
                className="form-input"
                value={filters.event_type}
                onChange={(e) => setFilters({ ...filters, event_type: e.target.value })}
              >
                <option value="">전체</option>
                <option value="video_view">🎬 비디오 조회</option>
                <option value="video_play">▶️ 재생</option>
                <option value="video_pause">⏸️ 일시정지</option>
                <option value="video_seek">⏩ 탐색</option>
                <option value="video_complete">✅ 완료</option>
                <option value="chat_message">💬 채팅</option>
              </select>
            </div>
          )}
          
          <div className="form-group">
            <label className="form-label">사용자</label>
            <select
              className="form-input"
              value={filters.user_id}
              onChange={(e) => setFilters({ ...filters, user_id: e.target.value })}
            >
              <option value="">전체 사용자</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name} ({user.student_id}) - {user.role === 'super_admin' ? '최고관리자' : user.role === 'admin' ? '관리자' : '사용자'}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label className="form-label">모듈</label>
            <select
              className="form-input"
              value={filters.module_id}
              onChange={(e) => setFilters({ ...filters, module_id: e.target.value })}
            >
              <option value="">전체 모듈</option>
              {videos.map((video) => (
                <option key={video.id} value={video.id}>
                  {video.title}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
          <button 
            onClick={() => {
              if (activeTab === 'events') fetchEventLogs()
              else if (activeTab === 'chat') fetchChatLogs()
              else fetchTimelineLogs()
            }} 
            className="btn btn-primary"
          >
            필터 적용
          </button>
          <button
            onClick={() => {
              setFilters({ event_type: '', user_id: '', module_id: '' })
              setPage(1)
            }}
            className="btn btn-secondary"
          >
            필터 초기화
          </button>
          <button
            onClick={() => handleExport(activeTab)}
            className="btn btn-secondary"
          >
            CSV 다운로드
          </button>
        </div>
      </div>
      
      {/* Logs Table */}
      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
        </div>
      ) : (
        <>
          <div className="card">
            {logs.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                로그가 없습니다
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '10px' }}>
                {logs.map((session, index) => {
                  const logId = `session-${session.id}`
                  
                  // 타임라인 탭: 메시지와 이벤트를 시간순으로 통합
                  let timelineItems = []
                  if (activeTab === 'timeline') {
                    // 메시지 추가
                    if (session.messages) {
                      session.messages.forEach(msg => {
                        timelineItems.push({
                          type: 'message',
                          timestamp: new Date(msg.created_at),
                          data: msg
                        })
                      })
                    }
                    // 비디오 이벤트 추가
                    if (session.video_events) {
                      session.video_events.forEach(event => {
                        timelineItems.push({
                          type: 'event',
                          timestamp: new Date(event.created_at),
                          data: event
                        })
                      })
                    }
                    // 시간순 정렬
                    timelineItems.sort((a, b) => a.timestamp - b.timestamp)
                  }
                  
                  return (
                  <div key={logId} className="card" style={{ padding: '15px', backgroundColor: '#f9f9f9' }}>
                    {/* 압축된 요약 정보 */}
                    <div 
                      style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        cursor: 'pointer'
                      }}
                      onClick={() => toggleLogDetails(logId)}
                    >
                      <div style={{ display: 'flex', gap: '15px', alignItems: 'center', flex: 1 }}>
                        <span style={{ fontSize: '12px', color: '#999' }}>
                          #{session.id}
                        </span>
                        {activeTab === 'timeline' ? (
                          <>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '3px',
                              backgroundColor: '#e3f2fd',
                              fontSize: '12px',
                              fontWeight: '500'
                            }}>
                              💬 학습 세션
                            </span>
                            <span style={{ fontSize: '14px', color: '#666' }}>
                              {session.user ? `${session.user.name} (${session.user.student_id})` : `사용자 ID: ${session.user_id}`}
                            </span>
                            {session.module_id && (
                              <span style={{ fontSize: '14px', color: '#666' }}>
                                📹 {getModuleTitle(session.module_id)}
                              </span>
                            )}
                            <span style={{ fontSize: '12px', color: '#666', backgroundColor: '#f3e5f5', padding: '2px 6px', borderRadius: '3px' }}>
                              {session.messages?.length || 0}개 대화
                            </span>
                            <span style={{ fontSize: '12px', color: '#666', backgroundColor: '#e8f5e9', padding: '2px 6px', borderRadius: '3px' }}>
                              {session.module_events?.length || 0}개 이벤트
                            </span>
                            {session.total_tokens > 0 && (
                              <span style={{ fontSize: '12px', color: '#666', backgroundColor: '#fff3e0', padding: '2px 6px', borderRadius: '3px' }}>
                                토큰: {session.total_tokens}
                              </span>
                            )}
                          </>
                        ) : activeTab === 'chat' ? (
                          <>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '3px',
                              backgroundColor: '#e3f2fd',
                              fontSize: '12px',
                              fontWeight: '500'
                            }}>
                              💬 대화 세션
                            </span>
                            <span style={{ fontSize: '14px', color: '#666' }}>
                              {log.user ? `${log.user.name} (${log.user.student_id})` : `사용자 ID: ${log.user_id}`}
                            </span>
                            {log.module_id && (
                              <span style={{ fontSize: '14px', color: '#666' }}>
                                📹 {getModuleTitle(log.module_id)}
                              </span>
                            )}
                            <span style={{ fontSize: '12px', color: '#666', backgroundColor: '#f3e5f5', padding: '2px 6px', borderRadius: '3px' }}>
                              {log.messages?.length || 0}개 메시지
                            </span>
                            {log.total_tokens > 0 && (
                              <span style={{ fontSize: '12px', color: '#666', backgroundColor: '#fff3e0', padding: '2px 6px', borderRadius: '3px' }}>
                                토큰: {log.total_tokens}
                              </span>
                            )}
                          </>
                        ) : (
                          <>
                            <span style={{
                              padding: '4px 8px',
                              borderRadius: '3px',
                              backgroundColor: '#e3f2fd',
                              fontSize: '12px',
                              fontWeight: '500'
                            }}>
                              {session.event_type}
                            </span>
                            <span style={{ fontSize: '14px', color: '#666' }}>
                              {getUserName(session.user_id)}
                            </span>
                            {session.module_id && (
                              <span style={{ fontSize: '14px', color: '#666' }}>
                                📹 {getModuleTitle(session.module_id)}
                              </span>
                            )}
                          </>
                        )}
                        <span style={{ fontSize: '12px', color: '#999' }}>
                          {new Date(activeTab === 'chat' || activeTab === 'timeline' ? (session.updated_at || session.created_at) : session.created_at).toLocaleString('ko-KR')}
                        </span>
                      </div>
                      <button 
                        className="btn btn-secondary"
                        style={{ padding: '4px 12px', fontSize: '12px' }}
                      >
                        {expandedLog === logId ? '닫기' : '상세보기'}
                      </button>
                    </div>
                    
                    {/* 확장된 상세 정보 */}
                    {expandedLog === logId && (
                      <div style={{ 
                        marginTop: '15px', 
                        paddingTop: '15px', 
                        borderTop: '1px solid #ddd',
                        fontSize: '14px'
                      }}>
                        {activeTab === 'timeline' ? (
                          <>
                            {/* 세션 정보 요약 */}
                            <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '5px', fontSize: '12px' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                                <div><strong>세션 ID:</strong> {session.id}</div>
                                <div><strong>메시지 수:</strong> {session.messages?.length || 0}개</div>
                                <div><strong>이벤트 수:</strong> {session.video_events?.length || 0}개</div>
                              </div>
                            </div>

                            {/* 통합 타임라인 */}
                            <div style={{ maxHeight: '600px', overflow: 'auto' }}>
                              {timelineItems.length > 0 ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                  {timelineItems.map((item, idx) => (
                                    item.type === 'message' ? (
                                      // 채팅 메시지
                                      <div 
                                        key={`msg-${item.data.id}`}
                                        style={{
                                          padding: '12px',
                                          borderRadius: '8px',
                                          backgroundColor: item.data.role === 'user' ? '#e3f2fd' : '#f3e5f5',
                                          marginLeft: item.data.role === 'user' ? '0' : '20px',
                                          marginRight: item.data.role === 'user' ? '20px' : '0',
                                        }}
                                      >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                          <strong style={{ fontSize: '13px', color: item.data.role === 'user' ? '#1976d2' : '#7b1fa2' }}>
                                            {item.data.role === 'user' ? '👤 사용자' : '🤖 AI'}
                                          </strong>
                                          <span style={{ fontSize: '11px', color: '#666' }}>
                                            {new Date(item.data.created_at).toLocaleTimeString('ko-KR')}
                                          </span>
                                        </div>
                                        <div style={{ 
                                          fontSize: '13px', 
                                          whiteSpace: 'pre-wrap', 
                                          wordBreak: 'break-word',
                                          lineHeight: '1.5'
                                        }}>
                                          {item.data.content}
                                        </div>
                                        {item.data.total_tokens > 0 && (
                                          <div style={{ marginTop: '8px', fontSize: '11px', color: '#666' }}>
                                            <span>토큰: {item.data.total_tokens}</span>
                                          </div>
                                        )}
                                      </div>
                                    ) : (
                                      // 비디오 이벤트
                                      <div 
                                        key={`evt-${item.data.id}`}
                                        style={{
                                          padding: '8px 12px',
                                          borderRadius: '6px',
                                          backgroundColor: '#e8f5e9',
                                          borderLeft: '3px solid #4caf50',
                                          margin: '0 40px'
                                        }}
                                      >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                          <div style={{ fontSize: '12px', fontWeight: '500', color: '#2e7d32' }}>
                                            {getEventTypeLabel(item.data.event_type)}
                                          </div>
                                          <span style={{ fontSize: '10px', color: '#666' }}>
                                            {new Date(item.data.created_at).toLocaleTimeString('ko-KR')}
                                          </span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>
                                          {formatEventData(item.data.event_type, item.data.event_data)}
                                        </div>
                                      </div>
                                    )
                                  ))}
                                </div>
                              ) : (
                                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                  활동 기록이 없습니다
                                </div>
                              )}
                            </div>
                          </>
                        ) : activeTab === 'chat' ? (
                          <>
                            {/* 세션 정보 */}
                            <div style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '5px', fontSize: '12px' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
                                <div><strong>세션 ID:</strong> {session.id}</div>
                                <div><strong>생성일:</strong> {new Date(session.created_at).toLocaleString('ko-KR')}</div>
                                <div><strong>총 토큰:</strong> {session.total_tokens}</div>
                                <div><strong>메시지 수:</strong> {session.messages?.length || 0}개</div>
                              </div>
                            </div>

                            {/* 대화 내용 */}
                            <div style={{ maxHeight: '500px', overflow: 'auto' }}>
                              {session.messages && session.messages.length > 0 ? (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                  {session.messages.map((message, idx) => (
                                    <div 
                                      key={message.id}
                                      style={{
                                        padding: '12px',
                                        borderRadius: '8px',
                                        backgroundColor: message.role === 'user' ? '#e3f2fd' : '#f3e5f5',
                                        marginLeft: message.role === 'user' ? '0' : '20px',
                                        marginRight: message.role === 'user' ? '20px' : '0',
                                      }}
                                    >
                                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                        <strong style={{ fontSize: '13px', color: message.role === 'user' ? '#1976d2' : '#7b1fa2' }}>
                                          {message.role === 'user' ? '👤 사용자' : '🤖 AI'}
                                        </strong>
                                        <span style={{ fontSize: '11px', color: '#666' }}>
                                          {new Date(message.created_at).toLocaleTimeString('ko-KR')}
                                        </span>
                                      </div>
                                      <div style={{ 
                                        fontSize: '13px', 
                                        whiteSpace: 'pre-wrap', 
                                        wordBreak: 'break-word',
                                        lineHeight: '1.5'
                                      }}>
                                        {message.content}
                                      </div>
                                      {message.total_tokens > 0 && (
                                        <div style={{ marginTop: '8px', fontSize: '11px', color: '#666' }}>
                                          <span style={{ marginRight: '10px' }}>프롬프트: {message.prompt_tokens}</span>
                                          <span style={{ marginRight: '10px' }}>완성: {message.completion_tokens}</span>
                                          <span>총: {message.total_tokens} 토큰</span>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                  메시지가 없습니다
                                </div>
                              )}
                            </div>
                          </>
                        ) : (
                          <>
                            <div style={{ marginBottom: '10px' }}>
                              <strong>{getEventTypeLabel(session.event_type)}</strong>
                              <div style={{ 
                                marginTop: '10px', 
                                padding: '12px', 
                                backgroundColor: '#f5f5f5', 
                                borderRadius: '6px',
                                fontSize: '13px'
                              }}>
                                {formatEventData(session.event_type, session.event_data)}
                              </div>
                            </div>
                            {session.ip_address && (
                              <div style={{ marginBottom: '5px', fontSize: '12px' }}>
                                <strong>IP 주소:</strong> {session.ip_address}
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )})}
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
