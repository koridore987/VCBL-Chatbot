/**
 * 유틸리티 함수
 */
import DOMPurify from 'dompurify'

/**
 * 입력 값 검증
 */
export const validation = {
  /**
   * 이메일 형식 검증
   */
  isValidEmail: (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return re.test(email)
  },

  /**
   * 학번 형식 검증 (영문자, 숫자, 하이픈만 허용)
   */
  isValidStudentId: (studentId) => {
    const re = /^[a-zA-Z0-9-]+$/
    return re.test(studentId)
  },

  /**
   * 비밀번호 강도 검증
   */
  isStrongPassword: (password) => {
    if (password.length < 8) return false
    if (!/[a-zA-Z]/.test(password)) return false
    if (!/[0-9]/.test(password)) return false
    return true
  },

  /**
   * 문자열 길이 검증
   */
  isValidLength: (str, min, max) => {
    const length = str.trim().length
    return length >= min && length <= max
  },

  /**
   * 필수 필드 검증
   */
  isRequired: (value) => {
    if (value === null || value === undefined) return false
    if (typeof value === 'string') return value.trim().length > 0
    return true
  },
}

/**
 * 포맷팅 함수
 */
export const formatters = {
  /**
   * 날짜 포맷팅
   */
  formatDate: (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  },

  /**
   * 상대 시간 포맷팅 (예: "3분 전")
   */
  formatRelativeTime: (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    const now = new Date()
    const diff = now - date

    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}일 전`
    if (hours > 0) return `${hours}시간 전`
    if (minutes > 0) return `${minutes}분 전`
    return '방금 전'
  },

  /**
   * 숫자 포맷팅 (천 단위 구분)
   */
  formatNumber: (num) => {
    if (num === null || num === undefined) return '0'
    return num.toLocaleString('ko-KR')
  },

  /**
   * 비용 포맷팅
   */
  formatCost: (cost) => {
    if (cost === null || cost === undefined) return '$0.0000'
    return `$${cost.toFixed(4)}`
  },

  /**
   * 파일 크기 포맷팅
   */
  formatFileSize: (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  },

  /**
   * 초를 분:초 형식으로 변환
   */
  formatDuration: (seconds) => {
    if (!seconds) return '0:00'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  },
}

/**
 * 보안 관련 유틸리티
 */
export const security = {
  /**
   * HTML sanitize (XSS 방어)
   */
  sanitizeHTML: (html) => {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
      ALLOWED_ATTR: ['href', 'target'],
    })
  },

  /**
   * 텍스트에서 HTML 태그 제거
   */
  stripHTML: (html) => {
    const div = document.createElement('div')
    div.innerHTML = html
    return div.textContent || div.innerText || ''
  },
}

/**
 * 문자열 유틸리티
 */
export const strings = {
  /**
   * 문자열 truncate
   */
  truncate: (str, maxLength) => {
    if (!str) return ''
    if (str.length <= maxLength) return str
    return str.slice(0, maxLength) + '...'
  },

  /**
   * 첫 글자 대문자화
   */
  capitalize: (str) => {
    if (!str) return ''
    return str.charAt(0).toUpperCase() + str.slice(1)
  },

  /**
   * URL에서 파라미터 추출
   */
  getQueryParam: (url, param) => {
    const urlObj = new URL(url)
    return urlObj.searchParams.get(param)
  },
}

/**
 * 디바운스 함수
 */
export const debounce = (func, delay) => {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

/**
 * 스로틀 함수
 */
export const throttle = (func, limit) => {
  let inThrottle
  return (...args) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * 로컬 스토리지 유틸리티
 */
export const storage = {
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error('Failed to save to localStorage:', error)
    }
  },

  get: (key) => {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : null
    } catch (error) {
      console.error('Failed to get from localStorage:', error)
      return null
    }
  },

  remove: (key) => {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error('Failed to remove from localStorage:', error)
    }
  },

  clear: () => {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('Failed to clear localStorage:', error)
    }
  },
}

/**
 * 에러 처리 유틸리티
 */
export const errorHandler = {
  /**
   * API 에러 메시지 추출
   */
  getErrorMessage: (error) => {
    if (error.response) {
      // 서버 응답이 있는 경우
      return error.response.data?.error || error.response.data?.message || '오류가 발생했습니다'
    } else if (error.request) {
      // 요청은 보냈지만 응답이 없는 경우
      return '서버와 연결할 수 없습니다. 네트워크를 확인해주세요.'
    } else {
      // 요청 설정 중 오류
      return error.message || '알 수 없는 오류가 발생했습니다'
    }
  },

  /**
   * 상태 코드별 처리
   */
  handleStatusCode: (status) => {
    switch (status) {
      case 400:
        return '잘못된 요청입니다'
      case 401:
        return '인증이 필요합니다'
      case 403:
        return '접근 권한이 없습니다'
      case 404:
        return '요청한 리소스를 찾을 수 없습니다'
      case 429:
        return '요청 횟수 제한을 초과했습니다'
      case 500:
        return '서버 오류가 발생했습니다'
      default:
        return '오류가 발생했습니다'
    }
  },
}

