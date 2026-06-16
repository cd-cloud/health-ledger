import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Check, Save, Undo2, CheckSquare, Square } from 'lucide-react'

import { getReport, parseReport } from '../api/reports'
import { updateBiomarkerValue, batchUpdateBiomarkerValues } from '../api/biomarkers'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import type { ReportDetail, BiomarkerValue } from '../types'

interface UndoState {
  message: string
  items: { id: number; is_reviewed: boolean }[]
}

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<ReportDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [parsing, setParsing] = useState(false)
  const [savingId, setSavingId] = useState<number | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [undoStack, setUndoStack] = useState<UndoState[]>([])

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await getReport(Number(id))
      setReport(data)
      setSelectedIds(new Set())
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载报告详情失败')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  async function handleParse() {
    if (!report) return
    setParsing(true)
    try {
      await parseReport(report.id)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : '解析失败')
    } finally {
      setParsing(false)
    }
  }

  async function handleReview(value: BiomarkerValue) {
    setSavingId(value.id)
    try {
      await updateBiomarkerValue(value.id, { is_reviewed: !value.is_reviewed })
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : '操作失败')
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
    } catch (err) {
      alert(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSavingId(null)
    }
  }

  function toggleSelection(valueId: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(valueId)) {
        next.delete(valueId)
      } else {
        next.add(valueId)
      }
      return next
    })
  }

  function toggleSelectAll() {
    if (!report) return
    if (selectedIds.size === report.values.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(report.values.map((v) => v.id)))
    }
  }

  async function batchReview(reviewed: boolean) {
    if (!report || selectedIds.size === 0) return

    const previousStates = report.values
      .filter((v) => selectedIds.has(v.id))
      .map((v) => ({ id: v.id, is_reviewed: v.is_reviewed }))

    const items = Array.from(selectedIds).map((valueId) => ({ id: valueId, is_reviewed: reviewed }))

    try {
      await batchUpdateBiomarkerValues(items)
      setUndoStack((prev) => [
        ...prev,
        {
          message: `批量${reviewed ? '校对' : '取消校对'} ${items.length} 项指标`,
          items: previousStates,
        },
      ])
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : '批量操作失败')
    }
  }

  async function handleUndo() {
    if (undoStack.length === 0 || !report) return

    const lastAction = undoStack[undoStack.length - 1]
    try {
      await batchUpdateBiomarkerValues(lastAction.items)
      setUndoStack((prev) => prev.slice(0, -1))
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : '撤销失败')
    }
  }

  if (loading) return <LoadingSpinner message="加载报告详情..." />
  if (error) return <ErrorState title="报告详情加载失败" error={error} onRetry={load} />
  if (!report) return <ErrorState title="报告不存在" error="无法找到该报告。" />

  const allSelected = report.values.length > 0 && selectedIds.size === report.values.length

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
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
          <h3 className="text-lg font-semibold">提取指标（人工校对）</h3>
          {report.values.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={toggleSelectAll}
                className="btn-secondary text-xs"
                title={allSelected ? '取消全选' : '全选'}
              >
                {allSelected ? <CheckSquare className="w-4 h-4 mr-1" /> : <Square className="w-4 h-4 mr-1" />}
                {allSelected ? '取消全选' : '全选'}
              </button>
              <button
                onClick={() => batchReview(true)}
                disabled={selectedIds.size === 0}
                className="btn-primary text-xs disabled:opacity-50"
              >
                <Check className="w-4 h-4 mr-1" />
                批量校对
              </button>
              <button
                onClick={() => batchReview(false)}
                disabled={selectedIds.size === 0}
                className="btn-secondary text-xs disabled:opacity-50"
              >
                <Square className="w-4 h-4 mr-1" />
                批量取消
              </button>
              <button
                onClick={handleUndo}
                disabled={undoStack.length === 0}
                className="btn-secondary text-xs disabled:opacity-50"
              >
                <Undo2 className="w-4 h-4 mr-1" />
                撤销{undoStack.length > 0 ? ` (${undoStack.length})` : ''}
              </button>
            </div>
          )}
        </div>

        {report.values.length === 0 ? (
          <EmptyState
            title="暂无指标数据"
            description="当前报告没有提取到指标。"
            action={
              report.status !== 'parsed' && (
                <button onClick={handleParse} className="btn-primary">
                  立即解析
                </button>
              )
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={toggleSelectAll}
                      className="rounded border-gray-300 text-primary focus:ring-primary"
                    />
                  </th>
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
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(value.id)}
                        onChange={() => toggleSelection(value.id)}
                        className="rounded border-gray-300 text-primary focus:ring-primary"
                      />
                    </td>
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
