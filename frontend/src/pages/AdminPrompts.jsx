import { useEffect, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { javascript } from '@codemirror/lang-javascript'
import api from '../services/api'

const AdminPrompts = () => {
  const [prompts, setPrompts] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingPrompt, setEditingPrompt] = useState(null)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    fetchPrompts()
  }, [])

  const fetchPrompts = async () => {
    try {
      const response = await api.get('/admin/prompts')
      // 백엔드는 { data: [...] } 형태로 반환
      const promptData = response.data.data || []
      setPrompts(promptData)
    } catch (err) {
      console.error('Failed to fetch prompts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (promptData) => {
    try {
      if (editingPrompt) {
        await api.put(`/admin/prompts/${editingPrompt.id}`, promptData)
      } else {
        await api.post('/admin/prompts', promptData)
      }
      setShowForm(false)
      setEditingPrompt(null)
      fetchPrompts()
    } catch (err) {
      const errorMsg = err.response?.data?.error || '저장에 실패했습니다'
      alert(`저장 실패: ${errorMsg}`)
      console.error('Save error:', err.response?.data)
    }
  }

  const handleDelete = async (promptId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      await api.delete(`/admin/prompts/${promptId}`)
      fetchPrompts()
    } catch (err) {
      alert(err.response?.data?.error || '삭제에 실패했습니다')
    }
  }

  const handleToggleActive = async (promptId, isActive) => {
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1>프롬프트 엔지니어링</h1>
        <button
          onClick={() => {
            setEditingPrompt(null)
            setShowForm(true)
          }}
          className="btn btn-primary"
        >
          프롬프트 추가
        </button>
      </div>
      
      {showForm ? (
        <PromptForm
          prompt={editingPrompt}
          onSave={handleSave}
          onCancel={() => {
            setShowForm(false)
            setEditingPrompt(null)
          }}
        />
      ) : (
        <div style={{ display: 'grid', gap: '20px' }}>
          {prompts.map((prompt) => (
            <div key={prompt.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                <div style={{ flex: 1 }}>
                  <h3>
                    {prompt.name}
                    {prompt.is_default && (
                      <span style={{
                        marginLeft: '10px',
                        padding: '4px 8px',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        borderRadius: '3px',
                        fontSize: '12px'
                      }}>
                        기본
                      </span>
                    )}
                    {!prompt.is_active && (
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
                  </h3>
                  <p style={{ color: '#666', margin: '5px 0' }}>{prompt.description}</p>
                  <p style={{ fontSize: '14px', color: '#666' }}>
                    버전: {prompt.version} | 
                    {prompt.video_id && ` 비디오 ID: ${prompt.video_id} |`}
                    {prompt.user_role && ` 권한: ${prompt.user_role}`}
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => handleToggleActive(prompt.id, prompt.is_active)}
                    className="btn btn-secondary"
                  >
                    {prompt.is_active ? '비활성화' : '활성화'}
                  </button>
                  <button
                    onClick={() => {
                      setEditingPrompt(prompt)
                      setShowForm(true)
                    }}
                    className="btn btn-secondary"
                  >
                    수정
                  </button>
                  <button
                    onClick={() => handleDelete(prompt.id)}
                    className="btn btn-danger"
                  >
                    삭제
                  </button>
                </div>
              </div>
              
              <div style={{ marginTop: '15px' }}>
                <h4 style={{ marginBottom: '10px', fontSize: '14px' }}>시스템 프롬프트:</h4>
                <div style={{
                  backgroundColor: '#f5f5f5',
                  padding: '15px',
                  borderRadius: '5px',
                  whiteSpace: 'pre-wrap',
                  fontSize: '14px',
                  fontFamily: 'monospace',
                  maxHeight: '200px',
                  overflow: 'auto'
                }}>
                  {prompt.system_prompt}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
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
    
    // 필수 필드 검증
    if (!formData.name || !formData.name.trim()) {
      alert('프롬프트 이름을 입력해주세요')
      return
    }
    
    if (!formData.system_prompt || !formData.system_prompt.trim()) {
      alert('시스템 프롬프트를 입력해주세요')
      return
    }
    
    // 빈 문자열을 null로 변환하고 불필요한 필드 제거
    const cleanedData = {
      name: formData.name.trim(),
      system_prompt: formData.system_prompt.trim(),
      is_default: formData.is_default
    }
    
    // 선택 필드는 값이 있을 때만 포함
    if (formData.description && formData.description.trim()) {
      cleanedData.description = formData.description.trim()
    }
    
    if (formData.constraints && formData.constraints.trim()) {
      cleanedData.constraints = formData.constraints.trim()
    }
    
    if (formData.video_id && formData.video_id !== '') {
      cleanedData.video_id = Number(formData.video_id)
    }
    
    if (formData.user_role && formData.user_role !== '') {
      cleanedData.user_role = formData.user_role
    }
    
    console.log('전송할 데이터:', cleanedData)
    onSave(cleanedData)
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

export default AdminPrompts

