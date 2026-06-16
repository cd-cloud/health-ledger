import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, FileCheck, AlertCircle, Loader2 } from 'lucide-react'

import { uploadReport, parseReport } from '../api/reports'

export default function UploadReport() {
  const [file, setFile] = useState<File | null>(null)
  const [reportDate, setReportDate] = useState('')
  const [uploading, setUploading] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0]
    if (selected && selected.type === 'application/pdf') {
      setFile(selected)
      setError(null)
    } else {
      setFile(null)
      setError('请选择 PDF 文件')
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) {
      setError('请先选择文件')
      return
    }

    setUploading(true)
    setError(null)
    setSuccess(null)
    try {
      const report = await uploadReport(file, reportDate || undefined)
      setUploading(false)
      setParsing(true)
      setSuccess('文件已上传，正在解析指标...')
      try {
        await parseReport(report.id)
        setSuccess('解析完成，正在跳转...')
        navigate(`/reports/${report.id}`)
      } catch (err) {
        setError('文件上传成功，但解析失败，请进入报告详情手动重试。')
        navigate(`/reports/${report.id}`)
      }
    } catch (err) {
      setUploading(false)
      setError(err instanceof Error ? err.message : '上传失败')
    }
  }

  const isBusy = uploading || parsing

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">上传体检报告</h2>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              file ? 'border-primary bg-blue-50' : 'border-gray-300 hover:border-primary'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              className="hidden"
              disabled={isBusy}
            />
            {file ? (
              <div className="flex flex-col items-center gap-2">
                <FileCheck className="w-10 h-10 text-primary" />
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">点击重新选择</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <UploadCloud className="w-10 h-10 text-gray-400" />
                <p className="font-medium text-gray-900">点击或拖拽上传 PDF 报告</p>
                <p className="text-sm text-gray-500">仅支持 .pdf 格式，原始文件将被保留</p>
              </div>
            )}
          </div>

          <div>
            <label htmlFor="reportDate" className="block text-sm font-medium text-gray-700 mb-1">
              报告日期（可选）
            </label>
            <input
              id="reportDate"
              type="date"
              value={reportDate}
              onChange={(e) => setReportDate(e.target.value)}
              className="input"
              disabled={isBusy}
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 text-sm text-red-700 bg-red-50 rounded-md p-3">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 text-sm text-green-700 bg-green-50 rounded-md p-3">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>{success}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isBusy || !file}
            className="btn-primary w-full disabled:opacity-50"
          >
            {uploading ? '上传中...' : parsing ? '解析中...' : '上传并解析'}
          </button>
        </form>
      </div>

      <div className="text-sm text-gray-500 space-y-1">
        <p>• 上传后系统会自动提取文本并尝试识别指标。</p>
        <p>• AI 提取结果需要人工校对后才会进入趋势分析。</p>
        <p>• 原始 PDF 文件将被保留在本地，可随时重新解析。</p>
      </div>
    </div>
  )
}
