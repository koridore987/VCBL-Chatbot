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
      <HeroSection />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <HiBookmark className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">전체 모듈</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <HiBookmark className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">완료된 모듈</p>
                <p className="text-2xl font-bold text-gray-900">{stats.completed}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <HiBookmark className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">진행 중인 모듈</p>
                <p className="text-2xl font-bold text-gray-900">{stats.inProgress}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filter Bar */}
        <FilterBar
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          placeholder="모듈 검색..."
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




