import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../../test/test-utils'
import { AIPanel } from '../AIPanel'

describe('AIPanel', () => {
  const defaultProps = {
    open: true,
    loading: false,
    output: '',
    hasContent: true,
    onContinue: vi.fn(),
    onGenerate: vi.fn(),
    onApply: vi.fn(),
  }

  it('renders panel when open', () => {
    render(<AIPanel {...defaultProps} />)
    expect(screen.getByText(/AI 写作助手/)).toBeInTheDocument()
  })

  it('shows tab buttons', () => {
    render(<AIPanel {...defaultProps} />)
    const tabs = screen.getAllByText('续写')
    expect(tabs.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('自由生成')).toBeInTheDocument()
  })

  it('shows loading indicator when loading', () => {
    render(<AIPanel {...defaultProps} loading={true} />)
    expect(screen.getByText('AI 正在创作中...')).toBeInTheDocument()
  })

  it('calls onContinue when submit clicked', () => {
    const onContinue = vi.fn()
    render(<AIPanel {...defaultProps} onContinue={onContinue} />)
    const submitBtns = screen.getAllByText('续写')
    const submitBtn = submitBtns[submitBtns.length - 1]
    fireEvent.click(submitBtn)
    expect(onContinue).toHaveBeenCalled()
  })

  it('shows apply button when output exists', () => {
    render(<AIPanel {...defaultProps} output="generated text" />)
    expect(screen.getByText('✓ 应用到编辑器')).toBeInTheDocument()
  })

  it('calls onApply when apply clicked', () => {
    const onApply = vi.fn()
    render(<AIPanel {...defaultProps} output="text" onApply={onApply} />)
    fireEvent.click(screen.getByText('✓ 应用到编辑器'))
    expect(onApply).toHaveBeenCalled()
  })
})
