import { Routes, Route, NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  Activity,
  AlertCircle,
} from 'lucide-react'

import Dashboard from './pages/Dashboard'
import UploadReport from './pages/UploadReport'
import ReportList from './pages/ReportList'
import ReportDetail from './pages/ReportDetail'
import BiomarkerList from './pages/BiomarkerList'
import BiomarkerTrend from './pages/BiomarkerTrend'

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

function App() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="w-full md:w-64 bg-white border-r border-gray-200 p-4">
        <div className="mb-6 px-4">
          <h1 className="text-lg font-bold text-gray-900">体检指标追踪</h1>
          <p className="text-xs text-gray-500">个人健康数据管理</p>
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

export default App
