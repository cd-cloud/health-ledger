import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Activity, AlertCircle, TrendingUp } from 'lucide-react'

import { listReports } from '../api/reports'
import { listBiomarkers, getAbnormalSummary } from '../api/biomarkers'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import type { Report, Biomarker, BiomarkerValue } from '../types'

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    parsed: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
  }
  const labels: Record<string, string> = {
    pending: '待解析',
    parsed: '已解析',
    error: '失败',
  }
  return <span className={`badge ${styles[status] ?? 'bg-gray-100 text-gray-800'}`}>{labels[status] ?? status}</span>
}

export default function Dashboard() {
  const [reports, setReports] = useState<Report[]>([])
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([])
  const [abnormal, setAbnormal] = useState<BiomarkerValue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [reportsRes, biomarkersRes, abnormalRes] = await Promise.all([
        listReports(),
        listBiomarkers(),
        getAbnormalSummary(),
      ])
      setReports(reportsRes.items)
      setBiomarkers(biomarkersRes)
      setAbnormal(abnormalRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载概览数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <LoadingSpinner message="加载概览数据..." />
  if (error) return <ErrorState title="概览加载失败" error={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">概览</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-full text-primary">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500">报告总数</p>
            <p className="text-2xl font-bold">{reports.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-full text-success">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500">指标种类</p>
            <p className="text-2xl font-bold">{biomarkers.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-red-100 rounded-full text-danger">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500">最新异常</p>
            <p className="text-2xl font-bold">{abnormal.length}</p>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="p-3 bg-purple-100 rounded-full text-purple-700">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500">可趋势分析</p>
            <p className="text-2xl font-bold">{biomarkers.filter((b) => abnormal.some((a) => a.biomarker.code === b.code)).length}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">最近报告</h3>
            <Link to="/reports" className="text-sm text-primary hover:underline">
              查看全部
            </Link>
          </div>
          {reports.length === 0 ? (
            <EmptyState
              title="暂无报告"
              description="请先上传体检报告。"
              action={
                <Link to="/upload" className="btn-primary">
                  上传报告
                </Link>
              }
            />
          ) : (
            <ul className="divide-y divide-gray-100">
              {reports.slice(0, 5).map((report) => (
                <li key={report.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{report.original_name}</p>
                    <p className="text-xs text-gray-500">{report.report_date ? report.report_date.slice(0, 10) : '未填写日期'}</p>
                  </div>
                  <StatusBadge status={report.status} />
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">最新异常指标</h3>
            <Link to="/abnormal" className="text-sm text-primary hover:underline">
              查看全部
            </Link>
          </div>
          {abnormal.length === 0 ? (
            <EmptyState title="暂无异常指标" description="暂无已校对的异常指标记录。" />
          ) : (
            <ul className="divide-y divide-gray-100">
              {abnormal.slice(0, 5).map((value) => (
                <li key={value.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{value.biomarker.name}</p>
                    <p className="text-xs text-gray-500">
                      {value.value} {value.unit}（参考 {value.reference_low ?? '-'} - {value.reference_high ?? '-'}）
                    </p>
                  </div>
                  <span className={`badge ${value.status === 'high' ? 'badge-high' : 'badge-low'}`}>
                    {value.status === 'high' ? '偏高' : '偏低'}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
