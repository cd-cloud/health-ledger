import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Trash2, RefreshCw, Download } from 'lucide-react'

import { listReports, deleteReport, parseReport, exportReportsArchive } from '../api/reports'
import { downloadBlob } from '../utils/download'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import type { Report } from '../types'

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

export default function ReportList() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const res = await listReports()
      setReports(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载报告列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleDelete(id: number) {
    if (!confirm('确定删除该报告？原始 PDF 也将被删除。')) return
    try {
      await deleteReport(id)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : '删除失败')
    }
  }

  async function handleParse(id: number) {
    try {
      await parseReport(id)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : '解析失败')
    }
  }

  async function handleExport() {
    setExporting(true)
    try {
      const blob = await exportReportsArchive()
      const timestamp = new Date().toISOString().slice(0, 10)
      downloadBlob(blob, `health_export_${timestamp}.zip`)
    } catch (err) {
      alert(err instanceof Error ? err.message : '导出失败')
    } finally {
      setExporting(false)
    }
  }

  if (loading) return <LoadingSpinner message="加载报告列表..." />
  if (error) return <ErrorState title="报告列表加载失败" error={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">报告列表</h2>
        <div className="flex items-center gap-3">
          {reports.length > 0 && (
            <button
              onClick={handleExport}
              disabled={exporting}
              className="btn-secondary inline-flex items-center gap-2"
              title="导出全部报告"
            >
              <Download className="w-4 h-4" />
              {exporting ? '导出中...' : '导出全部'}
            </button>
          )}
          <Link to="/upload" className="btn-primary">
            上传报告
          </Link>
        </div>
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
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">文件名</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">报告日期</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">上传时间</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <Link to={`/reports/${report.id}`} className="text-primary hover:underline">
                      {report.original_name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.report_date ? report.report_date.slice(0, 10) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={report.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      {report.status !== 'parsed' && (
                        <button
                          onClick={() => handleParse(report.id)}
                          className="p-1 text-gray-500 hover:text-primary"
                          title="重新解析"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(report.id)}
                        className="p-1 text-gray-500 hover:text-danger"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
