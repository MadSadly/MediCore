import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import MainPage from './pages/MainPage'
import PatientDetailPage from './pages/PatientDetailPage'
import DiagnosisPage from './pages/DiagnosisPage'
import MainLayout from './components/MainLayout'
import PatientLayout from './components/PatientLayout'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* 메인 (사이드바 없음) */}
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <MainLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<MainPage />} />
        </Route>

        {/* 환자 상세 (사이드바 있음, 환자 ID 고정) */}
        <Route
          path="/patients/:id"
          element={
            <PrivateRoute>
              <PatientLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<PatientDetailPage />} />
          <Route path="brain-tumor"    element={<DiagnosisPage diseaseType="brain-tumor"    label="뇌종양 진단"   assignee="변운조" />} />
          <Route path="spine-disk"     element={<DiagnosisPage diseaseType="spine-disk"     label="허리디스크"    assignee="김담현" />} />
          <Route path="colon-cancer"   element={<DiagnosisPage diseaseType="colon-cancer"   label="대장암 예측"   assignee="박기완" />} />
          <Route path="kidney-failure" element={<DiagnosisPage diseaseType="kidney-failure" label="신부전 관리"   assignee="김남준" />} />
          <Route path="skin-disease"   element={<DiagnosisPage diseaseType="skin-disease"   label="피부질환 분류" assignee="김민수" />} />
          <Route path="eye-disease"    element={<DiagnosisPage diseaseType="eye-disease"    label="안과 질환"     assignee="홍승현" />} />
        </Route>

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}