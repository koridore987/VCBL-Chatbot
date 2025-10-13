import { useState, useEffect } from 'react'
import api from '../services/api'

const ScaffoldingInterface = ({ video }) => {
  const [scaffoldings, setScaffoldings] = useState([])
  const [responses, setResponses] = useState({})
  const [activeIndex, setActiveIndex] = useState(0)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (video.scaffoldings) {
      setScaffoldings(video.scaffoldings)
      
      // Initialize responses
      const initialResponses = {}
      video.scaffoldings.forEach(scaffolding => {
        if (scaffolding.user_response) {
          initialResponses[scaffolding.id] = scaffolding.user_response.response_text
        } else {
          initialResponses[scaffolding.id] = ''
        }
      })
      setResponses(initialResponses)
    }
  }, [video])

  const handleSave = async (scaffoldingId) => {
    setSaving(true)
    setMessage('')
    
    try {
      await api.post(
        `/videos/${video.id}/scaffoldings/${scaffoldingId}/respond`,
        { response_text: responses[scaffoldingId] }
      )
      setMessage('저장되었습니다')
    } catch (err) {
      setMessage('저장에 실패했습니다')
    } finally {
      setSaving(false)
    }
  }

  if (!scaffoldings || scaffoldings.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        <p>아직 등록된 학습 질문이 없습니다.</p>
      </div>
    )
  }

  const currentScaffolding = scaffoldings[activeIndex]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Navigation */}
      <div style={{ padding: '15px', borderBottom: '1px solid #ddd', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={() => setActiveIndex(Math.max(0, activeIndex - 1))}
          disabled={activeIndex === 0}
          className="btn btn-secondary"
          style={{ padding: '5px 10px', fontSize: '12px' }}
        >
          이전
        </button>
        <span style={{ flex: 1, textAlign: 'center', fontSize: '14px', fontWeight: 'bold' }}>
          질문 {activeIndex + 1} / {scaffoldings.length}
        </span>
        <button
          onClick={() => setActiveIndex(Math.min(scaffoldings.length - 1, activeIndex + 1))}
          disabled={activeIndex === scaffoldings.length - 1}
          className="btn btn-secondary"
          style={{ padding: '5px 10px', fontSize: '12px' }}
        >
          다음
        </button>
      </div>
      
      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
        <h3 style={{ marginBottom: '15px' }}>{currentScaffolding.title}</h3>
        
        <div style={{ 
          padding: '15px', 
          backgroundColor: '#f0f0f0', 
          borderRadius: '5px', 
          marginBottom: '20px',
          whiteSpace: 'pre-wrap'
        }}>
          {currentScaffolding.prompt_text}
        </div>
        
        <div className="form-group">
          <label className="form-label">답변</label>
          <textarea
            className="form-textarea"
            value={responses[currentScaffolding.id] || ''}
            onChange={(e) => setResponses({
              ...responses,
              [currentScaffolding.id]: e.target.value
            })}
            placeholder="여기에 답변을 작성하세요..."
            style={{ minHeight: '200px' }}
          />
        </div>
        
        <button
          onClick={() => handleSave(currentScaffolding.id)}
          className="btn btn-primary"
          disabled={saving}
          style={{ width: '100%' }}
        >
          {saving ? '저장 중...' : '저장'}
        </button>
        
        {message && (
          <div style={{
            marginTop: '10px',
            padding: '10px',
            borderRadius: '5px',
            backgroundColor: message.includes('실패') ? '#ffebee' : '#e8f5e9',
            color: message.includes('실패') ? '#c62828' : '#2e7d32',
            textAlign: 'center'
          }}>
            {message}
          </div>
        )}
      </div>
    </div>
  )
}

export default ScaffoldingInterface

