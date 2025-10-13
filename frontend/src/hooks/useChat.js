/**
 * 채팅 관련 커스텀 훅
 */
import { useState, useCallback } from 'react'
import api from '../services/api'
import { API_ENDPOINTS } from '../constants'

export const useChat = () => {
  const [session, setSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)

  /**
   * 채팅 세션 생성 또는 가져오기
   */
  const createOrGetSession = useCallback(async (videoId) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.post(API_ENDPOINTS.CHAT.SESSIONS, {
        video_id: videoId
      })
      
      setSession(response.data)
      setMessages(response.data.messages || [])
      
      return response.data
    } catch (err) {
      const errorMessage = err.userMessage || err.response?.data?.error || '채팅 세션 생성 실패'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 메시지 전송
   */
  const sendMessage = useCallback(async (sessionId, message) => {
    try {
      setSending(true)
      setError(null)
      
      // 사용자 메시지를 즉시 UI에 추가
      const userMessage = { role: 'user', content: message }
      setMessages(prev => [...prev, userMessage])
      
      const response = await api.post(
        API_ENDPOINTS.CHAT.MESSAGES(sessionId),
        { message }
      )
      
      // AI 응답 추가
      setMessages(prev => [...prev, response.data.message])
      
      // 세션 정보 업데이트
      if (response.data.session) {
        setSession(prev => ({
          ...prev,
          ...response.data.session
        }))
      }
      
      return response.data
    } catch (err) {
      const errorMessage = err.userMessage || err.response?.data?.error || '메시지 전송 실패'
      setError(errorMessage)
      
      // 실패 시 사용자 메시지 제거
      setMessages(prev => prev.slice(0, -1))
      
      throw err
    } finally {
      setSending(false)
    }
  }, [])

  /**
   * 세션 초기화
   */
  const resetSession = useCallback(() => {
    setSession(null)
    setMessages([])
    setError(null)
  }, [])

  return {
    session,
    messages,
    loading,
    sending,
    error,
    createOrGetSession,
    sendMessage,
    resetSession,
    setError,
  }
}

export default useChat

