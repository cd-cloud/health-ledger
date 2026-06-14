import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, Save } from 'lucide-react'

import { getReport, parseReport } from '../api/reports'
import { updateBiomarkerValue } from '../api/biomarkers'
import type { ReportDetail, BiomarkerValue } from '../types'

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [parsing, setParsing] = useState(false)
  const [savingId, setSavingId] = useState<number | null>(null)

  async function load() {
    if (!id) return
    setLoading(true)
    const data = await getReport(Number(id))
    setReport(data)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [id])

  async function handleParse() {
    if (!report) return
    setParsing(true)
    try {
      await parseReport(report.id)
      await load()
    } finally {
      setParsing(false)
    }
  }

  async function handleReview(value: BiomarkerValue) {
    setSavingId(value.id)
    try {
      await updateBiomarkerValue(value.id, { is_reviewed: !value.is_reviewed })
      await load()
    } finally {
      setSavingId(null)
    }
  }

  async function handleValueChange(valueId: number, field: 'value' | 'status', newValue: string) {
    setSavingId(valueId)
    try {
      const payload =
        field === 'value'
          ? { value: Number(newValue) }
          : { status: newValue as 'normal' | 'high' | 'low' }
      await updateBiomarkerValue(valueId, payload)
      await load()
    } finally {
      setSavingId(null)
    }
  }

  if (loading) return <div className="text-gray-500">加载中...</div>
  if (!report) return <div className="text-gray-500">报告不存在</div>

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="btn-secondary">
        <ArrowLeft className="w-4 h-4 mr-1" />
        返回
      </button>

      <div className="card">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{report.original_name}</h2>
            <p className="text-sm text-gray-500 mt-1">
              报告日期：{report.report_date ? report.report_date.slice(0, 10) : '未填写'} · 状态：
              {report.status === 'parsed' ? '已解析' : report.status === 'pending' ? '待解析' : '失败'}
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleParse} disabled={parsing} className="btn-primary disabled:opacity-50">
              {parsing ? '解析中...' : '重新解析'}
            </button>
          </div>
        </div>
        {report.error_message && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded-md">{report.error_message}</div>
        )}
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">提取指标（人工校对）</h3>
        {report.values.length === 0 ? (
          <div className="text-gray-500">
            <p>暂无指标数据。</p>
            {report.status !== 'parsed' && (
              <button onClick={handleParse} className="text-primary hover:underline mt-2">
                立即解析
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">指标</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">原始值</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">标准值</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">参考范围</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">校对</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {report.values.map((value) => (
                  <tr key={value.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {value.biomarker.name}
                      <p className="text-xs text-gray-500 font-normal">
                        原文：{value.original_name ?? '-'} {value.original_value_text ?? ''} {value.original_unit ?? ''}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {value.original_value_text ?? '-'} {value.original_unit ?? ''}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <input
                        type="number"
                        step="any"
                        defaultValue={value.value}
                        onBlur={(e) => handleValueChange(value.id, 'value', e.target.value)}
                        className="input w-24"
                        disabled={savingId === value.id}
                      />
                      <span className="ml-2 text-gray-500">{value.unit}</span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <select
                        defaultValue={value.status ?? 'normal'}
                        onChange={(e) => handleValueChange(value.id, 'status', e.target.value)}
                        className="input w-28"
                        disabled={savingId === value.id}
                      >
                        <option value="normal">正常</option>
                        <option value="high">偏高</option>
                        <option value="low">偏低</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {value.reference_low ?? '-'} - {value.reference_high ?? '-'} {value.unit}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <button
                        onClick={() => handleReview(value)}
                        disabled={savingId === value.id}
                        className={`inline-flex items-center gap-1 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                          value.is_reviewed
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {value.is_reviewed ? (
                          <>
                            <Check className="w-3 h-3" />
                            已校对
                          </>
                        ) : (
                          <>
                            <Save className="w-3 h-3" />
                            确认
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
