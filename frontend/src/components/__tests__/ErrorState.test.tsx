import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ErrorState from '../ErrorState'

describe('ErrorState', () => {
  it('renders default error message', () => {
    render(<ErrorState />)
    expect(screen.getByText('加载失败')).toBeInTheDocument()
    expect(screen.getByText('请求失败，请稍后重试。')).toBeInTheDocument()
  })

  it('renders string error', () => {
    render(<ErrorState error="网络超时" />)
    expect(screen.getByText('网络超时')).toBeInTheDocument()
  })

  it('renders Error instance message', () => {
    render(<ErrorState error={new Error('服务器内部错误')} />)
    expect(screen.getByText('服务器内部错误')).toBeInTheDocument()
  })

  it('renders retry button and invokes callback', async () => {
    const onRetry = vi.fn()
    render(<ErrorState error="加载失败" onRetry={onRetry} />)

    const retryButton = screen.getByRole('button', { name: '重试' })
    expect(retryButton).toBeInTheDocument()

    await userEvent.click(retryButton)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})
