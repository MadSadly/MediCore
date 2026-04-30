import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Eye, EyeOff } from 'lucide-react'
import MediLogo from '../components/MediLogo'

const INITIAL_LOGIN    = { email: '', password: '' }
const INITIAL_REGISTER = { email: '', password: '', confirmPassword: '', hospitalCode: '', employeeNumber: '', ssnOrLicense: '' }

function FieldError({ msg }) {
  if (!msg) return null
  return <p className="text-red-400 text-[11px] mt-1.5 flex items-center gap-1"><span>⚠</span>{msg}</p>
}

export default function LoginPage() {
  const [tab, setTab] = useState('login')

  // 로그인 / 회원가입 폼 상태 완전 분리
  const [loginForm, setLoginForm]       = useState(INITIAL_LOGIN)
  const [registerForm, setRegisterForm] = useState(INITIAL_REGISTER)

  const [showLoginPw, setShowLoginPw]   = useState(false)
  const [showRegPw, setShowRegPw]       = useState(false)
  const [showSsn, setShowSsn]           = useState(false)

  const [loginError, setLoginError]     = useState('')
  const [regErrors, setRegErrors]       = useState({})  // 필드별 에러
  const [loading, setLoading]           = useState(false)

  const navigate = useNavigate()

  const setLogin = (k) => (e) =>
    setLoginForm(f => ({ ...f, [k]: e.target.value }))

  const setReg = (k) => (e) => {
    const v = ['hospitalCode', 'employeeNumber'].includes(k)
      ? e.target.value.toUpperCase()
      : e.target.value
    setRegisterForm(f => ({ ...f, [k]: v }))
    setRegErrors(errs => ({ ...errs, [k]: '' }))
  }

  const switchTab = (t) => {
    setTab(t)
    setLoginError('')
    setRegErrors({})
  }

  // ── 로그인 ──────────────────────────────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    setLoading(true)
    try {
      const res = await axios.post('/api/auth/login', {
        email: loginForm.email.trim().toLowerCase(), password: loginForm.password,
      })
      localStorage.setItem('token', res.data.token)
      localStorage.setItem('user', JSON.stringify({ name: res.data.name, email: res.data.email }))
      navigate('/dashboard')
    } catch (err) {
      const msg = err.response?.data?.message
      if (err.response?.status === 401) {
        setLoginError('이메일 또는 비밀번호가 올바르지 않습니다.')
      } else if (err.response?.status === 404) {
        setLoginError('등록되지 않은 이메일입니다. 회원가입을 먼저 진행해주세요.')
      } else {
        setLoginError(msg || '로그인에 실패했습니다. 잠시 후 다시 시도해주세요.')
      }
    } finally {
      setLoading(false)
    }
  }

  // ── 회원가입 유효성 ──────────────────────────────────────────────────
  const validateRegister = () => {
    const errs = {}
    const f = registerForm

    if (!f.hospitalCode.trim())
      errs.hospitalCode = '병원코드를 입력해주세요.'
    else if (f.hospitalCode.length < 3)
      errs.hospitalCode = '병원코드는 3자 이상이어야 합니다.'

    if (!f.employeeNumber.trim())
      errs.employeeNumber = '사원번호를 입력해주세요.'

    if (!f.ssnOrLicense.trim()) {
      errs.ssnOrLicense = '주민등록번호 또는 의사면허번호를 입력해주세요.'
    } else {
      const digits = f.ssnOrLicense.replace(/-/g, '')
      if (digits.length === 13) {
        // 주민등록번호: 13자리
      } else if (/^\d{5,6}$/.test(digits)) {
        // 의사면허번호: 5~6자리
      } else {
        errs.ssnOrLicense = '주민등록번호(13자리) 또는 의사면허번호(5~6자리 숫자)를 정확히 입력해주세요.'
      }
    }

    if (!f.email.trim())
      errs.email = '이메일을 입력해주세요.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email))
      errs.email = '올바른 이메일 형식이 아닙니다. (예: doctor@hospital.com)'

    if (!f.password)
      errs.password = '비밀번호를 입력해주세요.'
    else if (f.password.length < 8)
      errs.password = '비밀번호는 8자 이상이어야 합니다.'
    else if (!/[a-zA-Z]/.test(f.password) || !/[0-9]/.test(f.password))
      errs.password = '비밀번호는 영문과 숫자를 모두 포함해야 합니다.'

    if (!f.confirmPassword)
      errs.confirmPassword = '비밀번호 확인을 입력해주세요.'
    else if (f.password !== f.confirmPassword)
      errs.confirmPassword = '비밀번호가 일치하지 않습니다. 다시 확인해주세요.'

    return errs
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    const errs = validateRegister()
    if (Object.keys(errs).length > 0) {
      setRegErrors(errs)
      return
    }
    setLoading(true)
    try {
      await axios.post('/api/auth/register', {
        hospitalCode:   registerForm.hospitalCode,
        employeeNumber: registerForm.employeeNumber,
        ssnOrLicense:   registerForm.ssnOrLicense,
        email:          registerForm.email,
        password:       registerForm.password,
      })
      setRegisterForm(INITIAL_REGISTER)
      setRegErrors({})
      switchTab('login')
    } catch (err) {
      const msg = err.response?.data?.message
      const status = err.response?.status
      if (status === 409)
        setRegErrors({ email: '이미 가입된 이메일입니다. 로그인을 시도해보세요.' })
      else if (status === 403)
        setRegErrors({ ssnOrLicense: '병원 DB에 등록되지 않은 정보입니다. 병원코드·사원번호·주민번호(면허번호)를 다시 확인해주세요.' })
      else
        setRegErrors({ _global: msg || '회원가입에 실패했습니다. 입력 정보를 확인 후 다시 시도해주세요.' })
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors text-sm'
  const inputErrCls = 'w-full bg-slate-900 border border-red-500/60 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-red-400 transition-colors text-sm'
  const labelCls = 'block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2'

  const inp = (key) => regErrors[key] ? inputErrCls : inputCls

  return (
    <div className="min-h-screen bg-[#0b0e14] flex items-center justify-center p-4 bg-[radial-gradient(circle_at_center,_#1a1f2b,_#0b0e14)]">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <MediLogo size={52} />
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
                onClick={() => switchTab(key)}
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

          <div className="p-8">
            {tab === 'login' ? (
              /* ── 로그인 폼 ── */
              <form onSubmit={handleLogin} className="space-y-5">
                <div>
                  <label className={labelCls}>이메일</label>
                  <input type="email" value={loginForm.email} onChange={setLogin('email')}
                    required placeholder="doctor@medi.com" className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>비밀번호</label>
                  <div className="relative">
                    <input type={showLoginPw ? 'text' : 'password'} value={loginForm.password}
                      onChange={setLogin('password')} required placeholder="••••••••"
                      className={`${inputCls} pr-11`} />
                    <button type="button" onClick={() => setShowLoginPw(s => !s)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                      {showLoginPw ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                {loginError && (
                  <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <span className="text-red-400 text-sm flex-shrink-0">⚠</span>
                    <p className="text-red-400 text-sm">{loginError}</p>
                  </div>
                )}
                <button type="submit" disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-lg font-bold text-sm transition-colors glow-blue">
                  {loading ? '로그인 중...' : '로그인'}
                </button>
              </form>
            ) : (
              /* ── 회원가입 폼 ── */
              <form onSubmit={handleRegister} className="space-y-4">

                {/* 병원 인증 섹션 */}
                <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl space-y-4">
                  <p className="text-[11px] text-blue-400 font-bold uppercase tracking-widest">병원 직원 인증</p>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className={labelCls}>병원코드</label>
                      <input type="text" value={registerForm.hospitalCode} onChange={setReg('hospitalCode')}
                        required placeholder="HOSP001" maxLength={20} className={inp('hospitalCode')} />
                      <FieldError msg={regErrors.hospitalCode} />
                    </div>
                    <div>
                      <label className={labelCls}>사원번호</label>
                      <input type="text" value={registerForm.employeeNumber} onChange={setReg('employeeNumber')}
                        required placeholder="EMP001" maxLength={20} className={inp('employeeNumber')} />
                      <FieldError msg={regErrors.employeeNumber} />
                    </div>
                  </div>

                  <div>
                    <label className={labelCls}>주민등록번호 / 의사면허번호</label>
                    <div className="relative">
                      <input
                        type={showSsn ? 'text' : 'password'}
                        value={registerForm.ssnOrLicense}
                        onChange={setReg('ssnOrLicense')}
                        required
                        placeholder="주민번호 13자리 또는 면허번호 5~6자리"
                        maxLength={14}
                        className={`${inp('ssnOrLicense')} pr-11`}
                      />
                      <button type="button" onClick={() => setShowSsn(s => !s)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                        {showSsn ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    <FieldError msg={regErrors.ssnOrLicense} />
                    {!regErrors.ssnOrLicense && (
                      <p className="text-[10px] text-slate-600 mt-1.5">
                        주민등록번호: 13자리 숫자 · 의사면허번호: 5~6자리 숫자
                      </p>
                    )}
                  </div>
                </div>

                {/* 계정 정보 섹션 */}
                <div>
                  <label className={labelCls}>사용할 이메일 (ID)</label>
                  <input type="email" value={registerForm.email} onChange={setReg('email')}
                    required placeholder="doctor@medi.com" className={inp('email')} />
                  <FieldError msg={regErrors.email} />
                </div>

                <div>
                  <label className={labelCls}>비밀번호</label>
                  <div className="relative">
                    <input type={showRegPw ? 'text' : 'password'} value={registerForm.password}
                      onChange={setReg('password')} required placeholder="영문+숫자 8자 이상"
                      className={`${inp('password')} pr-11`} />
                    <button type="button" onClick={() => setShowRegPw(s => !s)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                      {showRegPw ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                  <FieldError msg={regErrors.password} />
                </div>

                <div>
                  <label className={labelCls}>비밀번호 확인</label>
                  <input type="password" value={registerForm.confirmPassword}
                    onChange={setReg('confirmPassword')} required placeholder="••••••••"
                    className={inp('confirmPassword')} />
                  <FieldError msg={regErrors.confirmPassword} />
                </div>

                {regErrors._global && (
                  <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <span className="text-red-400 text-sm flex-shrink-0">⚠</span>
                    <p className="text-red-400 text-sm">{regErrors._global}</p>
                  </div>
                )}

                <button type="submit" disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-3 rounded-lg font-bold text-sm transition-colors glow-blue">
                  {loading ? '처리 중...' : '병원 인증 후 가입'}
                </button>
              </form>
            )}
          </div>
        </div>

        <p className="text-center text-slate-600 text-xs mt-6">MediCore AI Diagnostics System © 2026</p>
      </div>
    </div>
  )
}