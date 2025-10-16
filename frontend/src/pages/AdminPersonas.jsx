import { useEffect, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { javascript } from '@codemirror/lang-javascript'
import api from '../services/api'
import { 
  HiCheckCircle, 
  HiXCircle, 
  HiPencil, 
  HiTrash, 
  HiPlus,
  HiLightningBolt,
  HiChatAlt2,
  HiRefresh,
  HiInformationCircle
} from 'react-icons/hi'

const AdminPersonas = () => {
  const [personas, setPersonas] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingPersona, setEditingPersona] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [selectedPersona, setSelectedPersona] = useState(null)
  const [testMessages, setTestMessages] = useState([])
  const [testInput, setTestInput] = useState('')
  const [testLoading, setTestLoading] = useState(false)

  useEffect(() => {
    fetchPersonas()
  }, [])

  const fetchPersonas = async () => {
    try {
      const response = await api.get('/admin/personas')
      const personaData = response.data.data || []
      setPersonas(personaData)
      
      // 첫 번째 페르소나를 자동 선택
      if (personaData.length > 0 && !selectedPersona) {
        setSelectedPersona(personaData[0])
      }
    } catch (err) {
      console.error('Failed to fetch personas:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (personaData) => {
    try {
      if (editingPersona) {
        await api.put(`/admin/personas/${editingPersona.id}`, personaData)
      } else {
        await api.post('/admin/personas', personaData)
      }
      setShowForm(false)
      setEditingPersona(null)
      fetchPersonas()
    } catch (err) {
      const errorMsg = err.response?.data?.error || '저장에 실패했습니다'
      alert(`저장 실패: ${errorMsg}`)
      console.error('Save error:', err.response?.data)
    }
  }

  const handleDelete = async (personaId) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      await api.delete(`/admin/personas/${personaId}`)
      fetchPersonas()
      if (selectedPersona?.id === personaId) {
        setSelectedPersona(null)
        setTestMessages([])
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || '삭제에 실패했습니다'
      alert(errorMsg)
    }
  }

  const handleToggleActivation = async (personaId) => {
    try {
      await api.put(`/admin/personas/${personaId}/activate`)
      fetchPersonas()
    } catch (err) {
      alert('활성화 변경에 실패했습니다')
    }
  }

  const handleTestChat = async () => {
    if (!testInput.trim() || !selectedPersona) return

    setTestLoading(true)
    const userMessage = testInput.trim()
    
    // 사용자 메시지 추가
    setTestMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setTestInput('')

    try {
      const response = await api.post('/admin/personas/test', {
        message: userMessage,
        persona_id: selectedPersona.id
      })
      
      // AI 응답 추가
      const aiMessage = response.data.data.message
      setTestMessages(prev => [...prev, { role: 'assistant', content: aiMessage }])
    } catch (err) {
      const errorMsg = err.response?.data?.error || '테스트 채팅 중 오류가 발생했습니다'
      alert(errorMsg)
      // 에러 발생 시 사용자 메시지 제거
      setTestMessages(prev => prev.slice(0, -1))
      setTestInput(userMessage)
    } finally {
      setTestLoading(false)
    }
  }

  const handleResetChat = () => {
    setTestMessages([])
  }

  const handleSelectPersona = (persona) => {
    setSelectedPersona(persona)
    setTestMessages([])
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="container" style={{ maxWidth: '1600px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <div>
          <h1>챗봇 페르소나 관리</h1>
          <p style={{ color: '#666', marginTop: '8px' }}>
            전역으로 적용할 챗봇 페르소나를 생성하고 관리합니다
          </p>
        </div>
        <button
          onClick={() => {
            setEditingPersona(null)
            setShowForm(true)
          }}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <HiPlus />
          페르소나 추가
        </button>
      </div>
      
      {showForm ? (
        <PersonaForm
          persona={editingPersona}
          onSave={handleSave}
          onCancel={() => {
            setShowForm(false)
            setEditingPersona(null)
          }}
        />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '60% 38%', gap: '30px' }}>
          {/* 왼쪽: 페르소나 목록 */}
          <div>
            <h2 style={{ marginBottom: '20px', fontSize: '20px' }}>페르소나 목록</h2>
            <div style={{ display: 'grid', gap: '20px' }}>
              {personas.map((persona) => (
                <div 
                  key={persona.id} 
                  className="card"
                  style={{
                    border: selectedPersona?.id === persona.id ? '2px solid #2196F3' : '1px solid #e0e0e0',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => handleSelectPersona(persona)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                        <h3 style={{ margin: 0 }}>{persona.name}</h3>
                        {persona.is_global_active && (
                          <span style={{
                            padding: '4px 12px',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            borderRadius: '20px',
                            fontSize: '12px',
                            fontWeight: 'bold',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px'
                          }}>
                            <HiCheckCircle />
                            활성
                          </span>
                        )}
                      </div>
                      <p style={{ color: '#666', margin: '5px 0 0 0' }}>{persona.description}</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleToggleActivation(persona.id)
                        }}
                        className="btn"
                        style={{
                          backgroundColor: persona.is_global_active ? '#f44336' : '#4CAF50',
                          color: 'white',
                          padding: '8px 16px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}
                        title={persona.is_global_active ? '비활성화' : '활성화'}
                      >
                        {persona.is_global_active ? <HiXCircle /> : <HiLightningBolt />}
                        {persona.is_global_active ? '비활성화' : '활성화'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setEditingPersona(persona)
                          setShowForm(true)
                        }}
                        className="btn btn-secondary"
                        style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        <HiPencil />
                        수정
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(persona.id)
                        }}
                        className="btn btn-danger"
                        style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        <HiTrash />
                        삭제
                      </button>
                    </div>
                  </div>
                </div>
              ))}
              
              {personas.length === 0 && (
                <div className="card" style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
                  <HiChatAlt2 style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.5 }} />
                  <p>아직 생성된 페르소나가 없습니다.</p>
                  <p>새로운 페르소나를 추가해보세요.</p>
                </div>
              )}
            </div>
          </div>

          {/* 오른쪽: 실시간 테스트 채팅 */}
          <div style={{ position: 'sticky', top: '20px', height: 'fit-content' }}>
            <div className="card" style={{ height: '700px', display: 'flex', flexDirection: 'column' }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '16px',
                paddingBottom: '16px',
                borderBottom: '1px solid #e0e0e0'
              }}>
                <div>
                  <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <HiChatAlt2 />
                    테스트 채팅
                  </h3>
                  {selectedPersona && (
                    <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#666' }}>
                      {selectedPersona.name}
                    </p>
                  )}
                </div>
                <button
                  onClick={handleResetChat}
                  className="btn btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px' }}
                >
                  <HiRefresh />
                  초기화
                </button>
              </div>

              {!selectedPersona ? (
                <div style={{ 
                  flex: 1, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  color: '#999',
                  textAlign: 'center'
                }}>
                  <div>
                    <HiInformationCircle style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.5 }} />
                    <p>왼쪽에서 페르소나를 선택하여</p>
                    <p>테스트 채팅을 시작하세요</p>
                  </div>
                </div>
              ) : (
                <>
                  {/* 채팅 메시지 영역 */}
                  <div style={{ 
                    flex: 1, 
                    overflowY: 'auto',
                    marginBottom: '16px',
                    padding: '16px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '8px',
                    minHeight: '400px'
                  }}>
                    {testMessages.length === 0 ? (
                      <div style={{ 
                        height: '100%', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        color: '#999'
                      }}>
                        <p>메시지를 입력하여 대화를 시작하세요</p>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {testMessages.map((msg, idx) => (
                          <div
                            key={idx}
                            style={{
                              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                              maxWidth: '80%',
                              padding: '12px 16px',
                              borderRadius: '12px',
                              backgroundColor: msg.role === 'user' ? '#2196F3' : 'white',
                              color: msg.role === 'user' ? 'white' : '#333',
                              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                              whiteSpace: 'pre-wrap'
                            }}
                          >
                            {msg.content}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 입력 영역 */}
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="text"
                      className="form-input"
                      value={testInput}
                      onChange={(e) => setTestInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !testLoading && handleTestChat()}
                      placeholder="메시지를 입력하세요..."
                      disabled={testLoading}
                      style={{ flex: 1 }}
                    />
                    <button
                      onClick={handleTestChat}
                      disabled={testLoading || !testInput.trim()}
                      className="btn btn-primary"
                      style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                    >
                      {testLoading ? '전송 중...' : '전송'}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// OpenAI 파라미터 정보
const OPENAI_PARAMS = {
  temperature: {
    label: 'Temperature',
    description: '응답의 창의성을 조절합니다 (0-2). 높을수록 다양하고 예측 불가능한 응답',
    min: 0,
    max: 2,
    step: 0.1,
    default: 0.7
  },
  max_tokens: {
    label: 'Max Tokens',
    description: '출력 토큰의 최대 개수',
    min: 1,
    max: 4000,
    step: 1,
    default: 1000
  },
  top_p: {
    label: 'Top P',
    description: '누적 확률 샘플링 (0-1). temperature 대신 사용',
    min: 0,
    max: 1,
    step: 0.01,
    default: 1
  },
  frequency_penalty: {
    label: 'Frequency Penalty',
    description: '반복되는 단어를 억제합니다 (-2 ~ 2)',
    min: -2,
    max: 2,
    step: 0.1,
    default: 0
  },
  presence_penalty: {
    label: 'Presence Penalty',
    description: '새로운 주제로의 전환을 장려합니다 (-2 ~ 2)',
    min: -2,
    max: 2,
    step: 0.1,
    default: 0
  }
}

const PersonaForm = ({ persona, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: persona?.name || '',
    description: persona?.description || '',
    system_prompt: persona?.system_prompt || '',
    constraints: persona?.constraints ? JSON.parse(persona.constraints) : {}
  })
  
  const [showParamSelector, setShowParamSelector] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!formData.name || !formData.name.trim()) {
      alert('페르소나 이름을 입력해주세요')
      return
    }
    
    if (!formData.system_prompt || !formData.system_prompt.trim()) {
      alert('시스템 프롬프트를 입력해주세요')
      return
    }
    
    const cleanedData = {
      name: formData.name.trim(),
      system_prompt: formData.system_prompt.trim(),
      constraints: Object.keys(formData.constraints).length > 0 ? formData.constraints : null
    }
    
    if (formData.description && formData.description.trim()) {
      cleanedData.description = formData.description.trim()
    }
    
    onSave(cleanedData)
  }

  const handleAddConstraint = (paramKey) => {
    const param = OPENAI_PARAMS[paramKey]
    setFormData({
      ...formData,
      constraints: {
        ...formData.constraints,
        [paramKey]: param.default
      }
    })
    setShowParamSelector(false)
  }

  const handleRemoveConstraint = (paramKey) => {
    const newConstraints = { ...formData.constraints }
    delete newConstraints[paramKey]
    setFormData({ ...formData, constraints: newConstraints })
  }

  const handleConstraintChange = (paramKey, value) => {
    setFormData({
      ...formData,
      constraints: {
        ...formData.constraints,
        [paramKey]: parseFloat(value)
      }
    })
  }

  return (
    <div className="card">
      <h2>{persona ? '페르소나 수정' : '페르소나 추가'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">페르소나 이름</label>
          <input
            type="text"
            className="form-input"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            required
            placeholder="예: 친절한 AI 조교"
          />
        </div>
        
        <div className="form-group">
          <label className="form-label">설명</label>
          <textarea
            className="form-textarea"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            style={{ minHeight: '80px' }}
            placeholder="이 페르소나에 대한 간단한 설명을 입력하세요"
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
        
        {/* OpenAI 파라미터 설정 */}
        <div className="form-group">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <label className="form-label" style={{ margin: 0 }}>OpenAI API 파라미터</label>
            <button
              type="button"
              onClick={() => setShowParamSelector(!showParamSelector)}
              className="btn btn-secondary"
              style={{ fontSize: '14px' }}
            >
              <HiPlus /> 파라미터 추가
            </button>
          </div>
          
          {showParamSelector && (
            <div style={{ 
              marginBottom: '16px', 
              padding: '12px', 
              backgroundColor: '#f5f5f5', 
              borderRadius: '8px' 
            }}>
              {Object.entries(OPENAI_PARAMS)
                .filter(([key]) => !formData.constraints[key])
                .map(([key, param]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => handleAddConstraint(key)}
                    className="btn btn-secondary"
                    style={{ marginRight: '8px', marginBottom: '8px', fontSize: '14px' }}
                  >
                    {param.label}
                  </button>
                ))}
            </div>
          )}
          
          {Object.entries(formData.constraints).length > 0 ? (
            <div style={{ display: 'grid', gap: '16px' }}>
              {Object.entries(formData.constraints).map(([key, value]) => {
                const param = OPENAI_PARAMS[key]
                if (!param) return null
                
                return (
                  <div 
                    key={key} 
                    style={{ 
                      padding: '16px', 
                      backgroundColor: '#f9f9f9', 
                      borderRadius: '8px',
                      border: '1px solid #e0e0e0'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                      <div>
                        <strong>{param.label}</strong>
                        <p style={{ fontSize: '13px', color: '#666', margin: '4px 0 0 0' }}>
                          {param.description}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveConstraint(key)}
                        className="btn btn-danger"
                        style={{ fontSize: '12px', padding: '6px 12px' }}
                      >
                        <HiTrash />
                      </button>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <input
                        type="range"
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        value={value}
                        onChange={(e) => handleConstraintChange(key, e.target.value)}
                        style={{ flex: 1 }}
                      />
                      <input
                        type="number"
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        value={value}
                        onChange={(e) => handleConstraintChange(key, e.target.value)}
                        className="form-input"
                        style={{ width: '100px' }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p style={{ color: '#999', fontSize: '14px' }}>
              파라미터를 추가하여 AI 응답 특성을 세밀하게 조정할 수 있습니다
            </p>
          )}
        </div>
        
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary">저장</button>
          <button type="button" onClick={onCancel} className="btn btn-secondary">취소</button>
        </div>
      </form>
    </div>
  )
}

export default AdminPersonas

