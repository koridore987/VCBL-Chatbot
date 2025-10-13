import { createContext, useState, useContext, useEffect } from 'react'
import api from '../services/api'

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
    const token = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (token && savedUser) {
      setUser(JSON.parse(savedUser))
      fetchCurrentUser()
    } else {
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me')
      setUser(response.data)
      localStorage.setItem('user', JSON.stringify(response.data))
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
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))
      setUser(user)
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || '로그인에 실패했습니다'
      }
    }
  }

  const register = async (studentId, password, name) => {
    try {
      await api.post('/auth/register', {
        student_id: studentId,
        password,
        name
      })
      
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || '회원가입에 실패했습니다'
      }
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
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

