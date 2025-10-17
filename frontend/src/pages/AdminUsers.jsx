import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import SortableTable from '../components/SortableTable'

const AdminUsers = () => {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState(null)
  const [userLogs, setUserLogs] = useState([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [uploading, setUploading] = useState(false)
  const { isSuperAdmin } = useAuth()

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users')
      const userData = response.data.data || []
      setUsers(userData)
    } catch (err) {
      console.error('Failed to fetch users:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchUserLogs = async (userId) => {
    try {
      const response = await api.get(`/logs/events?user_id=${userId}&per_page=50`)
      setUserLogs(response.data.items || [])
    } catch (err) {
      console.error('Failed to fetch user logs:', err)
    }
  }

  const handleUserClick = (user) => {
    setSelectedUser(user)
    fetchUserLogs(user.id)
  }

  const handlePreRegister = async (formData) => {
    try {
      await api.post('/admin/users/pre-register', formData)
      setShowAddForm(false)
      fetchUsers()
      alert('학번이 등록되었습니다')
    } catch (err) {
      alert(err.response?.data?.error || '등록에 실패했습니다')
    }
  }

  const handleRoleChange = async (userId, newRole) => {
    if (!confirm(`사용자의 권한을 ${newRole}로 변경하시겠습니까?`)) {
      return
    }
    
    try {
      await api.put(`/admin/users/${userId}/role`, { role: newRole })
      fetchUsers()
    } catch (err) {
      alert('권한 변경에 실패했습니다')
    }
  }

  const handleActivationToggle = async (userId, isActive) => {
    try {
      await api.put(`/admin/users/${userId}/activate`, { is_active: !isActive })
      fetchUsers()
      if (selectedUser && selectedUser.id === userId) {
        setSelectedUser({ ...selectedUser, is_active: !isActive })
      }
    } catch (err) {
      alert('상태 변경에 실패했습니다')
    }
  }

  const handlePasswordReset = async (userId) => {
    const newPassword = prompt('새 비밀번호를 입력하세요:')
    if (!newPassword) return
    
    try {
      await api.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword })
      alert('비밀번호가 재설정되었습니다')
    } catch (err) {
      alert('비밀번호 재설정에 실패했습니다')
    }
  }

  const handleCSVUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return
    
    // CSV 파일 검증
    if (!file.name.endsWith('.csv')) {
      alert('CSV 파일만 업로드 가능합니다')
      return
    }
    
    const formData = new FormData()
    formData.append('file', file)
    
    setUploading(true)
    
    try {
      const response = await api.post('/admin/users/bulk-register', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const result = response.data.data || response.data
      
      let message = `등록 완료: ${result.success_count}명 성공`
      if (result.error_count > 0) {
        message += `, ${result.error_count}명 실패`
        if (result.errors && result.errors.length > 0) {
          message += '\n\n에러 내역:\n' + result.errors.join('\n')
        }
      }
      
      alert(message)
      fetchUsers()
      
    } catch (err) {
      const errorData = err.response?.data?.data
      let errorMessage = err.response?.data?.error || 'CSV 업로드에 실패했습니다'
      
      if (errorData && errorData.errors && errorData.errors.length > 0) {
        errorMessage += '\n\n에러 내역:\n' + errorData.errors.join('\n')
      }
      
      alert(errorMessage)
    } finally {
      setUploading(false)
      // 파일 입력 초기화
      event.target.value = ''
    }
  }

  const downloadCSVTemplate = () => {
    // UTF-8 BOM 추가로 Excel에서도 한글이 깨지지 않도록
    const BOM = '\uFEFF'
    const csvContent = `${BOM}student_id,name,role
2024123456,홍길동,user
2024123457,김철수,admin
2024123458,이영희,user`
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', 'student_template.csv')
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 안내 메시지
    setTimeout(() => {
      alert('CSV 템플릿이 다운로드되었습니다.\n\n주의사항:\n- 컬럼 순서: student_id, name, role\n- 학번은 10자리 숫자여야 합니다.\n- Excel에서 수정 후 CSV로 저장하세요.')
    }, 100)
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  // 사용자 상세보기
  if (selectedUser) {
    return (
      <div className="container">
        <button onClick={() => setSelectedUser(null)} className="btn btn-secondary" style={{ marginBottom: '20px' }}>
          ← 목록으로
        </button>
        
        <div className="card" style={{ marginBottom: '20px' }}>
          <h2>{selectedUser.name} ({selectedUser.student_id})</h2>
          <div style={{ marginTop: '15px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div>
              <strong>권한:</strong> {selectedUser.role}
            </div>
            <div>
              <strong>상태:</strong> {selectedUser.is_active ? '활성' : '비활성'}
            </div>
            <div>
              <strong>일일 토큰:</strong> {selectedUser.daily_token_usage || 0}
            </div>
            <div>
              <strong>총 토큰:</strong> {selectedUser.total_token_usage || 0}
            </div>
          </div>
          
          <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
            <button
              onClick={() => handleActivationToggle(selectedUser.id, selectedUser.is_active)}
              className="btn btn-secondary"
            >
              {selectedUser.is_active ? '비활성화' : '활성화'}
            </button>
            <button
              onClick={() => handlePasswordReset(selectedUser.id)}
              className="btn btn-secondary"
            >
              비밀번호 재설정
            </button>
          </div>
        </div>
        
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>학습 활동 기록</h3>
          
          <SortableTable
            data={userLogs}
            columns={[
              {
                key: 'created_at',
                label: '시간',
                sortable: true,
                searchable: false,
                width: '180px',
                render: (value) => new Date(value).toLocaleString('ko-KR')
              },
              {
                key: 'event_type',
                label: '이벤트',
                sortable: true,
                searchable: true,
                width: '150px',
                render: (value) => (
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '3px',
                    backgroundColor: '#e3f2fd',
                    fontSize: '12px'
                  }}>
                    {value}
                  </span>
                )
              },
              {
                key: 'video_id',
                label: '비디오 ID',
                sortable: true,
                width: '120px',
                render: (value) => value || '-'
              },
              {
                key: 'event_data',
                label: '상세',
                sortable: false,
                render: (value) => (
                  <div style={{ 
                    fontSize: '12px', 
                    maxWidth: '300px', 
                    overflow: 'hidden', 
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {value?.substring(0, 50) || '-'}
                  </div>
                )
              }
            ]}
            enableSearch={true}
            searchPlaceholder="이벤트 타입으로 검색..."
            emptyState={
              <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
                아직 활동 기록이 없습니다
              </p>
            }
          />
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>학생 관리</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="file"
            accept=".csv"
            onChange={handleCSVUpload}
            style={{ display: 'none' }}
            id="csv-upload"
            disabled={uploading}
          />
          <label htmlFor="csv-upload">
            <button
              className="btn btn-accent"
              onClick={() => document.getElementById('csv-upload').click()}
              disabled={uploading}
              type="button"
            >
              {uploading ? '업로드 중...' : 'CSV 대량등록'}
            </button>
          </label>
          <button
            onClick={downloadCSVTemplate}
            className="btn btn-secondary"
          >
            CSV 양식 다운로드
          </button>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn btn-primary"
          >
            {showAddForm ? '취소' : '학번 사전등록'}
          </button>
        </div>
      </div>
      
      {showAddForm && (
        <div className="card" style={{ marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '15px' }}>학번 사전등록</h3>
          <PreRegisterForm onSubmit={handlePreRegister} onCancel={() => setShowAddForm(false)} />
        </div>
      )}
      
      <div className="card">
        <SortableTable
          data={users}
          columns={[
            {
              key: 'student_id',
              label: '학번',
              sortable: true,
              searchable: true,
              width: '120px'
            },
            {
              key: 'name',
              label: '이름',
              sortable: true,
              searchable: true,
              width: '100px'
            },
            {
              key: 'role',
              label: '권한',
              sortable: true,
              width: '150px',
              render: (value, user) => (
                isSuperAdmin() && user.role !== 'super' ? (
                  <select
                    value={user.role}
                    onChange={(e) => {
                      e.stopPropagation()
                      handleRoleChange(user.id, e.target.value)
                    }}
                    onClick={(e) => e.stopPropagation()}
                    style={{ padding: '5px', borderRadius: '3px', border: '1px solid #ddd' }}
                  >
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                  </select>
                ) : (
                  <span style={{ 
                    fontWeight: user.role === 'super' ? 'bold' : 'normal',
                    color: user.role === 'super' ? '#9C27B0' : 'inherit'
                  }}>
                    {user.role === 'super' ? 'Super (보호됨)' : user.role}
                  </span>
                )
              )
            },
            {
              key: 'is_active',
              label: '상태',
              sortable: true,
              width: '90px',
              render: (value) => (
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '3px',
                  backgroundColor: value ? '#e8f5e9' : '#ffebee',
                  color: value ? '#2e7d32' : '#c62828',
                  fontSize: '12px'
                }}>
                  {value ? '활성' : '비활성'}
                </span>
              )
            },
            {
              key: 'token_usage',
              label: '토큰 (일일/전체)',
              sortable: false,
              width: '150px',
              render: (_, user) => `${user.daily_token_usage || 0} / ${user.total_token_usage || 0}`
            },
            {
              key: 'password_hash',
              label: '가입상태',
              sortable: true,
              width: '100px',
              render: (value) => (
                value ? (
                  <span style={{ color: '#4CAF50', fontSize: '12px' }}>✓ 가입완료</span>
                ) : (
                  <span style={{ color: '#FF9800', fontSize: '12px' }}>대기중</span>
                )
              )
            },
            {
              key: 'actions',
              label: '작업',
              sortable: false,
              width: '200px',
              render: (_, user) => (
                <div onClick={(e) => e.stopPropagation()}>
                  {user.role === 'super' ? (
                    <span style={{ fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                      수정 불가
                    </span>
                  ) : (
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleActivationToggle(user.id, user.is_active)
                        }}
                        className="btn btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                      >
                        {user.is_active ? '비활성화' : '활성화'}
                      </button>
                      {user.password_hash && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handlePasswordReset(user.id)
                          }}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '12px' }}
                        >
                          비밀번호 재설정
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )
            }
          ]}
          onRowClick={handleUserClick}
          enableSearch={true}
          searchPlaceholder="학번 또는 이름으로 검색..."
          emptyState={
            <div style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
              아직 등록된 학생이 없습니다
            </div>
          }
        />
      </div>
    </div>
  )
}

const PreRegisterForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    student_id: '',
    name: '',
    role: 'user'
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // 학번을 정수로 변환
    const studentIdNum = parseInt(formData.student_id)
    if (isNaN(studentIdNum) || formData.student_id.length !== 10) {
      alert('학번은 10자리 숫자여야 합니다')
      return
    }
    
    onSubmit({
      ...formData,
      student_id: studentIdNum
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">학번 (10자리)</label>
        <input
          type="text"
          className="form-input"
          value={formData.student_id}
          onChange={(e) => setFormData({ ...formData, student_id: e.target.value.replace(/\D/g, '').slice(0, 10) })}
          placeholder="10자리 학번"
          maxLength="10"
          required
        />
      </div>
      
      <div className="form-group">
        <label className="form-label">이름</label>
        <input
          type="text"
          className="form-input"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="학생 이름"
          required
        />
      </div>
      
      <div className="form-group">
        <label className="form-label">역할</label>
        <select
          className="form-input"
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
        >
          <option value="user">일반 사용자</option>
          <option value="admin">관리자</option>
        </select>
      </div>
      
      <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
        <button type="submit" className="btn btn-primary">등록</button>
        <button type="button" onClick={onCancel} className="btn btn-secondary">취소</button>
      </div>
    </form>
  )
}

export default AdminUsers
