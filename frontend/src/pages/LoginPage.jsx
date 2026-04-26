import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Stethoscope, Eye, EyeOff } from 'lucide-react'

export default function LoginPage() {
  const [tab, setTab] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await axios.post('/api/auth/login', { email: form.email, password: form.password })
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify({ name: res.data.name, email: res.data.email }))
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || '로그인에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.')
      return
    }
    setLoading(true)
    try {
      await axios.post('/api/auth/register', { name: form.name, email: form.email, password: form.password })
      setTab('login')
      setForm(f => ({ ...f, name: '', confirmPassword: '' }))
    } catch (err) {
      setError(err.response?.data?.message || '회원가입에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0e14] flex items-center justify-center p-4 bg-[radial-gradient(circle_at_center,_#1a1f2b,_#0b0e14)]">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="bg-blue-600 p-3 rounded-xl glow-blue">
            <Stethoscope size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-white tracking-wide">MEDICORE</h1>
            <p className="text-[10px] text-blue-400 uppercase tracking-widest font-bold">AI 정밀 진단 시스템</p>
          </div>
        </div>

        {/* Card */}
        <div className="glass-card rounded-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-slate-800">
            {[
              { key: 'login', label: '로그인' },
              { key: 'register', label: '회원가입' },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => { setTab(key); setError('') }}
                className={`flex-1 py-4 text-sm font-bold transition-colors ${
                  tab === key
                    ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-600/5'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Form */}
          <div className="p-8">
            {tab === 'login' ? (
              <form onSubmit={handleLogin} className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">이메일</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={set('email')}
                    required
                    placeholder="doctor@medi.com"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">비밀번호</label>
                  <div className="relative">
                    <input
                      type={showPw ? 'text' : 'password'}
                      value={form.password}
                      onChange={set('password')}
                      required
                      placeholder="••••••••"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 pr-11 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                    />
                    <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                      {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                {error && <p className="text-red-400 text-sm">{error}</p>}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-lg font-bold text-sm transition-colors glow-blue"
                >
                  {loading ? '로그인 중...' : '로그인'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="space-y-5">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">이름</label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={set('name')}
                    required
                    placeholder="홍길동"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">이메일</label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={set('email')}
                    required
                    placeholder="doctor@medi.com"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">비밀번호</label>
                  <div className="relative">
                    <input
                      type={showPw ? 'text' : 'password'}
                      value={form.password}
                      onChange={set('password')}
                      required
                      placeholder="••••••••"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 pr-11 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                    />
                    <button type="button" onClick={() => setShowPw(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                      {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">비밀번호 확인</label>
                  <input
                    type="password"
                    value={form.confirmPassword}
                    onChange={set('confirmPassword')}
                    required
                    placeholder="••••••••"
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm"
                  />
                </div>
                {error && <p className="text-red-400 text-sm">{error}</p>}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-lg font-bold text-sm transition-colors glow-blue"
                >
                  {loading ? '처리 중...' : '회원가입'}
                </button>
              </form>
            )}
          </div>
        </div>

        <p className="text-center text-slate-600 text-xs mt-6">MediCore AI Diagnostics System © 2025</p>
      </div>
    </div>
  )
}