import { useEffect, useState } from 'react'
import { BrowserRouter, Navigate, NavLink, Route, Routes, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  LayoutDashboard, Building2, Users, GraduationCap, FlaskConical, FileCheck2,
  FolderArchive, ClipboardCheck, BarChart3, Bell, History, Settings, UserCircle,
  LogOut, Menu, Search, Plus, BriefcaseBusiness, ChevronRight, Eye, EyeOff, Upload, Download
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, LabelList } from 'recharts'
import api from './api'

const nav = [
  ['Dashboard', '/', LayoutDashboard],
  ['Institutions', '/institutions', Building2],
  ['Academic Years', '/academic-years', BookIcon],
  ['Facilities', '/facilities', Building2],
  ['Departments', '/departments', Building2],
  ['Programmes', '/programmes', BookIcon],
  ['Courses', '/courses', BookIcon],
  ['Faculty', '/faculty', Users],
  ['Students', '/students', GraduationCap],
  ['Research', '/research', FlaskConical],
  ['Publications', '/publications', FileCheck2],
  ['Placements', '/placements', BriefcaseBusiness],
  ['Accreditation', '/frameworks', FileCheck2],
  ['Criteria', '/criteria', ClipboardCheck],
  ['Parameters', '/parameters', ClipboardCheck],
  ['Evidence', '/evidence', FolderArchive],
  ['Submissions', '/submissions', ClipboardCheck],
  ['Users', '/users', UserCircle],
  ['Reports', '/reports', BarChart3],
  ['Notifications', '/notifications', Bell],
  ['Audit History', '/audit', History],
  ['Profile', '/profile', Settings],
]

const excelImportEndpoints = [
  'institutions', 'academic-years', 'facilities', 'departments', 'programmes',
  'courses', 'faculty', 'students', 'research-projects', 'publications',
  'placements', 'frameworks', 'criteria', 'parameters',
]

function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/login/', { username, password })
      localStorage.setItem('access', data.access)
      localStorage.setItem('refresh', data.refresh)
      navigate('/')
    } catch {
      setError('Invalid username or password.')
    }
  }
  return (
    <main className="login-page">
      <section className="login-brand">
        <div className="brand-mark">A</div>
        <div>
          <h1>Accreditation & Institutional Data</h1>
          <p>Management System</p>
        </div>
      </section>
      <form className="login-card" onSubmit={submit}>
        <h2>Welcome back</h2>
        <p className="muted">Sign in to your institutional workspace</p>
        {error && <div className="alert-error">{error}</div>}
        <label>Username
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter username" required />
        </label>
        <label>Password
          <div className="password-field">
            <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter password" required />
            <button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </label>
        <button className="primary-btn" type="submit">Sign in</button>
        <small>Demo: admin / Password@123</small>
        <button type="button" className="link-btn" onClick={() => navigate('/register')}>Create a new account</button>
        <button type="button" className="link-btn" onClick={() => navigate('/student-login')}>Student login or registration</button>
      </form>
    </main>
  )
}

function Protected({ children }) {
  const [state, setState] = useState(() => localStorage.getItem('access') ? 'checking' : 'signed-out')
  useEffect(() => {
    if (!localStorage.getItem('access')) return
    api.get('/auth/me/')
      .then(({ data }) => setState(data.role === 'STUDENT' ? 'student' : 'staff'))
      .catch(() => {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        setState('signed-out')
      })
  }, [])
  if (state === 'checking') return <div className="loader">Checking account...</div>
  if (state === 'student') return <Navigate to="/student/portal" replace />
  if (state === 'signed-out') return <Navigate to="/login" replace />
  return children
}

function StudentProtected({ children }) {
  const [state, setState] = useState(() => localStorage.getItem('access') ? 'checking' : 'signed-out')
  useEffect(() => {
    if (!localStorage.getItem('access')) return
    api.get('/auth/me/')
      .then(({ data }) => setState(data.role === 'STUDENT' ? 'student' : 'staff'))
      .catch(() => {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        setState('signed-out')
      })
  }, [])
  if (state === 'checking') return <div className="loader">Checking account...</div>
  if (state === 'signed-out') return <Navigate to="/student-login" replace />
  if (state === 'staff') return <Navigate to="/" replace />
  return children
}

function StudentLoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/auth/login/', { username, password })
      localStorage.setItem('access', data.access)
      localStorage.setItem('refresh', data.refresh)
      const profile = await api.get('/auth/me/')
      if (profile.data.role !== 'STUDENT') {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
        setError('This account is not a student account. Use the institutional sign-in page.')
        return
      }
      navigate('/student/portal')
    } catch {
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
      setError('Unable to sign in. Check your username and password.')
    }
  }

  return (
    <form className="login-card" onSubmit={submit}>
      <h2>Student login</h2>
      {error && <div className="alert-error">{error}</div>}
      <label>Username<input value={username} onChange={e => setUsername(e.target.value)} required /></label>
      <label>Password<div className="password-field">
        <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>
          {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div></label>
      <button className="primary-btn" type="submit">Sign in</button>
      <button type="button" className="link-btn" onClick={() => navigate('/login')}>Institutional sign in</button>
    </form>
  )
}

