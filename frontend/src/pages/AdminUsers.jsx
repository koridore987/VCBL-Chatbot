import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

const AdminUsers = () => {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const { isSuperAdmin } = useAuth()

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users')
      setUsers(response.data)
    } catch (err) {
      console.error('Failed to fetch users:', err)
    } finally {
      setLoading(false)
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

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '30px' }}>사용자 관리</h1>
      
      <div className="card" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '12px', textAlign: 'left' }}>학번</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>이름</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>권한</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>상태</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>토큰 사용량</th>
              <th style={{ padding: '12px', textAlign: 'left' }}>작업</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '12px' }}>{user.student_id}</td>
                <td style={{ padding: '12px' }}>{user.name}</td>
                <td style={{ padding: '12px' }}>
                  {isSuperAdmin() ? (
                    <select
                      value={user.role}
                      onChange={(e) => handleRoleChange(user.id, e.target.value)}
                      style={{ padding: '5px', borderRadius: '3px', border: '1px solid #ddd' }}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                      <option value="super">Super</option>
                    </select>
                  ) : (
                    <span>{user.role}</span>
                  )}
                </td>
                <td style={{ padding: '12px' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '3px',
                    backgroundColor: user.is_active ? '#e8f5e9' : '#ffebee',
                    color: user.is_active ? '#2e7d32' : '#c62828',
                    fontSize: '12px'
                  }}>
                    {user.is_active ? '활성' : '비활성'}
                  </span>
                </td>
                <td style={{ padding: '12px' }}>
                  {user.daily_token_usage} / {user.total_token_usage}
                </td>
                <td style={{ padding: '12px' }}>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    <button
                      onClick={() => handleActivationToggle(user.id, user.is_active)}
                      className="btn btn-secondary"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      {user.is_active ? '비활성화' : '활성화'}
                    </button>
                    <button
                      onClick={() => handlePasswordReset(user.id)}
                      className="btn btn-secondary"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      비밀번호 재설정
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default AdminUsers

