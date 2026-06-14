import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, AlertCircle } from 'lucide-react'

import { listBiomarkerValues } from '../api/biomarkers'
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
  const [filterStatus, setFilterStatus] = useState<string>('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      const valuesRes = await listBiomarkerValues({
        abnormal_only: isAbnormalPage,
        reviewed_only: false,
      })
      setValues(valuesRes)
      setLoading(false)
    }
    load()
  }, [isAbnormalPage])

  const displayedValues = filterStatus
    ? values.filter((v) => v.status === filterStatus)
    : values

  if (loading) return <div className="text-gray-500">加载中...</div>

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
        </div>
      </div>

      {displayedValues.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">
            {isAbnormalPage ? '暂无异常指标记录。' : '暂无指标记录。'}
          </p>
        </div>
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
