import { useState, useEffect } from 'react'
import { Outlet, useParams, useLocation } from 'react-router-dom'
import PatientSidebar from './PatientSidebar'
import axios from 'axios'

const DISEASE_FAVICON = {
  'brain-tumor':    { path: 'M360-120q-100 0-170-70T120-360q0-75 40.5-136T267-587q11-94 80.5-153.5T508-800q90 0 158 53t90 140q66 11 105 61t39 113q0 78-54.5 130.5T720-250v130H360v-120Zm0-80h280v-80h80q45 0 72.5-28.5T820-382q0-45-27.5-76.5T720-490h-40v-60q0-66-47-113t-113-47q-62 0-107.5 39T360-567h-40q-58 0-99 41t-41 99q0 58 41 99t99 41h40v144Zm200-160Zm-160-40h80v-120l80-80 80 80v120h80v-157l-160-160-160 160v157Z', color: '#60a5fa' },
  'spine-disk':     { path: 'M440-80v-160H200v-80h240v-160H200v-80h240v-160H200v-80h240V-880h80v120h240v80H520v160h240v80H520v160h240v80H520v160h-80Zm80-360Zm0-240Zm0 240h80-80Zm0-240h80-80Z', color: '#a78bfa' },
  'colon-cancer':   { path: 'M480-80q-83 0-141.5-58.5T280-280q0-48 20.5-90.5T360-442v-38q-50-11-85-49t-35-91q0-58 41-99t99-41q11 0 21 1.5t19 4.5q10-29 34.5-47.5T508-820q33 0 57.5 18.5T600-754q9-3 18.5-4.5T640-760q58 0 99 41t41 99q0 53-35 91t-85 49v38q39 27 59.5 69.5T740-280q0 83-58.5 141.5T480-80Zm0-80q50 0 85-35t35-85q0-50-35-85t-85-35q-50 0-85 35t-35 85q0 50 35 85t85 35Zm-160-440q25 0 42.5-17.5T380-660q0-25-17.5-42.5T320-720q-25 0-42.5 17.5T260-660q0 25 17.5 42.5T320-600Zm320 0q25 0 42.5-17.5T700-660q0-25-17.5-42.5T640-720q-25 0-42.5 17.5T580-660q0 25 17.5 42.5T640-600ZM480-280Zm0-120Z', color: '#fbbf24' },
  'kidney-failure': { path: 'M480-80q-51 0-98-19.5T296-158q-78-72-117-166.5T140-540q0-100 44-186t116-142q14-11 31-8.5t25 16.5q20 39 49.5 70T472-742q-12-27-18-56t-6-58q0-92 58-159t150-85q17-4 30.5 4.5T704-872q29 91 15 184T660-524q-17 26-38 48t-46 37q4 9 6.5 19t2.5 20q0 42-29.5 71T484-300q-8 0-15.5-1T454-304q-9 27-13.5 55T436-192q0 41 15.5 78T495-51q-7 1-7.5 1T480-80Zm20-300q8 0 14-6t6-14q0-8-6-14t-14-6q-8 0-14 6t-6 14q0 8 6 14t14 6Z', color: '#22d3ee' },
  'skin-disease':   { path: 'M480-80q-83 0-141.5-58.5T280-280v-360l-80-80v-120h80v-40h80v40h240v-40h80v40h80v120l-80 80v360q0 83-58.5 141.5T480-80Zm0-80q50 0 85-35t35-85v-360l80-80v-40H320v40l80 80v360q0 50 35 85t45 35Zm-80-320h-80v80h80v-80Zm160 0h-80v80h80v-80Zm-80 0Zm0 200q33 0 56.5-23.5T560-360h-160q0 33 23.5 56.5T480-280Z', color: '#fb7185' },
  'eye-disease':    { path: 'M607.5-372.5Q660-425 660-500t-52.5-127.5Q555-680 480-680t-127.5 52.5Q300-575 300-500t52.5 127.5Q405-320 480-320t127.5-52.5Zm-204-51Q372-455 372-500t31.5-76.5Q435-608 480-608t76.5 31.5Q588-545 588-500t-31.5 76.5Q525-392 480-392t-76.5-31.5ZM214-281.5Q94-363 40-500q54-137 174-218.5T480-800q146 0 266 81.5T920-500q-54 137-174 218.5T480-200q-146 0-266-81.5ZM480-500Zm207.5 160.5Q782-399 832-500q-50-101-144.5-160.5T480-720q-113 0-207.5 59.5T128-500q50 101 144.5 160.5T480-280q113 0 207.5-59.5Z', color: '#2dd4bf' },
}

const DEFAULT_FAVICON = '/favicon.svg'
const DEFAULT_TITLE   = 'MEDICORE'

const DISEASE_LABELS = {
  'brain-tumor':    '뇌종양 진단',
  'spine-disk':     '허리디스크',
  'colon-cancer':   '대장암 예측',
  'kidney-failure': '신부전 관리',
  'skin-disease':   '피부질환 분류',
  'eye-disease':    '안과 질환',
}

function makeFaviconHref(path, color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" fill="${color}"><path d="${path}"/></svg>`
  return `data:image/svg+xml,${encodeURIComponent(svg)}`
}

function setFavicon(href) {
  let link = document.querySelector("link[rel~='icon']")
  if (!link) {
    link = document.createElement('link')
    link.rel = 'icon'
    document.head.appendChild(link)
  }
  link.href = href
}

export default function PatientLayout() {
  const { id } = useParams()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [patientName, setPatientName] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    axios.get(`/api/patients/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => setPatientName(res.data.name))
      .catch(() => setPatientName(''))
  }, [id])

  // 현재 경로에 맞게 파비콘·탭 타이틀 교체
  useEffect(() => {
    const segment = location.pathname.split('/').pop()
    const disease = DISEASE_FAVICON[segment]

    if (disease) {
      setFavicon(makeFaviconHref(disease.path, disease.color))
      document.title = `${DISEASE_LABELS[segment]} | MEDICORE`
    } else {
      setFavicon(DEFAULT_FAVICON)
      document.title = DEFAULT_TITLE
    }

    return () => {
      setFavicon(DEFAULT_FAVICON)
      document.title = DEFAULT_TITLE
    }
  }, [location.pathname])

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0b0e14]">
      <PatientSidebar
        patientId={id}
        patientName={patientName}
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(o => !o)}
      />
      <div
        className="flex-1 flex flex-col min-w-0 sidebar-transition overflow-auto"
        style={{ marginLeft: sidebarOpen ? '18rem' : '5rem' }}
      >
        <main className="flex-1 p-6 custom-scrollbar bg-[radial-gradient(circle_at_top_right,_#1a1f2b,_#0b0e14)]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}