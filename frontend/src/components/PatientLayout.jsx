import { useState, useEffect } from 'react'
import { Outlet, useParams } from 'react-router-dom'
import PatientSidebar from './PatientSidebar'
import axios from 'axios'

export default function PatientLayout() {
  const { id } = useParams()
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