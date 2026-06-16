import { AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  error?: string | Error | null
  onRetry?: () => void
}

export default function ErrorState({
  title = '加载失败',
  error,
  onRetry,
}: ErrorStateProps) {
  const message =
    error instanceof Error ? error.message : typeof error === 'string' ? error : '请求失败，请稍后重试。'

  return (
    <div className="card text-center py-12">
      <AlertTriangle className="w-12 h-12 text-danger mx-auto mb-4" />
      <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500 mt-1">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary mt-4">
          重试
        </button>
      )}
    </div>
  )
}
