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
  HiSparkles
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
                className="flex items-center space-x-2 group transition-all duration-300"
              >
                <div className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-accent-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-300"></div>
                  <div className="relative p-2 bg-gradient-to-br from-primary-600 to-primary-500 rounded-lg">
                    <HiVideoCamera className="text-xl text-white" />
                  </div>
                </div>
                <div>
                  <span className="font-bold text-lg bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent hidden sm:block">
                    VCBL 학습 플랫폼
                  </span>
                  <span className="font-bold text-lg bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent sm:hidden">
                    VCBL
                  </span>
                </div>
              </Link>
              
              {/* Desktop Menu */}
              <div className="hidden md:flex items-center space-x-1">
                <Link 
                  to="/" 
                  className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200 ${
                    isActiveLink('/') 
                      ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                      : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                  }`}
                >
                  <HiHome className="text-lg" />
                  <span className="font-medium">학습하기</span>
                </Link>
                    
                {isAdmin() && (
                  <>
                    <Link 
                      to="/admin" 
                      className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200 ${
                        isActiveLink('/admin') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiChartBar className="text-lg" />
                      <span className="font-medium">대시보드</span>
                    </Link>
                    <Link 
                      to="/admin/students" 
                      className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200 ${
                        isActiveLink('/admin/students') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiUsers className="text-lg" />
                      <span className="font-medium">학생 관리</span>
                    </Link>
                    <Link 
                      to="/admin/content" 
                      className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200 ${
                        isActiveLink('/admin/content') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiVideoCamera className="text-lg" />
                      <span className="font-medium">콘텐츠 관리</span>
                    </Link>
                    <Link 
                      to="/admin/logs" 
                      className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-200 ${
                        isActiveLink('/admin/logs') 
                          ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                          : 'text-gray-700 hover:bg-primary-50 hover:text-primary-700'
                      }`}
                    >
                      <HiCog className="text-lg" />
                      <span className="font-medium">활동 로그</span>
                    </Link>
                  </>
                )}
                
                {/* User Info with Avatar */}
                <div className="ml-4 flex items-center space-x-3 px-4 py-2 bg-gradient-to-r from-primary-50 to-accent-50 rounded-xl border border-primary-100">
                  {/* Avatar with initials */}
                  <div className="relative">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-600 to-accent-600 flex items-center justify-center">
                      <span className="text-xs font-bold text-white">
                        {getUserInitials()}
                      </span>
                    </div>
                    {isAdmin() && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent-500 rounded-full border-2 border-white" title="관리자">
                        <HiSparkles className="text-[8px] text-white" />
                      </div>
                    )}
                  </div>
                  <div className="text-left">
                    <div className="text-sm font-semibold text-gray-800 leading-tight">
                      {user.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {user.student_id}
                    </div>
                  </div>
                </div>
                
                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-red-50 text-red-600 hover:bg-red-100 hover:shadow-md transition-all duration-200 ml-2"
                >
                  <HiLogout className="text-lg" />
                  <span className="font-medium">로그아웃</span>
                </button>
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-xl text-gray-700 hover:bg-primary-50 transition-all duration-200"
              >
                {mobileMenuOpen ? <HiX className="text-2xl" /> : <HiMenuAlt3 className="text-2xl" />}
              </button>
            </div>

            {/* Mobile Menu with smooth transition */}
            {mobileMenuOpen && (
              <div className="md:hidden pb-4">
                <div className="pt-4 border-t border-gray-200 space-y-2 animate-slide-down">
                  <Link 
                    to="/" 
                    className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                      isActiveLink('/') 
                        ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                        : 'text-gray-700 hover:bg-primary-50'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <HiHome className="text-xl" />
                    <span className="font-medium">학습하기</span>
                  </Link>
                  
                  {isAdmin() && (
                    <>
                      <Link 
                        to="/admin" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                          isActiveLink('/admin') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiChartBar className="text-xl" />
                        <span className="font-medium">대시보드</span>
                      </Link>
                      <Link 
                        to="/admin/students" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                          isActiveLink('/admin/students') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiUsers className="text-xl" />
                        <span className="font-medium">학생 관리</span>
                      </Link>
                      <Link 
                        to="/admin/content" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                          isActiveLink('/admin/content') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiVideoCamera className="text-xl" />
                        <span className="font-medium">콘텐츠 관리</span>
                      </Link>
                      <Link 
                        to="/admin/logs" 
                        className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
                          isActiveLink('/admin/logs') 
                            ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md' 
                            : 'text-gray-700 hover:bg-primary-50'
                        }`}
                        onClick={() => setMobileMenuOpen(false)}
                      >
                        <HiCog className="text-xl" />
                        <span className="font-medium">활동 로그</span>
                      </Link>
                    </>
                  )}
                  
                  {/* Mobile User Info */}
                  <div className="px-4 py-3 bg-gradient-to-r from-primary-50 to-accent-50 rounded-xl border border-primary-100 flex items-center space-x-3 mt-4">
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
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-gray-800">
                        {user.name}
                      </div>
                      <div className="text-xs text-gray-500">
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
                    className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-xl bg-red-50 text-red-600 hover:bg-red-100 transition-all"
                  >
                    <HiLogout className="text-xl" />
                    <span className="font-medium">로그아웃</span>
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
