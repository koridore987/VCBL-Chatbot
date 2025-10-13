import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Register from './pages/Register'
import VideoList from './pages/VideoList'
import LearningInterface from './pages/LearningInterface'
import AdminDashboard from './pages/AdminDashboard'
import AdminUsers from './pages/AdminUsers'
import AdminVideos from './pages/AdminVideos'
import AdminPrompts from './pages/AdminPrompts'
import AdminLogs from './pages/AdminLogs'
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
            
            <Route path="/" element={<ProtectedRoute><VideoList /></ProtectedRoute>} />
            <Route path="/videos/:videoId" element={<ProtectedRoute><LearningInterface /></ProtectedRoute>} />
            
            <Route path="/admin" element={<ProtectedRoute adminOnly><AdminDashboard /></ProtectedRoute>} />
            <Route path="/admin/users" element={<ProtectedRoute adminOnly><AdminUsers /></ProtectedRoute>} />
            <Route path="/admin/videos" element={<ProtectedRoute adminOnly><AdminVideos /></ProtectedRoute>} />
            <Route path="/admin/prompts" element={<ProtectedRoute adminOnly><AdminPrompts /></ProtectedRoute>} />
            <Route path="/admin/logs" element={<ProtectedRoute adminOnly><AdminLogs /></ProtectedRoute>} />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App

