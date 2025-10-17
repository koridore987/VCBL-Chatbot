import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { API_ENDPOINTS } from '../constants'
import { formatters } from '../utils'
import { HiBookmark, HiExclamationCircle, HiPlay, HiClock } from 'react-icons/hi'
import VideoCard from '../components/VideoCard'
import HeroSection from '../components/HeroSection'
import FilterBar from '../components/FilterBar'

const ModuleList = () => {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState('all')
  const { user } = useAuth()

  const scrollToVideos = () => {
    if (typeof window === 'undefined') return
    const target = document.getElementById('video-list')
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  useEffect(() => {
    // 로그인 사용자 정보가 준비된 뒤에만 목록 호출
    if (user) {
      fetchModules()
    }
  }, [user])

  const fetchModules = async () => {
    try {
      const response = await api.get(API_ENDPOINTS.MODULES.LIST)
      // 백엔드는 { data: [...] } 형태로 반환
      const moduleData = response.data.data || []
      setModules(moduleData)
    } catch (err) {
      console.error('Failed to fetch modules:', err)
      setError('모듈 목록을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  // Calculate completion statistics
  const stats = useMemo(() => {
    const total = modules.length
    const completed = modules.filter(module =>
      module.learning_progress?.status === 'completed'
    ).length
    const inProgress = modules.filter(module =>
      module.learning_progress?.status === 'in_progress'
    ).length
    const notStarted = total - completed - inProgress

    return { total, completed, inProgress, notStarted }
  }, [modules])

  // Filtered lists (tab + search)
  const segmentedModules = useMemo(() => {
    if (activeTab === 'all') return modules
    return modules.filter((module) => {
      const status = module.learning_progress?.status || 'not_started'
      if (activeTab === 'in_progress') return status === 'in_progress'
      if (activeTab === 'completed') return status === 'completed'
      if (activeTab === 'not_started') return status === 'not_started'
      return true
    })
  }, [modules, activeTab])

  const filteredModules = useMemo(() => {
    if (!searchTerm) return segmentedModules
    const keyword = searchTerm.toLowerCase()
    return segmentedModules.filter(module =>
      module.title.toLowerCase().includes(keyword) ||
      (module.description && module.description.toLowerCase().includes(keyword))
    )
  }, [segmentedModules, searchTerm])

  const continueModule = useMemo(() => {
    if (modules.length === 0) return null
    const candidates = modules.filter(module =>
      module.learning_progress?.status !== 'completed'
    )
    if (candidates.length === 0) return null

    const lastActivity = (module) => {
      const progress = module.learning_progress || {}
      return progress.last_activity_at || progress.started_at || null
    }

    const sorted = candidates
      .map(module => ({ module, at: lastActivity(module) }))
      .filter(item => !!item.at)
      .sort((a, b) => new Date(b.at) - new Date(a.at))

    if (sorted.length > 0) return sorted[0].module

    return candidates.find(module => module.learning_progress?.status === 'in_progress') || candidates[0]
  }, [modules])

  const continueProgress = continueModule?.learning_progress || null
  const continueLastActivity = continueProgress
    ? (continueProgress.last_activity_at || continueProgress.started_at)
    : null

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">모듈 목록을 불러오는 중...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <HiExclamationCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchModules}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <HeroSection stats={stats} onExploreClick={scrollToVideos} />
      
      <div id="video-list" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {continueModule && (
          <Link
            to={`/modules/${continueModule.id}`}
            className="group mb-6 block rounded-3xl bg-white shadow-lg shadow-primary-100/40 ring-1 ring-primary-100 transition hover:-translate-y-1 hover:shadow-xl"
          >
            <div className="grid grid-cols-1 md:grid-cols-[1.1fr_1.3fr] lg:grid-cols-[1fr_1.2fr]">
              <div className="relative h-48 overflow-hidden rounded-t-3xl md:h-full md:rounded-l-3xl md:rounded-tr-none">
                {continueModule.thumbnail_url ? (
                  <img
                    src={continueModule.thumbnail_url}
                    alt={continueModule.title}
                    className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-primary-500 to-accent-500 text-white/90">
                    <HiPlay className="text-5xl" />
                    <p className="mt-2 text-sm font-semibold">썸네일 준비 중</p>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-r from-black/45 via-black/20 to-transparent" />
                <div className="absolute bottom-4 left-4 inline-flex items-center gap-2 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-gray-800 shadow">
                  <HiClock className="text-base text-primary-600" />
                  최근에 보던 모듈 이어서 학습
                </div>
              </div>
              <div className="flex flex-col justify-between gap-4 px-6 py-6">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-primary-600">Continue learning</p>
                  <h2 className="mt-2 text-xl font-bold text-gray-900 line-clamp-2">
                    {continueModule.title}
                  </h2>
                  {continueModule.description && (
                    <p className="mt-3 text-sm text-gray-600 line-clamp-2">
                      {continueModule.description}
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
                    진행 중 · {continueLastActivity ? formatters.formatRelativeTime(continueLastActivity) : '방금 시작'}
                  </span>
                  <span className="inline-flex items-center gap-2 text-sm text-gray-500">
                    <HiPlay className="text-primary-500" />
                    클릭하면 바로 이어서 재생돼요
                  </span>
                </div>
              </div>
            </div>
          </Link>
        )}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">학습 가능한 영상</h2>
            <p className="text-sm text-gray-600">필터를 활용해 지금 필요한 모듈을 바로 찾아보세요.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {[
              { key: 'all', label: '전체', count: stats.total },
              { key: 'in_progress', label: '진행 중', count: stats.inProgress },
              { key: 'not_started', label: '미시작', count: Math.max(stats.notStarted, 0) },
              { key: 'completed', label: '완료', count: stats.completed },
            ].map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-1 rounded-full px-3.5 py-1.5 font-semibold ring-1 transition ${
                  activeTab === tab.key
                    ? 'bg-primary-600 text-white ring-primary-600'
                    : 'bg-white text-gray-700 ring-gray-200 hover:bg-gray-50'
                }`}
              >
                {tab.label}
                <span className={`ml-1 inline-flex h-5 min-w-[1.25rem] items-center justify-center rounded-full text-xs ${
                  activeTab === tab.key ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        <FilterBar
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
        />

        {/* Module Grid */}
        {filteredModules.length === 0 ? (
          <div className="text-center py-12">
            <HiBookmark className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">
              {searchTerm ? '검색 결과가 없습니다.' : '아직 등록된 모듈이 없습니다.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredModules.map((module) => (
              <VideoCard
                key={module.id}
                video={module}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ModuleList
