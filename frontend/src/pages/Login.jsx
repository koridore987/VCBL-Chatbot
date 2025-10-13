import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { HiVideoCamera, HiLockClosed, HiUser, HiArrowRight, HiSparkles } from 'react-icons/hi'

const Login = () => {
  const [studentId, setStudentId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { user, login } = useAuth()
  const navigate = useNavigate()

  // 이미 로그인된 사용자는 메인 페이지로 리다이렉트
  useEffect(() => {
    if (user) {
      navigate('/', { replace: true })
    }
  }, [user, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // 학번을 정수로 변환
    const studentIdNum = parseInt(studentId)
    if (isNaN(studentIdNum)) {
      setError('올바른 학번을 입력하세요')
      return
    }

    setLoading(true)

    const result = await login(studentIdNum, password)
    
    if (result.success) {
      navigate('/')
    } else {
      setError(result.error)
    }
    
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 p-4 relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-20 -left-20 w-96 h-96 bg-gradient-to-br from-primary-400/20 to-accent-400/20 rounded-full blur-3xl animate-blob" />
      <div className="absolute bottom-20 -right-20 w-96 h-96 bg-gradient-to-tr from-secondary-400/20 to-primary-400/20 rounded-full blur-3xl animate-blob" style={{ animationDelay: '2s' }} />
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo Section */}
        <div className="text-center mb-8">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", delay: 0.2 }}
            className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-primary-600 to-primary-500 rounded-2xl mb-4 shadow-xl relative"
          >
            <HiVideoCamera className="text-4xl text-white" />
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-accent-500 rounded-full flex items-center justify-center">
              <HiSparkles className="text-white text-xs" />
            </div>
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-4xl font-extrabold mb-2"
          >
            <span className="bg-gradient-to-r from-primary-600 to-primary-500 bg-clip-text text-transparent">
              VCBL
            </span>
            <span className="text-gray-800"> 학습 플랫폼</span>
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-gray-600"
          >
            영상 기반 인터랙티브 학습
          </motion.p>
        </div>
        
        {/* Login Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass-card p-8 shadow-glass-lg"
        >
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">로그인</h2>
          
          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="alert alert-error mb-6"
            >
              <p className="text-sm font-medium">{error}</p>
            </motion.div>
          )}
          
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Student ID Field */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                학번 (10자리)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <HiUser className="text-gray-400 text-lg" />
                </div>
                <input
                  type="text"
                  className="form-input pl-11"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  placeholder="10자리 학번을 입력하세요"
                  maxLength="10"
                  required
                />
              </div>
            </div>
            
            {/* Password Field */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                비밀번호
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <HiLockClosed className="text-gray-400 text-lg" />
                </div>
                <input
                  type="password"
                  className="form-input pl-11"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  required
                />
              </div>
            </div>
            
            {/* Submit Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              className={`btn w-full flex items-center justify-center space-x-2 py-3 ${
                loading ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'btn-primary'
              }`}
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="spinner !w-5 !h-5 !border-2"></div>
                  <span>로그인 중...</span>
                </>
              ) : (
                <>
                  <span>로그인</span>
                  <HiArrowRight className="text-xl" />
                </>
              )}
            </motion.button>
          </form>
          
          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              계정이 없으신가요?{' '}
              <Link to="/register" className="text-primary-600 hover:text-primary-700 font-bold hover:underline">
                회원가입
              </Link>
            </p>
          </div>
        </motion.div>
        
        {/* Footer */}
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center text-gray-500 text-sm mt-6"
        >
          © 2024 VCBL 학습 플랫폼. All rights reserved.
        </motion.p>
      </motion.div>
    </div>
  )
}

export default Login
