import { createContext, useState, useContext, useEffect } from 'react'
import api from '../services/api'
import { storage } from '../utils'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // storage helper를 사용하여 토큰과 사용자 정보 로드
    const token = storage.get('token')
    const savedUser = storage.get('user')
    
    if (token && savedUser) {
      setUser(savedUser)
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
      storage.set('user', response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (studentId, password) => {
    try {
      const response = await api.post('/auth/login', {
        student_id: studentId,
        password
      })
      
      const { access_token, user } = response.data
      
      // storage helper를 사용하여 토큰과 사용자 정보 저장
      storage.set('token', access_token)
      storage.set('user', user)
      
      // 토큰 저장 후 충분히 대기한 뒤 상태 업데이트 (동기화 보장)
      await new Promise(resolve => setTimeout(resolve, 100))
      setUser(user)
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || '로그인에 실패했습니다'
      }
    }
  }

  const register = async (studentId, password) => {
    try {
      await api.post('/auth/register', {
        student_id: studentId,
        password
      })
      
      // 회원가입 후 자동 로그인
      const loginResult = await login(studentId, password)
      
      return { success: true, autoLoggedIn: loginResult.success }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || '회원가입에 실패했습니다'
      }
    }
  }

  const logout = () => {
    storage.remove('token')
    storage.remove('user')
    setUser(null)
  }

  const isAdmin = () => {
    return user && (user.role === 'admin' || user.role === 'super')
  }

  const isSuperAdmin = () => {
    return user && user.role === 'super'
  }

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      isAdmin,
      isSuperAdmin
    }}>
      {children}
    </AuthContext.Provider>
  )
}

