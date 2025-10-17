import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  HiHome, 
  HiCog, 
  HiUsers, 
  HiVideoCamera, 
  HiDocumentText, 
  HiChartBar, 
  HiLogout,
  HiUser,
  HiMenuAlt3,
  HiX,
  HiSparkles,
  HiChatAlt2
} from 'react-icons/hi'
import { useState } from 'react'

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Check if link is active
  const isActiveLink = (path) => {
    return location.pathname === path
  }

  // Generate user initials for avatar
  const getUserInitials = () => {
    if (!user || !user.name) return 'U'
    const names = user.name.split(' ')
    if (names.length >= 2) {
      return names[0][0] + names[1][0]
    }
    return user.name.substring(0, 2).toUpperCase()
  }

  // Don't render navbar on login/register pages
  if (!user) {
    return null
  }

  return (
    <nav className="sticky top-0 z-50 animate-slide-down">
      {/* Glass morphism navbar */}
      <div className="mx-4 mt-4 mb-2">
        <div className="glass-card shadow-glass-lg">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Logo/Brand */}
              <Link 
                to="/" 
                className="flex items-center space-x-2 group transition-all duration-300 flex-shrink-0"
              >
                <div className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-accent-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-300"></div>
                  <div className="relative p-2 bg-gradient-to-br from-primary-600 to-primary-500 rounded-lg">
                    <HiVideoCamera className="text-xl text-white" />
                  </div>
                </div>
                <div className="hidden sm:block">
                  <span className="font-bold text-lg bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent whitespace-nowrap">
                    VCBL 학습 플랫폼
                  </span>
                </div>
                <div className="sm:hidden">
                  <span className="font-bold text-lg bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent whitespace-nowrap">
                    VCBL
                  </span>
                </div>
              </Link>
              
              {/* Desktop Menu */}
              <div className="hidden lg:flex items-center space-x-1 flex-1 justify-center">
                <Link 
                  to="/" 
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                    isActiveLink('/') 
                      ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                      : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                  }`}
                >
                  <HiHome className="text-lg flex-shrink-0" />
                  <span className="font-medium text-sm">학습하기</span>
                </Link>
                    
                {isAdmin() && (
                  <>
                    <Link 
                      to="/admin" 
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                        isActiveLink('/admin') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiChartBar className="text-lg flex-shrink-0" />
                      <span className="font-medium text-sm">대시보드</span>
                    </Link>
                    <Link 
                      to="/admin/students" 
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                        isActiveLink('/admin/students') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiUsers className="text-lg flex-shrink-0" />
                      <span className="font-medium text-sm">학생 관리</span>
                    </Link>
                    <Link 
                      to="/admin/content" 
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                        isActiveLink('/admin/content') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiVideoCamera className="text-lg flex-shrink-0" />
                      <span className="font-medium text-sm">콘텐츠 관리</span>
                    </Link>
                    <Link 
                      to="/admin/personas" 
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                        isActiveLink('/admin/personas') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiChatAlt2 className="text-lg flex-shrink-0" />
                      <span className="font-medium text-sm">챗봇 관리</span>
                    </Link>
                    <Link 
                      to="/admin/logs" 
                      className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 whitespace-nowrap ${
                        isActiveLink('/admin/logs') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiCog className="text-lg flex-shrink-0" />
                      <span className="font-medium text-sm">활동 로그</span>
                    </Link>
                  </>
                )}
                
                {/* User Info with Avatar */}
                <div className="ml-4 flex items-center space-x-3 px-3 py-2 bg-gradient-to-r from-primary-50 to-accent-50 rounded-lg border border-primary-100 flex-shrink-0">
                  {/* Avatar with initials */}
                  <div className="relative">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-600 to-accent-600 flex items-center justify-center">
                      <span className="text-xs font-bold text-white">
                        {getUserInitials()}
                      </span>
                    </div>
                    {isAdmin() && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center" title="관리자">
                        <HiSparkles className="text-[8px] text-white" />
                      </div>
                    )}
                  </div>
                  <div className="text-left min-w-0">
                    <div className="text-sm font-semibold text-gray-800 leading-tight truncate">
                      {user.name}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {user.student_id}
                    </div>
                  </div>
                </div>
                
                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 hover:shadow-md transition-all duration-200 ml-2 flex-shrink-0"
                >
                  <HiLogout className="text-lg flex-shrink-0" />
                  <span className="font-medium text-sm whitespace-nowrap">로그아웃</span>
                </button>
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 rounded-lg text-gray-700 hover:bg-primary-50 transition-all duration-200 flex-shrink-0"
              >
                {mobileMenuOpen ? <HiX className="text-xl" /> : <HiMenuAlt3 className="text-xl" />}
              </button>
            </div>

            {/* Mobile Menu with smooth transition */}
            {mobileMenuOpen && (
              <div className="lg:hidden pb-4">
                <div className="pt-4 border-t border-gray-200 space-y-2 animate-slide-down">
                  <Link 
                    to="/" 
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                      isActiveLink('/') 
                        ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                        : 'text-gray-700 hover:bg-primary-50'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <HiHome className="text-lg flex-shrink-0" />
                    <span className="font-medium text-sm">학습하기</span>
                  </Link>
                  
                  {isAdmin() && (
                    <>
                      <Link 
                        to="/admin" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          isActiveLink('/admin') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiChartBar className="text-lg flex-shrink-0" />
                        <span className="font-medium text-sm">대시보드</span>
                      </Link>
                      <Link 
                        to="/admin/students" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          isActiveLink('/admin/students') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiUsers className="text-lg flex-shrink-0" />
                        <span className="font-medium text-sm">학생 관리</span>
                      </Link>
                      <Link 
                        to="/admin/content" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          isActiveLink('/admin/content') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiVideoCamera className="text-lg flex-shrink-0" />
                        <span className="font-medium text-sm">콘텐츠 관리</span>
                      </Link>
                      <Link 
                        to="/admin/personas" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          isActiveLink('/admin/personas') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiChatAlt2 className="text-lg flex-shrink-0" />
                        <span className="font-medium text-sm">챗봇 관리</span>
                      </Link>
                      <Link 
                        to="/admin/logs" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                          isActiveLink('/admin/logs') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiCog className="text-lg flex-shrink-0" />
                        <span className="font-medium text-sm">활동 로그</span>
                      </Link>
                    </>
                  )}
                  
                  {/* Mobile User Info */}
                  <div className="px-4 py-3 bg-gradient-to-r from-primary-50 to-accent-50 rounded-lg border border-primary-100 flex items-center space-x-3 mt-4">
                    <div className="relative">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-600 to-accent-600 flex items-center justify-center">
                        <span className="text-sm font-bold text-white">
                          {getUserInitials()}
                        </span>
                      </div>
                      {isAdmin() && (
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center" title="관리자">
                          <HiSparkles className="text-[10px] text-white" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-gray-800 truncate">
                        {user.name}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {user.student_id}
                      </div>
                    </div>
                  </div>
                  
                  {/* Mobile Logout */}
                  <button
                    onClick={() => {
                      setMobileMenuOpen(false)
                      handleLogout()
                    }}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-all"
                  >
                    <HiLogout className="text-lg flex-shrink-0" />
                    <span className="font-medium text-sm">로그아웃</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
