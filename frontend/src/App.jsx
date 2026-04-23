import { useState } from 'react'
import axios from 'axios'

function StatusBadge({ status }) {
  if (status === null) return <span className="text-gray-400">대기 중</span>
  if (status === 'loading') return <span className="text-yellow-500 animate-pulse">확인 중...</span>
  if (status === 'ok') return <span className="text-green-500 font-bold">연결 성공</span>
  return <span className="text-red-500 font-bold">연결 실패</span>
}

function ServerCard({ title, endpoint, description }) {
  const [status, setStatus] = useState(null)
  const [detail, setDetail] = useState('')

  const check = async () => {
    setStatus('loading')
    setDetail('')
    try {
      const res = await axios.get(endpoint)
      setStatus('ok')
      setDetail(JSON.stringify(res.data))
    } catch (e) {
      setStatus('error')
      setDetail(e.message)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-6 flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold text-gray-800">{title}</h2>
        <StatusBadge status={status} />
      </div>
      <p className="text-sm text-gray-500">{description}</p>
      <code className="text-xs bg-gray-100 rounded px-2 py-1 text-gray-600">{endpoint}</code>
      {detail && (
        <pre className="text-xs bg-gray-50 border rounded p-2 overflow-auto max-h-20">{detail}</pre>
      )}
      <button
        onClick={check}
        className="mt-auto bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-2 text-sm font-semibold transition-colors"
      >
        연결 테스트
      </button>
    </div>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-black text-gray-900 mb-2">MEDI-Zero 서버 연결 테스트</h1>
      <p className="text-gray-500 mb-8">각 서버의 연결 버튼을 눌러 상태를 확인하세요.</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
        <ServerCard
          title="Spring Boot"
          endpoint="/api/health"
          description="React → Vite Proxy → Spring :8080"
        />
        <ServerCard
          title="FastAPI (직접)"
          endpoint="/ai/health"
          description="React → Vite Proxy → FastAPI :8000"
        />
        <ServerCard
          title="Spring → FastAPI"
          endpoint="/api/ai-health"
          description="React → Spring :8080 → FastAPI :8000"
        />
      </div>
    </div>
  )
}
