import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useAIAssistant } from './useAIAssistant'
import * as api from '../lib/api'

let currentAiOutput = ''

const mockUiStoreState = {
  aiOutput: currentAiOutput,
  setAiLoading: vi.fn(),
  setAiOutput: vi.fn((text: string) => { currentAiOutput = text }),
  clearAiOutput: vi.fn(() => { currentAiOutput = '' }),
}

vi.mock('../stores/projectStore', () => ({
  useProjectStore: (selector: any) =>
    selector({
      chapterContent: 'existing content',
      saveChapter: vi.fn(),
    }),
}))

vi.mock('../stores/uiStore', () => ({
  useUiStore: (selector?: any) =>
    selector ? selector(mockUiStoreState) : mockUiStoreState,
}))

describe('useAIAssistant', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns expected interface', () => {
    const { result } = renderHook(() => useAIAssistant())
    expect(result.current).toHaveProperty('aiOutput')
    expect(result.current).toHaveProperty('handleAiContinue')
    expect(result.current).toHaveProperty('handleAiGenerate')
    expect(result.current).toHaveProperty('handleApplyAiOutput')
  })

  it('handleAiContinue calls api.aiContinue', async () => {
    vi.spyOn(api, 'aiContinue').mockResolvedValue({ text: 'continued text' })
    const { result } = renderHook(() => useAIAssistant())

    await act(async () => {
      await result.current.handleAiContinue()
    })

    expect(api.aiContinue).toHaveBeenCalled()
  })

  it('handleAiGenerate calls api.aiGenerate', async () => {
    vi.spyOn(api, 'aiGenerate').mockResolvedValue({ text: 'generated text' })
    const { result } = renderHook(() => useAIAssistant())

    await act(async () => {
      await result.current.handleAiGenerate('write a story')
    })

    expect(api.aiGenerate).toHaveBeenCalledWith(
      expect.objectContaining({ prompt: 'write a story' }),
    )
  })
})