function StudentRegisterForm({ onSwitchToLogin, onRegistered }) {
  const [options, setOptions] = useState(null)
  const [form, setForm] = useState({
    username: '', email: '', password: '', confirmPassword: '', full_name: '',
    student_id: '', roll_number: '', institution: '', department: '', programme: '',
    academic_year: '', admission_year: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/auth/student-options/')
      .then(({ data }) => setOptions(data))
      .catch(() => setError('Unable to load universities and academic options. Refresh and try again.'))
  }, [])

  const departments = (options?.departments || []).filter(
    item => String(item.institution_id) === form.institution)
  const programmes = (options?.programmes || []).filter(
    item => String(item.department_id) === form.department)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setSaving(true)
    try {
      await api.post('/auth/student-register/', {
        username: form.username,
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        student_id: form.student_id,
        roll_number: form.roll_number,
        institution: form.institution,
        department: form.department,
        programme: form.programme,
        academic_year: form.academic_year,
        admission_year: form.admission_year,
      })
      setSuccess('Student account created. Redirecting to student login...')
      setTimeout(onRegistered, 900)
    } catch (e) {
      const data = e.response?.data
      setError(typeof data === 'string' ? data : JSON.stringify(data || 'Unable to create student account'))
    } finally {
      setSaving(false)
    }
  }

  return (
      <form className="login-card student-register-card" onSubmit={submit}>
        <h2>Student registration</h2>
        {error && <div className="alert-error">{error}</div>}
        {success && <div className="notice">{success}</div>}
        {options && !options.institutions.length && <div className="alert-error">No universities have departments and programmes configured yet. Please contact an administrator.</div>}
        <div className="student-form-grid">
          <label>Full name<input value={form.full_name} onChange={e => setForm({...form, full_name:e.target.value})} required /></label>
          <label>Username<input value={form.username} onChange={e => setForm({...form, username:e.target.value})} required /></label>
          <label>Email<input type="email" value={form.email} onChange={e => setForm({...form, email:e.target.value})} required /></label>
          <label>Student ID<input value={form.student_id} onChange={e => setForm({...form, student_id:e.target.value})} required /></label>
          <label>Roll number<input value={form.roll_number} onChange={e => setForm({...form, roll_number:e.target.value})} required /></label>
          <label>University / Institution<select value={form.institution} onChange={e => setForm({...form, institution:e.target.value, department:'', programme:''})} required>
            <option value="">Select university</option>{options?.institutions.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
          <label>Department<select value={form.department} onChange={e => {
            const department = e.target.value
            const matchingProgrammes = (options?.programmes || []).filter(
              item => String(item.department_id) === department)
            setForm({
              ...form,
              department,
              programme: matchingProgrammes.length === 1 ? String(matchingProgrammes[0].id) : '',
            })
          }} required disabled={!form.institution}>
            <option value="">Select department</option>{departments.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
          <label>Programme<select value={form.programme} onChange={e => setForm({...form, programme:e.target.value})} required disabled={!form.department}>
            <option value="">Select programme</option>{programmes.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
          <label>Academic year<select value={form.academic_year} onChange={e => setForm({...form, academic_year:e.target.value})} required>
            <option value="">Select academic year</option>{options?.academic_years.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select></label>
          <label>Admission year<input type="number" min="1900" max="2200" value={form.admission_year} onChange={e => setForm({...form, admission_year:e.target.value})} required /></label>
          <label>Password<div className="password-field">
            <input type={showPassword ? 'text' : 'password'} value={form.password} onChange={e => setForm({...form, password:e.target.value})} required />
            <button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div></label>
          <label>Confirm password<input type={showPassword ? 'text' : 'password'} value={form.confirmPassword} onChange={e => setForm({...form, confirmPassword:e.target.value})} required /></label>
        </div>
        <button className="primary-btn" type="submit" disabled={saving || !options}>{saving ? 'Creating account...' : 'Create student account'}</button>
        <button type="button" className="link-btn" onClick={onSwitchToLogin}>Already registered? Student login</button>
      </form>
  )
}

function StudentAuth() {
  const location = useLocation()
  const navigate = useNavigate()
  const isRegister = location.pathname === '/student-register'
  function switchMode(mode) {
    navigate(mode === 'register' ? '/student-register' : '/student-login')
  }
  return (
    <main className="login-page student-auth-page">
      <section className="login-brand"><div className="brand-mark">A</div><div>
        <h1>Student Portal</h1><p>Access your university account or create a student record.</p>
      </div></section>
      <section className="student-auth-panel">
        <div className="student-auth-tabs" role="tablist" aria-label="Student account">
          <button type="button" role="tab" aria-selected={!isRegister} className={!isRegister ? 'active' : ''} onClick={() => switchMode('login')}>Student login</button>
          <button type="button" role="tab" aria-selected={isRegister} className={isRegister ? 'active' : ''} onClick={() => switchMode('register')}>Student registration</button>
        </div>
        {isRegister
          ? <StudentRegisterForm onSwitchToLogin={() => switchMode('login')} onRegistered={() => switchMode('login')} />
          : <StudentLoginForm />}
      </section>
    </main>
  )
}

function StudentPortal() {
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  useEffect(() => {
    api.get('/auth/student-profile/')
      .then(({ data }) => setProfile(data))
      .catch(() => setError('Unable to load your student profile. Please contact your university administrator.'))
  }, [])

  function logout() {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    navigate('/student-login')
  }

  return (
    <main className="student-portal-page">
      <header className="student-portal-header">
        <div><div className="brand-mark small">A</div><div><strong>Student Portal</strong><span>Accreditation & Institutional Data</span></div></div>
        <button className="secondary-btn" onClick={logout}>Sign out</button>
      </header>
      <section className="student-portal-content">
        <p className="eyebrow">MY UNIVERSITY RECORD</p>
        <h1>{profile?.full_name || 'Student account'}</h1>
        {error && <div className="alert-error">{error}</div>}
        {!profile && !error && <div className="loader">Loading your profile...</div>}
        {profile && <div className="student-profile-grid">
          <article><span>University</span><strong>{profile.institution_name}</strong></article>
          <article><span>Department</span><strong>{profile.department_name}</strong></article>
          <article><span>Programme</span><strong>{profile.programme_name}</strong></article>
          <article><span>Academic year</span><strong>{profile.academic_year_name}</strong></article>
          <article><span>Student ID</span><strong>{profile.student_id}</strong></article>
          <article><span>Roll number</span><strong>{profile.roll_number}</strong></article>
          <article><span>Email</span><strong>{profile.email}</strong></article>
          <article><span>Admission year</span><strong>{profile.admission_year}</strong></article>
        </div>}
      </section>
    </main>
  )
}

function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '', confirmPassword: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    try {
      await api.post('/auth/register/', {
        username: form.username,
        email: form.email,
        password: form.password,
      })
      setSuccess('Account created. Redirecting to login...')
      setTimeout(() => navigate('/login'), 900)
    } catch (e) {
      setError(JSON.stringify(e.response?.data || 'Unable to create account'))
    }
  }

  return (
    <main className="login-page">
      <section className="login-brand">
        <div className="brand-mark">A</div>
        <div><h1>Create Institutional Account</h1><p>Accreditation & Institutional Data Management</p></div>
      </section>
      <form className="login-card" onSubmit={submit}>
        <h2>Register</h2>
        {error && <div className="alert-error">{error}</div>}
        {success && <div className="notice">{success}</div>}
        <label>Username<input value={form.username} onChange={e => setForm({...form, username:e.target.value})} required /></label>
        <label>Email<input type="email" value={form.email} onChange={e => setForm({...form, email:e.target.value})} required /></label>
        <label>Password
          <div className="password-field">
            <input type={showPassword ? 'text' : 'password'} value={form.password} onChange={e => setForm({...form, password:e.target.value})} required />
            <button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </label>
        <label>Confirm password
          <input type={showPassword ? 'text' : 'password'} value={form.confirmPassword} onChange={e => setForm({...form, confirmPassword:e.target.value})} required />
        </label>
        <button className="primary-btn" type="submit">Create account</button>
        <button type="button" className="link-btn" onClick={() => navigate('/login')}>Back to login</button>
      </form>
    </main>
  )
}

function StatCard({ title, value, icon: Icon, tone, onClick }) {
  return (
    <article className={`stat-card ${onClick ? 'stat-card-clickable' : ''}`} onClick={onClick} role={onClick ? 'button' : undefined}>
      <div className={`stat-icon ${tone}`}><Icon size={21} /></div>
      <div><p>{title}</p><strong>{value ?? 0}</strong></div>
    </article>
  )
}

function Dashboard() {
  const params = useParams()
  const [data, setData] = useState(null)
  const [institutions, setInstitutions] = useState([])
  const [institution, setInstitution] = useState(params.institutionId || localStorage.getItem('dashboard_institution') || '')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/institutions/?page_size=100').then(r => setInstitutions(r.data.results || r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (params.institutionId) setInstitution(params.institutionId)
  }, [params.institutionId])

  useEffect(() => {
    localStorage.setItem('dashboard_institution', institution)
    api.get('/dashboard/', { params: institution ? { institution } : {} })
      .then(r => setData(r.data))
      .catch(() => setData(null))
  }, [institution])
  function selectInstitution(value) {
    setInstitution(value)
    localStorage.setItem('dashboard_institution', value)
    if (value) navigate(`/dashboard/${value}`)
    else navigate('/')
  }
  function openData(path) {
    navigate(institution ? `${path}?institution=${institution}` : path)
  }
  const pieData = data?.submission_stats?.map(x => ({
    name: String(x.status).replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase()),
    value: x.count,
  })) || []
  const colors = ['#2563eb', '#f59e0b', '#22a06b', '#8b5cf6', '#ef4444', '#06b6d4']
  return (
    <div className="page">
      <div className="page-heading">
        <div><p className="eyebrow">OVERVIEW</p><h1>Institution Dashboard</h1></div>
        <label className="institution-selector">{data?.institution || 'Institution'}
          <select value={institution} onChange={e => selectInstitution(e.target.value)}>
            <option value="">All institutions</option>
            {institutions.map(i => <option key={i.id} value={i.id}>{i.name}</option>)}
          </select>
        </label>
      </div>
      <section className="stats-grid">
        <StatCard title="Departments" value={data?.departments} icon={Building2} tone="blue" onClick={() => openData('/departments')} />
        <StatCard title="Faculty" value={data?.faculty} icon={Users} tone="violet" onClick={() => openData('/faculty')} />
        <StatCard title="Students" value={data?.students} icon={GraduationCap} tone="green" onClick={() => openData('/students')} />
        <StatCard title="Programmes" value={data?.programmes} icon={BookIcon} tone="amber" onClick={() => openData('/programmes')} />
        <StatCard title="Research Projects" value={data?.research_projects} icon={FlaskConical} tone="pink" onClick={() => openData('/research')} />
        <StatCard title="Publications" value={data?.publications} icon={FileCheck2} tone="cyan" onClick={() => openData('/publications')} />
      </section>
      <section className="chart-grid">
        <article className="panel"><div className="panel-head"><h3>Department-wise Students</h3></div>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.department_stats || []}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip formatter={(value) => [`${value} students`, 'Student Count']} />
                <Bar dataKey="student_count" name="Students" fill="#2563eb" radius={[5, 5, 0, 0]}>
                  <LabelList dataKey="student_count" position="top" fill="#eaf1ff" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>
        <article className="panel"><div className="panel-head"><h3>Submission Status</h3></div>
          <div className="chart-box pie-box">
            {pieData.length ? <ResponsiveContainer width="100%" height="100%">
              <PieChart><Pie data={pieData} dataKey="value" nameKey="name" innerRadius={48} outerRadius={78} paddingAngle={2}>
                {pieData.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
                <LabelList dataKey="value" position="inside" fill="#fff" fontSize={11} />
              </Pie><Tooltip formatter={(value, name) => [`${value} submissions`, name]} /><Legend wrapperStyle={{ fontSize: 10, color: '#93a4c4' }} /></PieChart>
            </ResponsiveContainer> : <div className="empty-chart">No submissions yet</div>}
          </div>
        </article>
        <article className="panel completion-panel"><div className="panel-head"><h3>Data Completeness</h3></div>
          <div className="progress-ring" style={{ '--value': `${data?.data_completeness || 0}%` }}>
            <span>{data?.data_completeness || 0}%</span>
          </div>
          <p className="muted">{data?.verified_records || 0} verified records</p>
        </article>
      </section>
      <section className="lower-grid">
        <article className="panel clickable-panel" onClick={() => navigate('/submissions')}><div className="panel-head"><h3>Pending Approvals</h3><span className="badge">{data?.pending_submissions || 0}</span></div>
          <div className="activity-list">{(data?.recent_activity || []).slice(0, 5).map((a, i) =>
            <div className="activity" key={i}><div className="activity-dot" /><div><strong>{a.action}</strong><p>{a.module} • {a.record_reference || 'Record'}</p></div><ChevronRight size={16} /></div>)}
            {!data?.recent_activity?.length && <p className="empty">No recent activity</p>}</div>
        </article>
        <article className="panel clickable-panel" onClick={() => navigate('/frameworks')}><div className="panel-head"><h3>Accreditation Summary</h3></div>
          <div className="summary-list">
            <div><span>Criteria</span><strong>{data?.criteria || 0}</strong></div>
            <div><span>Parameters</span><strong>{data?.parameters || 0}</strong></div>
            <div><span>Verified</span><strong>{data?.verified_records || 0}</strong></div>
            <div><span>Missing evidence</span><strong className="danger">{data?.missing_evidence || 0}</strong></div>
          </div>
        </article>
      </section>
    </div>
  )
}

