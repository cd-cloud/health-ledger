import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, AlertCircle, Download } from 'lucide-react'

import { listBiomarkerValues, exportBiomarkerValues } from '../api/biomarkers'
import { downloadBlob } from '../utils/download'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import type { BiomarkerValue } from '../types'

function StatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="badge bg-gray-100 text-gray-800">未知</span>
  const styles: Record<string, string> = {
    normal: 'badge-normal',
    high: 'badge-high',
    low: 'badge-low',
  }
  const labels: Record<string, string> = {
    normal: '正常',
    high: '偏高',
    low: '偏低',
  }
  return <span className={`badge ${styles[status]}`}>{labels[status]}</span>
}

export default function BiomarkerList({ abnormalOnly = false }: { abnormalOnly?: boolean }) {
  const location = useLocation()
  const isAbnormalPage = location.pathname === '/abnormal' || abnormalOnly

  const [values, setValues] = useState<BiomarkerValue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const valuesRes = await listBiomarkerValues({
        abnormal_only: isAbnormalPage,
        reviewed_only: false,
      })
      setValues(valuesRes)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载指标列表失败')
    } finally {
      setLoading(false)
    }
  }, [isAbnormalPage])

  useEffect(() => {
    load()
  }, [load])

  const displayedValues = filterStatus
    ? values.filter((v) => v.status === filterStatus)
    : values

  async function handleExport(format: 'csv' | 'json') {
    setExporting(true)
    try {
      const blob = await exportBiomarkerValues(format, {
        abnormal_only: isAbnormalPage,
      })
      const extension = format === 'csv' ? 'csv' : 'json'
      downloadBlob(blob, `biomarker_values_${isAbnormalPage ? 'abnormal' : 'all'}.${extension}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : '导出失败')
    } finally {
      setExporting(false)
    }
  }

  if (loading) return <LoadingSpinner message="加载指标列表..." />
  if (error) return <ErrorState title="指标列表加载失败" error={error} onRetry={load} />

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-2">
          {isAbnormalPage && <AlertCircle className="w-6 h-6 text-danger" />}
          <h2 className="text-2xl font-bold text-gray-900">
            {isAbnormalPage ? '异常指标' : '指标列表'}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-500">状态筛选：</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="input w-32"
          >
            <option value="">全部</option>
            <option value="high">偏高</option>
            <option value="low">偏低</option>
            <option value="normal">正常</option>
          </select>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting || values.length === 0}
            className="btn-secondary text-xs disabled:opacity-50"
          >
            <Download className="w-4 h-4 mr-1" />
            CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            disabled={exporting || values.length === 0}
            className="btn-secondary text-xs disabled:opacity-50"
          >
            JSON
          </button>
        </div>
      </div>

      {displayedValues.length === 0 ? (
        <EmptyState
          title={isAbnormalPage ? '暂无异常指标' : '暂无指标记录'}
          description={
            isAbnormalPage
              ? '当前没有已校对的异常指标记录。'
              : '请先上传报告并完成解析。'
          }
          action={
            !isAbnormalPage && (
              <Link to="/upload" className="btn-primary">
                上传报告
              </Link>
            )
          }
        />
      ) : (
        <div className="card overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">指标</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">数值</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">参考范围</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">报告日期</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">校对</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">趋势</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displayedValues.map((value) => (
                <tr key={value.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {value.biomarker.name}
                    <p className="text-xs text-gray-500 font-normal">{value.biomarker.code}</p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {value.value} {value.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {value.reference_low ?? '-'} - {value.reference_high ?? '-'} {value.unit}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={value.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {value.report?.report_date ? value.report.report_date.slice(0, 10) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={value.is_reviewed ? 'text-green-600' : 'text-yellow-600'}>
                      {value.is_reviewed ? '已校对' : '未校对'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      to={`/biomarkers/${value.biomarker.code}/trend`}
                      className="inline-flex items-center gap-1 text-primary hover:underline"
                    >
                      <TrendingUp className="w-4 h-4" />
                      趋势
                    </Link>
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
