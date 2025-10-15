import { useState, useEffect, useMemo } from 'react'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { API_ENDPOINTS } from '../constants'
import { formatters } from '../utils'
import { HiBookmark, HiExclamationCircle } from 'react-icons/hi'
import VideoCard from '../components/VideoCard'
import HeroSection from '../components/HeroSection'
import FilterBar from '../components/FilterBar'

const VideoList = () => {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const { user } = useAuth()

  useEffect(() => {
    // 로그인 사용자 정보가 준비된 뒤에만 목록 호출
    if (user) {
      fetchVideos()
    }
  }, [user])

  const fetchVideos = async () => {
    try {
      const response = await api.get(API_ENDPOINTS.VIDEOS.LIST)
      // 백엔드는 { data: [...] } 형태로 반환
      const videoData = response.data.data || []
      setVideos(videoData)
    } catch (err) {
      console.error('Failed to fetch videos:', err)
      setError('비디오 목록을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  // Filter and search videos
  const filteredVideos = useMemo(() => {
    const statusRank = {
      in_progress: 0,
      not_started: 1,
      completed: 2
    }

    const filtered = videos.filter(video => {
      // Search filter
      const matchesSearch = video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          (video.description && video.description.toLowerCase().includes(searchTerm.toLowerCase()))
      
      return matchesSearch
    })
    
    return filtered.slice().sort((a, b) => {
      const statusA = a.learning_progress?.status || 'not_started'
      const statusB = b.learning_progress?.status || 'not_started'
      if (statusRank[statusA] !== statusRank[statusB]) {
        return (statusRank[statusA] ?? 1) - (statusRank[statusB] ?? 1)
      }
      const orderA = a.order_index ?? 0
      const orderB = b.order_index ?? 0
      return orderA - orderB
    })
  }, [videos, searchTerm])

  const progressOverview = useMemo(() => {
    if (!videos.length) return null

    const counts = {
      completed: 0,
      in_progress: 0,
      not_started: 0
    }
    let latestTimestamp = null
    let latestVideoTitle = ''

    videos.forEach((video) => {
      const status = video.learning_progress?.status || 'not_started'
      if (counts[status] === undefined) {
        counts[status] = 0
      }
      counts[status] += 1

      const activityTimestamp = video.learning_progress?.completed_at
        || video.learning_progress?.last_activity_at
        || video.learning_progress?.started_at

      if (activityTimestamp) {
        const activityDate = new Date(activityTimestamp)
        if (!latestTimestamp || activityDate > new Date(latestTimestamp)) {
          latestTimestamp = activityTimestamp
          latestVideoTitle = video.title
        }
      }
    })

    const totalTracked = Object.values(counts).reduce((sum, value) => sum + value, 0)

    return {
      counts,
      latestTimestamp,
      latestVideoTitle,
      totalTracked
    }
  }, [videos])

  // Stats는 더 이상 필요하지 않음
  const stats = null

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-gray-600 font-medium">비디오를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <HeroSection stats={stats} />
        
        {progressOverview && (
          <div className="glass-card mb-8 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-800">나의 학습 현황</h2>
              <span className="text-xs text-gray-500">
                총 학습 중 콘텐츠: {progressOverview.totalTracked}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-xl bg-emerald-50 px-4 py-3">
                <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">완료</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">
                  {progressOverview.counts.completed}
                </p>
              </div>
              <div className="rounded-xl bg-blue-50 px-4 py-3">
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">진행 중</p>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {progressOverview.counts.in_progress}
                </p>
              </div>
              <div className="rounded-xl bg-gray-50 px-4 py-3">
                <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">미시작</p>
                <p className="text-2xl font-bold text-gray-700 mt-1">
                  {progressOverview.counts.not_started}
                </p>
              </div>
            </div>
            {progressOverview.latestTimestamp && (
              <p className="text-xs text-gray-500 mt-4">
                최근 학습: <span className="font-medium text-gray-700">{progressOverview.latestVideoTitle}</span>
                {' · '}
                {formatters.formatRelativeTime(progressOverview.latestTimestamp)}
              </p>
            )}
          </div>
        )}
        
        {/* Error Alert */}
        {error && (
          <div className="alert alert-error mb-6">
            <HiExclamationCircle className="text-2xl flex-shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
        )}
        
        {videos.length > 0 && (
          <>
            {/* Search and Filter */}
            <FilterBar 
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
            />
            
            {/* Video Grid */}
            <div id="video-list">
              {filteredVideos.length === 0 ? (
                <div className="glass-card p-12 text-center">
                  <HiBookmark className="mx-auto text-6xl text-gray-300 mb-4" />
                  <p className="text-gray-600 text-lg font-medium">
                    검색 조건에 맞는 비디오가 없습니다
                  </p>
                  <button
                    onClick={() => {
                      setSearchTerm('')
                    }}
                    className="mt-4 btn btn-secondary"
                  >
                    필터 초기화
                  </button>
                </div>
              ) : (
                <>
                  {/* Results count */}
                  <div className="mb-4 text-sm text-gray-600">
                    <span className="font-semibold text-gray-800">{filteredVideos.length}</span>개의 비디오
                  </div>
                  
                  {/* Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
                    {filteredVideos.map((video) => (
                      <VideoCard key={video.id} video={video} />
                    ))}
                  </div>
                </>
              )}
            </div>
          </>
        )}
        
        {/* Empty state when no videos at all */}
        {videos.length === 0 && !error && (
          <div className="glass-card p-12 text-center">
            <HiBookmark className="mx-auto text-6xl text-gray-300 mb-4" />
            <p className="text-gray-600 text-lg font-medium mb-2">
              아직 등록된 비디오가 없습니다
            </p>
            <p className="text-gray-500 text-sm">
              관리자가 학습 비디오를 추가하면 여기에 표시됩니다
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default VideoList
