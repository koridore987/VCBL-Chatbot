import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const Navbar = () => {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          VCBL 학습 플랫폼
        </Link>
        
        {user && (
          <ul className="navbar-menu">
            <li>
              <Link to="/" className="navbar-link">학습하기</Link>
            </li>
            
            {isAdmin() && (
              <>
                <li>
                  <Link to="/admin" className="navbar-link">관리자</Link>
                </li>
                <li>
                  <Link to="/admin/prompts" className="navbar-link">프롬프트 관리</Link>
                </li>
              </>
            )}
            
            <li>
              <span className="navbar-link" style={{ cursor: 'default' }}>
                {user.name} ({user.student_id})
              </span>
            </li>
            
            <li>
              <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '5px 15px' }}>
                로그아웃
              </button>
            </li>
          </ul>
        )}
      </div>
    </nav>
  )
}

export default Navbar

