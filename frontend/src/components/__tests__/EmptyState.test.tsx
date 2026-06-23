import { render, screen } from '@testing-library/react'
import EmptyState from '../EmptyState'

describe('EmptyState', () => {
  it('renders default empty state', () => {
    render(<EmptyState />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
    expect(screen.getByText('当前没有可显示的内容。')).toBeInTheDocument()
  })

  it('renders custom title and description', () => {
    render(<EmptyState title="没有报告" description="请上传体检报告。" />)
    expect(screen.getByText('没有报告')).toBeInTheDocument()
    expect(screen.getByText('请上传体检报告。')).toBeInTheDocument()
  })

  it('renders action element when provided', () => {
    render(<EmptyState action={<button>去上传</button>} />)
    expect(screen.getByRole('button', { name: '去上传' })).toBeInTheDocument()
  })
})