function BookIcon(props) { return <GraduationCap {...props} /> }

function GenericList({ endpoint, title, fields, formFields = null, addLabel = 'Add Record', institutionFilter = null, currentUserRole = null }) {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const institutionId = searchParams.get('institution')
  const [rows, setRows] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [institutions, setInstitutions] = useState([])
  const [institutionLoadError, setInstitutionLoadError] = useState('')
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState(null)
  const [importInstitution, setImportInstitution] = useState(institutionId || '')
  const [importing, setImporting] = useState(false)
  const [importError, setImportError] = useState('')
  const [importSuccess, setImportSuccess] = useState('')
  const [resolvedUserRole, setResolvedUserRole] = useState(currentUserRole)
  const effectiveUserRole = currentUserRole || resolvedUserRole
  const isStudentImport = endpoint === 'students'
  const canImportRecords = excelImportEndpoints.includes(endpoint)
    && ['SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'].includes(effectiveUserRole)
    && (endpoint !== 'institutions' || effectiveUserRole === 'SUPER_ADMIN')

  useEffect(() => {
    if (currentUserRole) {
      setResolvedUserRole(currentUserRole)
      return
    }
    api.get('/auth/me/')
      .then(({ data }) => setResolvedUserRole(data.role))
      .catch(() => setResolvedUserRole(null))
  }, [currentUserRole])

  useEffect(() => {
    if (!['departments', 'students'].includes(endpoint)) return
    api.get('/institutions/', { params: { page_size: 100 } })
      .then(r => setInstitutions(Array.isArray(r.data) ? r.data : r.data.results || []))
      .catch(() => setInstitutionLoadError('Unable to load institutions. Refresh the page and try again.'))
  }, [endpoint])

  async function load() {
    setLoading(true)
    try {
      const r = await api.get(`/${endpoint}/`, { params: {
        ...(search ? { search } : {}),
        ...(institutionId && institutionFilter ? { [institutionFilter]: institutionId } : {}),
      } })
      setRows(Array.isArray(r.data) ? r.data : r.data.results || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [endpoint, search, institutionId])

  function openCreate() {
    setEditing({})
    const defaults = Object.fromEntries((formFields || []).map(f => [f.name, f.default ?? '']))
    if (endpoint === 'departments') {
      defaults.institution = institutions.some(item => String(item.id) === institutionId) ? institutionId : ''
    }
    setForm(defaults)
    setError(institutionLoadError)
  }

  function openEdit(row) {
    setEditing(row)
    setForm(Object.fromEntries((formFields || []).map(f => [f.name, row[f.name] ?? f.default ?? ''])))
    setError('')
  }

  async function save(e) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (editing?.id) await api.patch(`/${endpoint}/${editing.id}/`, form)
      else await api.post(`/${endpoint}/`, form)
      setEditing(null)
      await load()
    } catch (e) {
      const data = e.response?.data
      setError(typeof data === 'string' ? data : JSON.stringify(data || 'Unable to save record'))
    } finally {
      setSaving(false)
    }
  }

  async function remove(row) {
    if (!window.confirm(`Delete ${row.name || row.full_name || row.title || 'this record'}?`)) return
    try {
      await api.delete(`/${endpoint}/${row.id}/`)
      setRows(previous => previous.filter(item => item.id !== row.id))
      await load()
    } catch (e) {
      const detail = e.response?.data?.detail || e.response?.data || 'This record could not be deleted because it is still referenced by other data.'
      window.alert(typeof detail === 'string' ? detail : JSON.stringify(detail))
    }
  }

  function openImport() {
    setImportInstitution(institutionId || '')
    setImportFile(null)
    setImportError('')
    setImportSuccess('')
    setImportOpen(value => !value)
  }

  async function downloadImportTemplate() {
    setImportError('')
    try {
      const templatePath = isStudentImport
        ? '/students/import-template/'
        : `/bulk-import/${endpoint}/template/`
      const response = await api.get(templatePath, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = isStudentImport ? 'student_import_template.xlsx' : `${endpoint}_import_template.xlsx`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      setImportError(e.response?.data?.detail || 'Unable to download the Excel template.')
    }
  }

  async function importRecords(e) {
    e.preventDefault()
    setImportError('')
    setImportSuccess('')
    if (!importFile) {
      setImportError('Choose an .xlsx workbook to import.')
      return
    }
    const body = new FormData()
    body.append('file', importFile)
    if (isStudentImport && importInstitution) body.append('institution', importInstitution)
    setImporting(true)
    try {
      const importPath = isStudentImport ? '/students/import-excel/' : `/bulk-import/${endpoint}/`
      const response = await api.post(importPath, body)
      setImportSuccess(response.data.detail)
      setImportFile(null)
      await load()
    } catch (e) {
      const data = e.response?.data
      const rowErrors = data?.errors?.map(item =>
        `Row ${item.row}: ${Object.entries(item.errors).map(([field, message]) => `${field}: ${message}`).join(', ')}`
      )
      setImportError(rowErrors?.length
        ? `${data.detail}\n${rowErrors.join('\n')}`
        : typeof data?.detail === 'string' ? data.detail : JSON.stringify(data || 'Unable to import student records'))
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="page">
      <div className="page-heading"><div><p className="eyebrow">MANAGEMENT</p><h1>{title}</h1></div>
        <div className="page-heading-actions">
          {canImportRecords && <button className="secondary-btn compact" onClick={openImport}><Upload size={16} /> Import Excel</button>}
          {formFields && <button className="primary-btn compact" onClick={openCreate}><Plus size={17} /> {addLabel}</button>}
        </div>
      </div>
      {importOpen && canImportRecords && <article className="panel student-import-panel">
        <div className="student-import-heading"><div><h3>Import {title.toLowerCase()}</h3><p>Downloads a section-specific template. Foreign-key columns use IDs listed on the workbook's reference sheets; the entire workbook is validated before saving.</p></div>
          <button type="button" className="text-action" onClick={downloadImportTemplate}><Download size={15} /> Download template</button>
        </div>
        <form className="student-import-form" onSubmit={importRecords}>
          {isStudentImport && effectiveUserRole === 'SUPER_ADMIN'
            ? <label>University<select value={importInstitution} onChange={e => setImportInstitution(e.target.value)} required>
                <option value="">Select university</option>{institutions.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select></label>
            : isStudentImport && <p className="muted">Student records will be added to your university; no login accounts are created.</p>}
          <label>Excel workbook (.xlsx)<input type="file" accept=".xlsx" onChange={e => setImportFile(e.target.files?.[0] || null)} required /></label>
          <button className="primary-btn compact" type="submit" disabled={importing}>{importing ? 'Importing...' : 'Import records'}</button>
        </form>
        {isStudentImport && effectiveUserRole === 'SUPER_ADMIN' && institutionLoadError && <div className="alert-error">{institutionLoadError}</div>}
        {importError && <div className="alert-error" style={{ whiteSpace: 'pre-wrap' }}>{importError}</div>}
        {importSuccess && <div className="notice">{importSuccess}</div>}
      </article>}
      <article className="panel table-panel">
        <div className="table-tools"><div className="search-box"><Search size={17} /><input value={search} onChange={e => setSearch(e.target.value)} placeholder={`Search ${title.toLowerCase()}...`} /></div></div>
        {loading ? <div className="loader">Loading...</div> : <div className="table-wrap"><table>
          <thead><tr>{fields.map(f => <th key={f.key}>{f.label}</th>)}{formFields && <th>Actions</th>}</tr></thead>
          <tbody>{rows.map(row => <tr key={row.id}>{fields.map(f => <td key={f.key}>{String(row[f.key] ?? '—')}</td>)}
            {formFields && <td><div className="row-actions">
              {endpoint === 'institutions' && <button onClick={() => navigate(`/dashboard/${row.id}`)}>Open Dashboard</button>}
              <button onClick={() => openEdit(row)}>Edit</button><button onClick={() => remove(row)}>Delete</button>
            </div></td>}
          </tr>)}</tbody>
        </table>{!rows.length && <div className="empty">No records found</div>}</div>}
      </article>
      {editing && <div className="modal-backdrop" onMouseDown={() => setEditing(null)}>
        <form className="modal-card" onSubmit={save} onMouseDown={e => e.stopPropagation()}>
          <div className="modal-head"><h3>{editing.id ? 'Edit' : 'Add'} {title.replace(/s$/, '')}</h3><button type="button" onClick={() => setEditing(null)}>×</button></div>
          {error && <div className="alert-error">{error}</div>}
          <div className="modal-fields">{formFields.map(f =>
            f.type === 'select' || (endpoint === 'departments' && f.name === 'institution')
              ? <label key={f.name}>{f.label}<select value={form[f.name] ?? ''} onChange={e => setForm({...form, [f.name]: e.target.value})} required={f.required}>
                  <option value="">Select {f.label}</option>
                  {endpoint === 'departments' && f.name === 'institution'
                    ? institutions.map(item => <option key={item.id} value={item.id}>{item.name}</option>)
                    : f.options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select></label>
              : <label key={f.name}>{f.label}{f.textarea
                ? <textarea value={form[f.name] ?? ''} onChange={e => setForm({...form, [f.name]: e.target.value})} required={f.required} />
                : <input type={f.type || 'text'} value={form[f.name] ?? ''} onChange={e => setForm({...form, [f.name]: e.target.value})} required={f.required} />
              }</label>)}</div>
          <div className="modal-actions"><button type="button" className="secondary-btn" onClick={() => setEditing(null)}>Cancel</button><button className="primary-btn" disabled={saving}>{saving ? 'Saving...' : 'Save Record'}</button></div>
        </form>
      </div>}
    </div>
  )
}

function Evidence() {
  const [rows, setRows] = useState([])
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [userRole, setUserRole] = useState(null)
  const [importOpen, setImportOpen] = useState(false)
  const [importWorkbook, setImportWorkbook] = useState(null)
  const [importDocuments, setImportDocuments] = useState([])
  const [importError, setImportError] = useState('')
  const [importSuccess, setImportSuccess] = useState('')
  const [importing, setImporting] = useState(false)
  const canImport = ['SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'].includes(userRole)
  useEffect(() => { api.get('/evidence/').then(r => setRows(r.data.results || r.data)) }, [])
  useEffect(() => { api.get('/auth/me/').then(r => setUserRole(r.data.role)).catch(() => setUserRole(null)) }, [])
  async function upload(e) {
    e.preventDefault()
    if (!file || !title) return
    const form = new FormData()
    form.append('title', title); form.append('file', file)
    form.append('category', 'Accreditation'); form.append('department', '1'); form.append('academic_year', '1')
    await api.post('/evidence/', form)
    setTitle(''); setFile(null)
    const r = await api.get('/evidence/'); setRows(r.data.results || r.data)
  }
  async function downloadEvidence(row) {
    const response = await api.get(`/evidence/${row.id}/download/`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = row.title || 'evidence-document'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }
  async function downloadImportTemplate() {
    setImportError('')
    try {
      const response = await api.get('/bulk-import/evidence/template/', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = 'evidence_import_template.xlsx'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      setImportError(e.response?.data?.detail || 'Unable to download the Excel template.')
    }
  }
  async function importEvidence(e) {
    e.preventDefault()
    setImportError('')
    setImportSuccess('')
    if (!importWorkbook) {
      setImportError('Choose an .xlsx workbook to import.')
      return
    }
    const body = new FormData()
    body.append('file', importWorkbook)
    importDocuments.forEach(document => body.append('documents', document))
    setImporting(true)
    try {
      const response = await api.post('/bulk-import/evidence/', body)
      setImportSuccess(response.data.detail)
      setImportWorkbook(null)
      setImportDocuments([])
      const result = await api.get('/evidence/')
      setRows(result.data.results || result.data)
    } catch (e) {
      const data = e.response?.data
      const rowErrors = data?.errors?.map(item =>
        `Row ${item.row}: ${Object.entries(item.errors).map(([field, message]) => `${field}: ${message}`).join(', ')}`
      )
      setImportError(rowErrors?.length
        ? `${data.detail}\n${rowErrors.join('\n')}`
        : typeof data?.detail === 'string' ? data.detail : JSON.stringify(data || 'Unable to import evidence'))
    } finally {
      setImporting(false)
    }
  }
  return (
    <div className="page"><div className="page-heading"><div><p className="eyebrow">DOCUMENT REPOSITORY</p><h1>Evidence Library</h1></div>
      {canImport && <button className="secondary-btn compact" onClick={() => setImportOpen(value => !value)}><Upload size={16} /> Import Excel</button>}</div>
      {importOpen && canImport && <article className="panel student-import-panel">
        <div className="student-import-heading"><div><h3>Import evidence records</h3><p>Upload an Excel workbook and one matching document for every evidence row. Maximum 10 MB per file and 50 MB total.</p></div>
          <button type="button" className="text-action" onClick={downloadImportTemplate}><Download size={15} /> Download template</button></div>
        <form className="student-import-form" onSubmit={importEvidence}>
          <label>Excel workbook (.xlsx)<input type="file" accept=".xlsx" onChange={e => setImportWorkbook(e.target.files?.[0] || null)} required /></label>
          <label>Evidence documents<input type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx" onChange={e => setImportDocuments(Array.from(e.target.files || []))} required /></label>
          <button className="primary-btn compact" type="submit" disabled={importing}>{importing ? 'Importing...' : 'Import evidence'}</button>
        </form>
        {importError && <div className="alert-error" style={{ whiteSpace: 'pre-wrap' }}>{importError}</div>}
        {importSuccess && <div className="notice">{importSuccess}</div>}
      </article>}
      <article className="panel evidence-upload"><form onSubmit={upload}>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Document title" />
        <input type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx" onChange={e => setFile(e.target.files[0])} />
        <button className="primary-btn compact" type="submit"><Plus size={17} /> Upload Evidence</button>
      </form></article>
      <article className="panel table-panel"><div className="table-wrap"><table>
        <thead><tr><th>Title</th><th>Category</th><th>Version</th><th>Action</th></tr></thead>
        <tbody>{rows.map(r => <tr key={r.id}><td>{r.title}</td><td>{r.category}</td><td>v{r.version}</td><td><button className="text-action" onClick={() => downloadEvidence(r)}>Download</button></td></tr>)}</tbody>
      </table>{!rows.length && <div className="empty">No evidence uploaded</div>}</div></article>
    </div>
  )
}

function Submissions() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [userRole, setUserRole] = useState(null)
  const [importOpen, setImportOpen] = useState(false)
  const [importFile, setImportFile] = useState(null)
  const [importError, setImportError] = useState('')
  const [importSuccess, setImportSuccess] = useState('')
  const [importing, setImporting] = useState(false)
  const [searchParams] = useSearchParams()
  const institutionId = localStorage.getItem('dashboard_institution') || searchParams.get('institution')
  const canImport = ['SUPER_ADMIN', 'INSTITUTIONAL_ADMIN'].includes(userRole)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const r = await api.get('/submissions/', {
        params: institutionId ? { department__institution: institutionId } : {},
      })
      setRows(Array.isArray(r.data) ? r.data : r.data.results || [])
    } catch (e) {
      setError(e.response?.data?.detail || 'Unable to load submissions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [institutionId])
  useEffect(() => { api.get('/auth/me/').then(r => setUserRole(r.data.role)).catch(() => setUserRole(null)) }, [])
  async function action(row, decision) {
    if (decision === 'review') {
      await api.post(`/submissions/${row.id}/review/`, { decision: 'UNDER_REVIEW', comments: 'Reviewed from the portal.' })
    } else if (decision === 'verify') {
      await api.post(`/submissions/${row.id}/review/`, { decision: 'VERIFIED', comments: 'Evidence verified.' })
    } else {
      await api.post(`/submissions/${row.id}/${decision}/`)
    }
    await load()
  }
  async function downloadImportTemplate() {
    setImportError('')
    try {
      const response = await api.get('/bulk-import/submissions/template/', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = 'submissions_import_template.xlsx'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      setImportError(e.response?.data?.detail || 'Unable to download the Excel template.')
    }
  }
  async function importSubmissions(e) {
    e.preventDefault()
    setImportError('')
    setImportSuccess('')
    if (!importFile) {
      setImportError('Choose an .xlsx workbook to import.')
      return
    }
    const body = new FormData()
    body.append('file', importFile)
    setImporting(true)
    try {
      const response = await api.post('/bulk-import/submissions/', body)
      setImportSuccess(response.data.detail)
      setImportFile(null)
      await load()
    } catch (e) {
      const data = e.response?.data
      const rowErrors = data?.errors?.map(item =>
        `Row ${item.row}: ${Object.entries(item.errors).map(([field, message]) => `${field}: ${message}`).join(', ')}`
      )
      setImportError(rowErrors?.length
        ? `${data.detail}\n${rowErrors.join('\n')}`
        : typeof data?.detail === 'string' ? data.detail : JSON.stringify(data || 'Unable to import submissions'))
    } finally {
      setImporting(false)
    }
  }
  return (
    <div className="page"><div className="page-heading"><div><p className="eyebrow">WORKFLOW</p><h1>Submission Management</h1></div>
      {canImport && <button className="secondary-btn compact" onClick={() => setImportOpen(value => !value)}><Upload size={16} /> Import Excel</button>}</div>
      {importOpen && canImport && <article className="panel student-import-panel">
        <div className="student-import-heading"><div><h3>Import submissions</h3><p>Imported submissions are created as drafts; submit them through the normal review and approval workflow.</p></div>
          <button type="button" className="text-action" onClick={downloadImportTemplate}><Download size={15} /> Download template</button></div>
        <form className="student-import-form" onSubmit={importSubmissions}>
          <label>Excel workbook (.xlsx)<input type="file" accept=".xlsx" onChange={e => setImportFile(e.target.files?.[0] || null)} required /></label>
          <button className="primary-btn compact" type="submit" disabled={importing}>{importing ? 'Importing...' : 'Import submissions'}</button>
        </form>
        {importError && <div className="alert-error" style={{ whiteSpace: 'pre-wrap' }}>{importError}</div>}
        {importSuccess && <div className="notice">{importSuccess}</div>}
      </article>}
      {error && <div className="alert-error">{error}</div>}
      <article className="panel table-panel"><div className="table-wrap"><table>
        <thead><tr><th>Title</th><th>Status</th><th>Evidence</th><th>Actions</th></tr></thead>
        <tbody>{loading ? <tr><td colSpan="4" className="empty">Loading submissions...</td></tr> : rows.map(r => <tr key={r.id}><td>{r.title}</td><td><span className={`status status-${String(r.status).toLowerCase()}`}>{String(r.status).replaceAll('_', ' ')}</span></td><td>{r.evidence_count}</td>
          <td><div className="row-actions">
            {r.status === 'DRAFT' && <button onClick={() => action(r, 'submit')}>Submit</button>}
            {r.status === 'SUBMITTED' && <button onClick={() => action(r, 'review')}>Review</button>}
            {r.status === 'UNDER_REVIEW' && <button onClick={() => action(r, 'verify')}>Verify</button>}
            {r.status === 'VERIFIED' && <button onClick={() => action(r, 'approve')}>Approve</button>}
          </div></td></tr>)}</tbody>
      </table>      {!loading && !error && !rows.length && <div className="empty">No submissions found</div>}</div></article>
    </div>
  )
}

function Notifications() {
  const [rows, setRows] = useState([])
  useEffect(() => { api.get('/notifications/').then(r => setRows(r.data.results || r.data)) }, [])
  async function read(row) { await api.post(`/notifications/${row.id}/read/`); setRows(rows.map(r => r.id === row.id ? {...r, is_read: true} : r)) }
  return <div className="page"><div className="page-heading"><div><p className="eyebrow">INBOX</p><h1>Notifications</h1></div></div>
    <section className="notification-list">{rows.map(r => <article className={r.is_read ? 'notification' : 'notification unread'} key={r.id}>
      <Bell size={18} /><div><strong>{r.title}</strong><p>{r.message}</p></div>{!r.is_read && <button onClick={() => read(r)}>Mark read</button>}
    </article>)}</section></div>
}

function Reports() {
  const [type, setType] = useState('institutional')
  const [format, setFormat] = useState('xlsx')
  const [department, setDepartment] = useState('')
  const [academicYear, setAcademicYear] = useState('')
  const [status, setStatus] = useState('')
  const [departments, setDepartments] = useState([])
  const [academicYears, setAcademicYears] = useState([])
  const [generating, setGenerating] = useState(false)
  const [message, setMessage] = useState('')
  useEffect(() => {
    api.get('/departments/?page_size=100').then(r => setDepartments(r.data.results || r.data))
    api.get('/academic-years/?page_size=100').then(r => setAcademicYears(r.data.results || r.data))
  }, [])
  async function generate() {
    setGenerating(true)
    setMessage('')
    try {
      const response = await api.get('/report-download/', {
        params: { type, format, department, academic_year: academicYear, status },
        responseType: 'blob',
      })
      const disposition = response.headers['content-disposition'] || ''
      const match = disposition.match(/filename="?([^";]+)"?/)
      const filename = match?.[1] || `${type}-report.${format}`
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      setMessage(`Report downloaded: ${filename}`)
    } catch (error) {
      setMessage(error.response?.status === 401
        ? 'Please sign in again before generating a report.'
        : 'The report could not be generated. Please try again.')
    } finally {
      setGenerating(false)
    }
  }
  return <div className="page"><div className="page-heading"><div><p className="eyebrow">ANALYTICS</p><h1>Reports & Exports</h1></div></div>
    <article className="panel report-panel"><label>Report type<select value={type} onChange={e => setType(e.target.value)}>
      <option value="institutional">Institutional</option><option value="faculty">Faculty</option><option value="student">Student</option><option value="accreditation">Accreditation</option>
      <option value="placement">Placement</option><option value="research">Research</option>
    </select></label><label>Department<select value={department} onChange={e => setDepartment(e.target.value)}><option value="">All departments</option>{departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
    <label>Academic year<select value={academicYear} onChange={e => setAcademicYear(e.target.value)}><option value="">All academic years</option>{academicYears.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}</select></label>
    {type === 'accreditation' && <label>Status<select value={status} onChange={e => setStatus(e.target.value)}><option value="">All statuses</option>{['DRAFT','SUBMITTED','UNDER_REVIEW','CORRECTION_REQUIRED','VERIFIED','APPROVED'].map(s => <option key={s} value={s}>{s.replaceAll('_',' ')}</option>)}</select></label>}
    <label>Export format<select value={format} onChange={e => setFormat(e.target.value)}><option value="xlsx">Excel (.xlsx)</option><option value="pdf">PDF</option></select></label>
    <button className="primary-btn" onClick={generate} disabled={generating}>
      <BarChart3 size={17} /> {generating ? 'Generating...' : 'Generate Report'}
    </button>
    {message && <p className="report-message">{message}</p>}
    </article></div>
}

function ProfileSettings() {
  const [profile, setProfile] = useState({ first_name: '', last_name: '', email: '', phone: '' })
  const [password, setPassword] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [message, setMessage] = useState('')
  useEffect(() => { api.get('/auth/me/').then(r => setProfile({
    first_name: r.data.first_name || '', last_name: r.data.last_name || '',
    email: r.data.email || '', phone: r.data.phone || '',
  })) }, [])
  async function saveProfile(e) {
    e.preventDefault()
    await api.patch('/auth/profile/', profile)
    setMessage('Profile updated successfully.')
  }
  async function savePassword(e) {
    e.preventDefault()
    if (password.new_password !== password.confirm_password) {
      setMessage('New passwords do not match.')
      return
    }
    try {
      await api.post('/auth/change-password/', password)
      setPassword({ old_password: '', new_password: '', confirm_password: '' })
      setMessage('Password changed successfully.')
    } catch (e) {
      setMessage(JSON.stringify(e.response?.data || 'Unable to change password'))
    }
  }
  return <div className="page"><div className="page-heading"><div><p className="eyebrow">ACCOUNT</p><h1>Profile & Settings</h1></div></div>
    {message && <div className="notice">{message}</div>}
    <div className="settings-grid">
      <form className="panel settings-card" onSubmit={saveProfile}><h3>Personal Profile</h3>
        <label>First name<input value={profile.first_name} onChange={e => setProfile({...profile, first_name: e.target.value})} /></label>
        <label>Last name<input value={profile.last_name} onChange={e => setProfile({...profile, last_name: e.target.value})} /></label>
        <label>Email<input type="email" value={profile.email} onChange={e => setProfile({...profile, email: e.target.value})} /></label>
        <label>Phone<input value={profile.phone} onChange={e => setProfile({...profile, phone: e.target.value})} /></label>
        <button className="primary-btn">Save Profile</button>
      </form>
      <form className="panel settings-card" onSubmit={savePassword}><h3>Change Password</h3>
        <label>Current password<input type="password" value={password.old_password} onChange={e => setPassword({...password, old_password: e.target.value})} required /></label>
        <label>New password<input type="password" value={password.new_password} onChange={e => setPassword({...password, new_password: e.target.value})} required /></label>
        <label>Confirm password<input type="password" value={password.confirm_password} onChange={e => setPassword({...password, confirm_password: e.target.value})} required /></label>
        <button className="primary-btn">Change Password</button>
      </form>
    </div>
  </div>
}

function Audit() {
  return <GenericList endpoint="audit" title="Audit History" fields={[
    { key: 'action', label: 'Action' }, { key: 'module', label: 'Module' },
    { key: 'record_reference', label: 'Record' }, { key: 'timestamp', label: 'Timestamp' },
  ]} />
}

function Layout() {
  const [open, setOpen] = useState(false)
  const [user, setUser] = useState(null)
  const navigate = useNavigate()
  useEffect(() => { api.get('/auth/me/').then(r => setUser(r.data)).catch(() => navigate('/login')) }, [navigate])
  function logout() { localStorage.clear(); navigate('/login') }
  return (
    <div className="app-shell">
      <aside className={open ? 'sidebar open' : 'sidebar'}>
        <div className="sidebar-brand"><div className="brand-mark small">A</div><div><strong>AIMS</strong><span>Accreditation Portal</span></div></div>
        <nav>{nav.filter(([label]) => {
          if (!user) return true
          if (user.role === 'MANAGEMENT_VIEWER') return ['Dashboard','Reports','Notifications','Profile','Audit History'].includes(label)
          if (user.role === 'FACULTY_STAFF') return !['Users','Audit History','Institutions','Departments','Programmes','Courses'].includes(label)
          if (user.role === 'REVIEWER_VERIFIER') return !['Users','Audit History','Institutions','Departments','Programmes','Courses'].includes(label)
          return true
        }).map(([label, path, Icon]) => <NavLink key={path} to={path} end={path === '/'} onClick={() => setOpen(false)}>
          <Icon size={18} /><span>{label}</span>
        </NavLink>)}</nav>
      </aside>
      <div className="main-area">
        <header className="topbar"><button className="menu-btn" onClick={() => setOpen(!open)}><Menu size={21} /></button>
          <div className="top-search"><Search size={17} /><span>Search institution records...</span></div>
          <div className="top-actions"><button className="icon-btn" onClick={() => navigate('/notifications')}><Bell size={19} /></button>
            <button className="profile"><div className="avatar">{(user?.first_name?.[0] || user?.username?.[0] || 'U').toUpperCase()}
            </div><div><strong>{user?.first_name || user?.username}</strong><span>{user?.role?.replaceAll('_', ' ')}</span></div></button>
            <button className="icon-btn" title="Logout" onClick={logout}><LogOut size={19} /></button>
          </div>
        </header>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard/:institutionId" element={<Dashboard />} />
          <Route path="/institutions" element={<GenericList endpoint="institutions" title="Institutions" fields={[
            {key:'name',label:'Institution'}, {key:'code',label:'Code'}, {key:'email',label:'Email'}, {key:'phone',label:'Phone'}]}
            formFields={[
              {name:'name',label:'Institution name',required:true},
              {name:'code',label:'Institution code',required:true},
              {name:'address',label:'Address',textarea:true},
              {name:'website',label:'Website',type:'url'},
              {name:'email',label:'Email',type:'email'},
              {name:'phone',label:'Phone'},
            ]} />} />
          <Route path="/academic-years" element={<GenericList endpoint="academic-years" title="Academic Years" fields={[
            {key:'name',label:'Academic Year'}, {key:'start_date',label:'Start Date'}, {key:'end_date',label:'End Date'}, {key:'is_current',label:'Current'}]}
            formFields={[
              {name:'name',label:'Academic year',required:true},
              {name:'start_date',label:'Start date',required:true,type:'date'},
              {name:'end_date',label:'End date',required:true,type:'date'},
            ]} />} />
          <Route path="/facilities" element={<GenericList endpoint="facilities" title="Institutional Facilities" fields={[
            {key:'name',label:'Facility'}, {key:'facility_type',label:'Type'}, {key:'location',label:'Location'}, {key:'capacity',label:'Capacity'}]}
            formFields={[
              {name:'institution',label:'Institution ID',required:true,type:'number'},
              {name:'name',label:'Facility name',required:true},
              {name:'facility_type',label:'Facility type',required:true},
              {name:'location',label:'Location'},
              {name:'capacity',label:'Capacity',type:'number'},
              {name:'description',label:'Description',textarea:true},
            ]} />} />
          <Route path="/departments" element={<GenericList endpoint="departments" title="Departments" fields={[
            {key:'name',label:'Department'}, {key:'code',label:'Code'}, {key:'head',label:'Head'}, {key:'is_active',label:'Status'}]}
            formFields={[
              {name:'institution',label:'Institution',required:true},
              {name:'name',label:'Department name',required:true},
              {name:'code',label:'Department code',required:true},
              {name:'head',label:'Department head'},
            ]} institutionFilter="institution" />} />
          <Route path="/programmes" element={<GenericList endpoint="programmes" title="Academic Programmes" fields={[
            {key:'name',label:'Programme'}, {key:'code',label:'Code'}, {key:'duration_years',label:'Duration'}, {key:'is_active',label:'Active'}]}
            formFields={[
              {name:'department',label:'Department ID',required:true,type:'number'},
              {name:'name',label:'Programme name',required:true},
              {name:'code',label:'Programme code',required:true},
              {name:'duration_years',label:'Duration (years)',required:true,type:'number'},
            ]} institutionFilter="department__institution" />} />
          <Route path="/courses" element={<GenericList endpoint="courses" title="Courses" fields={[
            {key:'name',label:'Course'}, {key:'code',label:'Code'}, {key:'credits',label:'Credits'}, {key:'semester',label:'Semester'}]}
            formFields={[
              {name:'programme',label:'Programme ID',required:true,type:'number'},
              {name:'name',label:'Course name',required:true},
              {name:'code',label:'Course code',required:true},
              {name:'credits',label:'Credits',required:true,type:'number'},
              {name:'semester',label:'Semester',required:true,type:'number'},
            ]} />} />
          <Route path="/faculty" element={<GenericList endpoint="faculty" title="Faculty" fields={[
            {key:'faculty_id',label:'Faculty ID'}, {key:'full_name',label:'Name'}, {key:'email',label:'Email'}, {key:'designation',label:'Designation'}]}
            formFields={[
              {name:'faculty_id',label:'Faculty ID',required:true},{name:'full_name',label:'Full name',required:true},
              {name:'email',label:'Email',required:true,type:'email'}, {name:'phone',label:'Phone'},
              {name:'department',label:'Department ID',required:true,type:'number'}, {name:'designation',label:'Designation',required:true},
              {name:'qualification',label:'Qualification',required:true}, {name:'experience_years',label:'Experience',type:'number'},
              {name:'joining_date',label:'Joining date',required:true,type:'date'}, {name:'specialization',label:'Specialization'},
            ]} institutionFilter="department__institution" />} />
          <Route path="/students" element={<GenericList endpoint="students" title="Students" fields={[
            {key:'student_id',label:'Student ID'}, {key:'roll_number',label:'Roll Number'}, {key:'full_name',label:'Name'}, {key:'email',label:'Email'}]}
            formFields={[
              {name:'student_id',label:'Student ID',required:true},{name:'roll_number',label:'Roll number',required:true},
              {name:'full_name',label:'Full name',required:true},{name:'email',label:'Email',required:true,type:'email'},
              {name:'department',label:'Department ID',required:true,type:'number'}, {name:'programme',label:'Programme ID',required:true,type:'number'},
              {name:'academic_year',label:'Academic year ID',required:true,type:'number'}, {name:'admission_year',label:'Admission year',required:true,type:'number'},
            ]} institutionFilter="department__institution" currentUserRole={user?.role} />} />
          <Route path="/research" element={<GenericList endpoint="research-projects" title="Research Projects" fields={[
            {key:'title',label:'Project'}, {key:'funding_agency',label:'Funding Agency'}, {key:'funding_amount',label:'Amount'}, {key:'status',label:'Status'}]} />} />
          <Route path="/placements" element={<GenericList endpoint="placements" title="Placements" fields={[
            {key:'company',label:'Company'}, {key:'position',label:'Position'}, {key:'package_lpa',label:'Package (LPA)'}, {key:'placement_date',label:'Date'}]} />} />
          <Route path="/frameworks" element={<GenericList endpoint="frameworks" title="Accreditation Frameworks" fields={[
            {key:'name',label:'Framework'}, {key:'code',label:'Code'}, {key:'version',label:'Version'}, {key:'is_active',label:'Active'}]}
            formFields={[
              {name:'name',label:'Framework name',required:true},{name:'code',label:'Framework code',required:true},
              {name:'description',label:'Description',textarea:true},{name:'version',label:'Version',required:true},
            ]} />} />
          <Route path="/criteria" element={<GenericList endpoint="criteria" title="Accreditation Criteria" fields={[
            {key:'code',label:'Code'}, {key:'title',label:'Criterion'}, {key:'weight',label:'Weight'}]}
            formFields={[
              {name:'framework',label:'Framework ID',required:true,type:'number'}, {name:'code',label:'Criterion code',required:true},
              {name:'title',label:'Criterion title',required:true}, {name:'description',label:'Description',textarea:true},
              {name:'weight',label:'Weight',type:'number'},
            ]} />} />
          <Route path="/parameters" element={<GenericList endpoint="parameters" title="Accreditation Parameters" fields={[
            {key:'code',label:'Code'}, {key:'title',label:'Parameter'}, {key:'deadline',label:'Deadline'}]}
            formFields={[
              {name:'criterion',label:'Criterion ID',required:true,type:'number'}, {name:'code',label:'Parameter code',required:true},
              {name:'title',label:'Parameter title',required:true}, {name:'description',label:'Description',textarea:true},
              {name:'required_information',label:'Required information',textarea:true}, {name:'department',label:'Department ID',type:'number'},
              {name:'academic_year',label:'Academic year ID',type:'number'}, {name:'deadline',label:'Deadline',type:'date'},
            ]} />} />
          <Route path="/publications" element={<GenericList endpoint="publications" title="Publications" fields={[
            {key:'title',label:'Publication'}, {key:'publication_type',label:'Type'}, {key:'publication_date',label:'Date'}, {key:'doi_or_reference',label:'DOI/Reference'}]}
            formFields={[
              {name:'title',label:'Title',required:true},{name:'authors',label:'Authors',required:true},
              {name:'department',label:'Department ID',required:true,type:'number'}, {name:'publication_type',label:'Publication type',required:true},
              {name:'publication_date',label:'Publication date',required:true,type:'date'}, {name:'academic_year',label:'Academic year ID',required:true,type:'number'},
              {name:'doi_or_reference',label:'DOI or reference'},
            ]} />} />
          <Route path="/users" element={<GenericList endpoint="users" title="Users" fields={[
            {key:'username',label:'Username'}, {key:'email',label:'Email'}, {key:'role',label:'Role'}, {key:'is_active',label:'Active'}]}
            formFields={[
              {name:'username',label:'Username',required:true},{name:'email',label:'Email',required:true,type:'email'},
              {name:'first_name',label:'First name'}, {name:'last_name',label:'Last name'},
              {name:'role',label:'Role',required:true,type:'select',options:[
                {value:'SUPER_ADMIN',label:'Super Admin'}, {value:'INSTITUTIONAL_ADMIN',label:'Institutional Admin'},
                {value:'ACCREDITATION_COORDINATOR',label:'Accreditation Coordinator'}, {value:'DEPARTMENT_ADMIN',label:'Department Admin'},
                {value:'FACULTY_STAFF',label:'Faculty/Staff'}, {value:'REVIEWER_VERIFIER',label:'Reviewer/Verifier'},
                {value:'MANAGEMENT_VIEWER',label:'Management Viewer'},
              ]}, {name:'password',label:'Password',type:'password'},
            ]} />} />
          <Route path="/evidence" element={<Evidence />} />
          <Route path="/submissions" element={<Submissions />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/profile" element={<ProfileSettings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  )
}

export default function App() {
  return <BrowserRouter><Routes>
    <Route path="/student-login" element={<StudentAuth />} />
    <Route path="/student-register" element={<StudentAuth />} />
    <Route path="/student/portal" element={<StudentProtected><StudentPortal /></StudentProtected>} />
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route path="/*" element={<Protected><Layout /></Protected>} />
  </Routes></BrowserRouter>
}
