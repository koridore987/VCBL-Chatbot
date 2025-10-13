import { useState, useEffect, useRef } from 'react'
import api from '../services/api'

const ChatInterface = ({ videoId }) => {
  const [session, setSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    createOrGetSession()
  }, [videoId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const createOrGetSession = async () => {
    try {
      const response = await api.post('/chat/sessions', { video_id: videoId })
      setSession(response.data)
      setMessages(response.data.messages || [])
    } catch (err) {
      setError('채팅 세션을 생성하는데 실패했습니다')
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    
    if (!input.trim() || !session) return
    
    const userMessage = input.trim()
    setInput('')
    setLoading(true)
    setError('')
    
    // Add user message to UI immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    
    try {
      const response = await api.post(`/chat/sessions/${session.id}/messages`, {
        message: userMessage
      })
      
      // Add assistant message
      setMessages(prev => [...prev, response.data.message])
      
      // Update session info
      setSession(prev => ({
        ...prev,
        total_tokens: response.data.session.total_tokens,
        total_cost: response.data.session.total_cost
      }))
    } catch (err) {
      setError(err.response?.data?.error || '메시지 전송에 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Messages */}
      <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#666', marginTop: '40px' }}>
            <p>AI와 대화를 시작해보세요!</p>
            <p style={{ fontSize: '14px', marginTop: '10px' }}>
              학습 내용에 대해 질문하거나 토론할 수 있습니다.
            </p>
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: '15px',
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            <div
              style={{
                maxWidth: '80%',
                padding: '10px 15px',
                borderRadius: '10px',
                backgroundColor: msg.role === 'user' ? '#4CAF50' : '#e0e0e0',
                color: msg.role === 'user' ? 'white' : 'black',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}
        
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '15px' }}>
            <div style={{ padding: '10px 15px', borderRadius: '10px', backgroundColor: '#e0e0e0' }}>
              <div className="spinner" style={{ width: '20px', height: '20px', borderWidth: '3px' }}></div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Session Info */}
      {session && (
        <div style={{ padding: '10px 20px', borderTop: '1px solid #ddd', fontSize: '12px', color: '#666' }}>
          사용 토큰: {session.total_tokens} | 비용: ${session.total_cost?.toFixed(4) || '0.0000'}
        </div>
      )}
      
      {/* Error */}
      {error && (
        <div style={{ padding: '10px 20px', backgroundColor: '#ffebee', color: '#c62828', fontSize: '14px' }}>
          {error}
        </div>
      )}
      
      {/* Input */}
      <form onSubmit={sendMessage} style={{ padding: '20px', borderTop: '1px solid #ddd' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            className="form-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요..."
            disabled={loading}
            style={{ flex: 1 }}
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !input.trim()}
          >
            전송
          </button>
        </div>
      </form>
    </div>
  )
}

export default ChatInterface

