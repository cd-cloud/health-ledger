import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  Activity,
  AlertCircle,
  LogOut,
} from 'lucide-react'

import { useAuth } from './contexts/AuthContext'
import Dashboard from './pages/Dashboard'
import UploadReport from './pages/UploadReport'
import ReportList from './pages/ReportList'
import ReportDetail from './pages/ReportDetail'
import BiomarkerList from './pages/BiomarkerList'
import BiomarkerTrend from './pages/BiomarkerTrend'
import Login from './pages/Login'
import Register from './pages/Register'

function NavItem({ to, icon: Icon, children }: { to: string; icon: React.ElementType; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive ? 'bg-primary text-white' : 'text-gray-700 hover:bg-gray-100'
        }`
      }
    >
      <Icon className="w-4 h-4" />
      {children}
    </NavLink>
  )
}

function MainLayout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="w-full md:w-64 bg-white border-r border-gray-200 p-4">
        <div className="mb-6 px-4">
          <h1 className="text-lg font-bold text-gray-900">体检指标追踪</h1>
          <p className="text-xs text-gray-500">个人健康数据管理</p>
          {user && (
            <p className="mt-1 text-xs text-gray-400 truncate" title={user.username}>
              {user.username}
            </p>
          )}
        </div>
        <nav className="space-y-1">
          <NavItem to="/" icon={LayoutDashboard}>
            概览
          </NavItem>
          <NavItem to="/upload" icon={UploadCloud}>
            上传报告
          </NavItem>
          <NavItem to="/reports" icon={FileText}>
            报告列表
          </NavItem>
          <NavItem to="/biomarkers" icon={Activity}>
            指标列表
          </NavItem>
          <NavItem to="/abnormal" icon={AlertCircle}>
            异常指标
          </NavItem>
        </nav>
        <div className="mt-6 px-4">
          <button
            onClick={() => logout()}
            className="flex w-full items-center gap-2 rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
          >
            <LogOut className="w-4 h-4" />
            登出
          </button>
        </div>
      </aside>
      <main className="flex-1 p-4 md:p-8 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadReport />} />
          <Route path="/reports" element={<ReportList />} />
          <Route path="/reports/:id" element={<ReportDetail />} />
          <Route path="/biomarkers" element={<BiomarkerList />} />
          <Route path="/biomarkers/:code/trend" element={<BiomarkerTrend />} />
          <Route path="/abnormal" element={<BiomarkerList abnormalOnly />} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <Register />} />
      <Route path="/*" element={user ? <MainLayout /> : <Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App
