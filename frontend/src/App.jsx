import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import MainPage from './pages/MainPage'
import PatientDetailPage from './pages/PatientDetailPage'
import MainLayout from './components/MainLayout'
import PatientLayout from './components/PatientLayout'

// 팀원별 진단 페이지 (각자 본인 폴더 파일만 수정하세요)
import BrainTumorPage    from './WJ/BrainTumorPage'     // WJ - 뇌종양
import SpineDiskPage     from './DH/SpineDiskPage'       // DH - 허리디스크
import ColonCancerPage   from './GW/ColonCancerPage'     // GW - 대장암
import KidneyFailurePage from './NJ/KidneyFailurePage'   // NJ - 신부전
import SkinDiseasePage   from './MS/SkinDiseasePage'     // MS - 피부질환
import EyeDiseasePage    from './SH/EyeDiseasePage'      // SH - 안과

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