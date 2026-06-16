import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
  message?: string
}

export default function LoadingSpinner({ message = '加载中...' }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-gray-500">
      <Loader2 className="w-8 h-8 animate-spin text-primary mb-2" />
      <p className="text-sm">{message}</p>
    </div>
  )
}
