import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './index.css'
import App from './App.jsx'

// 401 응답 시 토큰 제거 후 로그인 페이지로 이동
// - 토큰 만료, 위변조 모두 여기서 처리됨
axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const isAuthEndpoint = err.config?.url?.includes('/api/auth/')
      if (!isAuthEndpoint) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.replace('/login')
      }
    }
    return Promise.reject(err)
  }
)

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)