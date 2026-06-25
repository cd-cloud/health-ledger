import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from 'recharts'
import { ArrowLeft, Sparkles } from 'lucide-react'

import { getTrend, analyzeTrend } from '../api/biomarkers'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorState from '../components/ErrorState'
import EmptyState from '../components/EmptyState'
import type { TrendData, TrendAnalysis } from '../types'

interface ChartPoint {
  date: string
  value: number
  status: string | null
}

function TrendDot(props: {
  cx?: number
  cy?: number
  payload?: ChartPoint
}) {
  const { cx, cy, payload } = props
  if (cx == null || cy == null || !payload) return null

  const color =
    payload.status === 'high'
      ? '#dc2626'
      : payload.status === 'low'
      ? '#d97706'
      : '#2563eb'

  return (
    <circle
      cx={cx}
      cy={cy}
      r={5}
      fill={color}
      stroke="#fff"
      strokeWidth={2}
    />
  )
}

export default function BiomarkerTrend() {
  const { code } = useParams<{ code: string }>()
  const [trend, setTrend] = useState<TrendData | null>(null)
  const [analysis, setAnalysis] = useState<TrendAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const load = useCallback(async () => {
    if (!code) return
    setLoading(true)
    setError(null)
    try {
      const data = await getTrend(code)
      setTrend(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载趋势数据失败')
    } finally {
      setLoading(false)
    }
  }, [code])

  useEffect(() => {
    load()
  }, [load])

  async function handleAnalyze() {
    if (!code) return
    setAnalyzing(true)
    try {
      const data = await analyzeTrend(code)
      setAnalysis(data)
    } catch (err) {
      alert(err instanceof Error ? err.message : '分析失败')
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) return <LoadingSpinner message="加载趋势数据..." />
  if (error) return <ErrorState title="趋势加载失败" error={error} onRetry={load} />
  if (!trend) return <ErrorState title="指标不存在" error="无法找到该指标的趋势数据。" />

  const chartData: ChartPoint[] = trend.points.map((p) => ({
    date: p.report_date ? p.report_date.slice(0, 10) : '未知日期',
    value: p.value,
    status: p.status,
  }))

  const hasReferenceRange =
    trend.biomarker.reference_low !== null && trend.biomarker.reference_high !== null

  return (
    <div className="space-y-6">
      <Link to="/biomarkers" className="btn-secondary">
        <ArrowLeft className="w-4 h-4 mr-1" />
        返回指标列表
      </Link>

      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900">{trend.biomarker.name} 趋势</h2>
        <p className="text-sm text-gray-500 mt-1">
          标准单位：{trend.biomarker.unit_standard} · 参考范围：
          {trend.biomarker.reference_low ?? '-'} - {trend.biomarker.reference_high ?? '-'}
        </p>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">历史趋势（仅已校对数据）</h3>
        {chartData.length === 0 ? (
          <EmptyState
            title="暂无趋势数据"
            description="暂无已校对数据用于趋势展示。请先上传报告并在报告详情页校对指标。"
          />
        ) : (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                {hasReferenceRange && (
                  <ReferenceArea
                    y1={trend.biomarker.reference_low ?? undefined}
                    y2={trend.biomarker.reference_high ?? undefined}
                    stroke="none"
                    fill="#22c55e"
                    fillOpacity={0.05}
                  />
                )}
                {trend.biomarker.reference_high !== null && (
                  <ReferenceLine
                    y={trend.biomarker.reference_high}
                    label="上限"
                    stroke="#dc2626"
                    strokeDasharray="3 3"
                  />
                )}
                {trend.biomarker.reference_low !== null && (
                  <ReferenceLine
                    y={trend.biomarker.reference_low}
                    label="下限"
                    stroke="#d97706"
                    strokeDasharray="3 3"
                  />
                )}
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={<TrendDot />}
                  activeDot={{ r: 7 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
        {chartData.length > 0 && (
          <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-primary" /> 正常
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-danger" /> 偏高
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-warning" /> 偏低
            </span>
          </div>
        )}
      </div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            AI 趋势分析
          </h3>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || chartData.length < 2}
            className="btn-primary disabled:opacity-50"
          >
            {analyzing ? '分析中...' : '生成分析'}
          </button>
        </div>

        {chartData.length < 2 && (
          <p className="text-sm text-gray-500">需要至少 2 条已校对记录才能生成趋势分析。</p>
        )}

        {analysis && (
          <div className="space-y-3">
            <div className="p-4 bg-blue-50 rounded-md text-gray-800 leading-relaxed">
              {analysis.analysis}
            </div>
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
              <span className="font-semibold">医疗免责声明：</span>
              {analysis.disclaimer}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
