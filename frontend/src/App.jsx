import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Register from './pages/Register'
import Survey from './pages/Survey'
import VideoList from './pages/VideoList'
import LearningInterface from './pages/LearningInterface'
import AdminDashboard from './pages/AdminDashboard'
import AdminUsers from './pages/AdminUsers'
import AdminVideos from './pages/AdminVideos'
import AdminPersonas from './pages/AdminPersonas'
import AdminLogs from './pages/AdminLogs'
import AdminSurveys from './pages/AdminSurveys'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Navbar />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            <Route path="/survey" element={<ProtectedRoute><Survey /></ProtectedRoute>} />
            <Route path="/" element={<ProtectedRoute><VideoList /></ProtectedRoute>} />
            <Route path="/videos/:videoId" element={<ProtectedRoute><LearningInterface /></ProtectedRoute>} />
            
            <Route path="/admin" element={<ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>} />
            <Route path="/admin/students" element={<ProtectedRoute adminOnly><AdminUsers /></ProtectedRoute>} />
            <Route path="/admin/content" element={<ProtectedRoute adminOnly><AdminVideos /></ProtectedRoute>} />
            <Route path="/admin/personas" element={<ProtectedRoute adminOnly><AdminPersonas /></ProtectedRoute>} />
            <Route path="/admin/surveys" element={<ProtectedRoute adminOnly><AdminSurveys /></ProtectedRoute>} />
            <Route path="/admin/logs" element={<ProtectedRoute adminOnly><AdminLogs /></ProtectedRoute>} />
            
            {/* 하위 호환성을 위한 리다이렉트 */}
            <Route path="/admin/users" element={<Navigate to="/admin/students" replace />} />
            <Route path="/admin/videos" element={<Navigate to="/admin/content" replace />} />
            <Route path="/admin/prompts" element={<Navigate to="/admin/personas" replace />} />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App

