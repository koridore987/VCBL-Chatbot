import { useState, useEffect, useMemo } from 'react'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { API_ENDPOINTS } from '../constants'
import { formatters } from '../utils'
import { HiBookmark, HiExclamationCircle } from 'react-icons/hi'
import VideoCard from '../components/VideoCard'
import HeroSection from '../components/HeroSection'
import FilterBar from '../components/FilterBar'

const ModuleList = () => {
  const [modules, setModules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
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

  // Filter and search modules
  const filteredModules = useMemo(() => {
    if (!searchTerm) return modules

    return modules.filter(module =>
      module.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (module.description && module.description.toLowerCase().includes(searchTerm.toLowerCase()))
    )
  }, [modules, searchTerm])

  // Calculate completion statistics
  const stats = useMemo(() => {
    const total = modules.length
    const completed = modules.filter(module => 
      module.learning_progress?.status === 'completed'
    ).length
    const inProgress = modules.filter(module => 
      module.learning_progress?.status === 'in_progress'
    ).length

    return { total, completed, inProgress }
  }, [modules])

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
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">학습 가능한 영상</h2>
            <p className="text-sm text-gray-600">필터를 사용해 원하는 모듈을 바로 찾아보세요.</p>
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredModules.map((module) => (
              <VideoCard
                key={module.id}
                video={module}
                to={`/modules/${module.id}`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ModuleList



