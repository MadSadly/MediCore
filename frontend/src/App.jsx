import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import MainPage from './pages/MainPage'
import PatientDetailPage from './pages/PatientDetailPage'
import Layout from './components/Layout'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

function ComingSoon({ title }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <p className="text-4xl mb-4">🚧</p>
        <h2 className="text-xl font-bold text-slate-300">{title}</h2>
        <p className="text-slate-500 mt-2">해당 모듈은 각 팀원이 개발 중입니다.</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<MainPage />} />
          <Route path="patients/:id" element={<PatientDetailPage />} />
          <Route path="brain-tumor" element={<ComingSoon title="뇌종양 진단 (변운조)" />} />
          <Route path="spine-disk" element={<ComingSoon title="허리디스크 (김담현)" />} />
          <Route path="colon-cancer" element={<ComingSoon title="대장암 예측 (박기완)" />} />
          <Route path="kidney-failure" element={<ComingSoon title="신부전 관리 (김남준)" />} />
          <Route path="skin-disease" element={<ComingSoon title="피부질환 분류 (김민수)" />} />
          <Route path="eye-disease" element={<ComingSoon title="안과 질환 (홍승현)" />} />
          <Route path="settings" element={<ComingSoon title="설정" />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}