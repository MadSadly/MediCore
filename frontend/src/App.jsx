import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import axios from 'axios'
import LoginPage from './pages/LoginPage'
import MainPage from './pages/MainPage'
import PatientDetailPage from './pages/PatientDetailPage'
import MainLayout from './components/MainLayout'
import PatientLayout from './components/PatientLayout'

import BrainTumorPage    from './WJ/BrainTumorPage'
import SpineDiskPage     from './DH/SpineDiskPage'
import ColonCancerPage   from './GW/ColonCancerPage'
import KidneyFailurePage from './NJ/KidneyFailurePage'
import SkinDiseasePage   from './MS/SkinDiseasePage'
import EyeDiseasePage    from './SH/EyeDiseasePage'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

const INACTIVITY_LIMIT = 30 * 60 * 1000  // 30분 비활동 시 자동 로그아웃

export default function App() {
  const lastActivityRef = useRef(Date.now())

  // 사용자 활동 감지 — 마우스·키보드·클릭·스크롤 시 타이머 리셋
  useEffect(() => {
    const onActivity = () => { lastActivityRef.current = Date.now() }
    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
    events.forEach(e => window.addEventListener(e, onActivity, { passive: true }))
    return () => events.forEach(e => window.removeEventListener(e, onActivity))
  }, [])

  useEffect(() => {
    const checkToken = () => {
      const token = localStorage.getItem('token')
      if (!token) return

      // 30분 비활동 자동 로그아웃
      if (Date.now() - lastActivityRef.current > INACTIVITY_LIMIT) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return
      }

      try {
        const { exp } = JSON.parse(atob(token.split('.')[1]))
        if (exp * 1000 < Date.now()) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
      } catch { void 0 }
    }

    checkToken()
    const timer = setInterval(checkToken, 30000)

    const interceptor = axios.interceptors.response.use(
      res => res,
      err => {
        if (err.response?.status === 401) {
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
        return Promise.reject(err)
      }
    )

    return () => {
      clearInterval(timer)
      axios.interceptors.response.eject(interceptor)
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route path="/dashboard" element={<PrivateRoute><MainLayout /></PrivateRoute>}>
          <Route index element={<MainPage />} />
        </Route>

        <Route path="/patients/:id" element={<PrivateRoute><PatientLayout /></PrivateRoute>}>
          <Route index element={<PatientDetailPage />} />
          <Route path="brain-tumor"    element={<BrainTumorPage />} />
          <Route path="spine-disk"     element={<SpineDiskPage />} />
          <Route path="colon-cancer"   element={<ColonCancerPage />} />
          <Route path="kidney-failure" element={<KidneyFailurePage />} />
          <Route path="skin-disease"   element={<SkinDiseasePage />} />
          <Route path="eye-disease"    element={<EyeDiseasePage />} />
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}