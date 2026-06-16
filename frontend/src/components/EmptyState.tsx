import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title?: string
  description?: string
  action?: React.ReactNode
}

export default function EmptyState({
  title = '暂无数据',
  description = '当前没有可显示的内容。',
  action,
}: EmptyStateProps) {
  return (
    <div className="card text-center py-12">
      <Inbox className="w-12 h-12 text-gray-300 mx-auto mb-4" />
      <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500 mt-1">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
