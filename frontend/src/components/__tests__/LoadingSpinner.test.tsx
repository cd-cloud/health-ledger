import { render, screen } from '@testing-library/react'
import LoadingSpinner from '../LoadingSpinner'

describe('LoadingSpinner', () => {
  it('renders default loading message', () => {
    render(<LoadingSpinner />)
    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('renders custom message', () => {
    render(<LoadingSpinner message="正在上传报告..." />)
    expect(screen.getByText('正在上传报告...')).toBeInTheDocument()
  })

  it('renders a spin icon for visual feedback', () => {
    const { container } = render(<LoadingSpinner />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})
