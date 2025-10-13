/**
 * 비디오 관련 커스텀 훅
 */
import { useState, useCallback } from 'react'
import api from '../services/api'
import { API_ENDPOINTS } from '../constants'

export const useVideo = () => {
  const [videos, setVideos] = useState([])
  const [currentVideo, setCurrentVideo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  /**
   * 모든 비디오 조회
   */
  const fetchVideos = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.get(API_ENDPOINTS.VIDEOS.LIST)
      // 백엔드는 { data: [...] } 형태로 반환
      const videoData = response.data.data || []
      setVideos(videoData)
      
      return videoData
    } catch (err) {
      const errorMessage = err.userMessage || err.response?.data?.error || '비디오 목록 조회 실패'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 특정 비디오 조회
   */
  const fetchVideo = useCallback(async (videoId) => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await api.get(API_ENDPOINTS.VIDEOS.DETAIL(videoId))
      // 백엔드는 success_response(video_data)로 반환 - dict는 merge되므로 직접 접근
      setCurrentVideo(response.data)
      
      return response.data
    } catch (err) {
      const errorMessage = err.userMessage || err.response?.data?.error || '비디오 정보 조회 실패'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  /**
   * 비디오 이벤트 로그
   */
  const logEvent = useCallback(async (videoId, eventType, eventData = {}) => {
    try {
      await api.post(API_ENDPOINTS.VIDEOS.EVENT(videoId), {
        event_type: eventType,
        event_data: eventData
      })
    } catch (err) {
      console.error('Failed to log event:', err)
      // 이벤트 로그 실패는 조용히 처리
    }
  }, [])

  return {
    videos,
    currentVideo,
    loading,
    error,
    fetchVideos,
    fetchVideo,
    logEvent,
    setError,
  }
}

export default useVideo

