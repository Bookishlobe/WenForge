import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '../../test/test-utils'
import { ProviderSwitcher } from '../ProviderSwitcher'
import type { UserSettings } from '../../types'

describe('ProviderSwitcher', () => {
  const defaultSettings: UserSettings = {
    activeProvider: {
      writing: 'openai',
      polishing: 'claude',
      outline: 'deepseek',
    },
  }

  it('renders provider indicators', () => {
    render(<ProviderSwitcher settings={defaultSettings} onOpenSettings={vi.fn()} />)
    expect(screen.getByText('写作')).toBeInTheDocument()
  })

  it('calls onOpenSettings when settings button clicked', () => {
    const onOpenSettings = vi.fn()
    render(<ProviderSwitcher settings={defaultSettings} onOpenSettings={onOpenSettings} />)
    const btn = screen.getByRole('button')
    fireEvent.click(btn)
    expect(onOpenSettings).toHaveBeenCalled()
  })
})
