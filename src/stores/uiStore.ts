import { create } from 'zustand'
import type { StoryOutline } from '../lib/api'

type AutoWritePhase = 'outline' | 'writing' | 'paused' | 'done' | 'error'
type AutoWriteMode = 'idle' | 'wizard' | 'outline_review' | 'generating'

interface UiState {
  aiPanelOpen: boolean
  aiLoading: boolean
  aiOutput: string
  autoWriteMode: AutoWriteMode
  showInnovation: boolean
  genPhase: AutoWritePhase
  genProgress: { current: number; total: number }
  genLogs: string[]
  genError: string
  generatedOutline: StoryOutline | null

  toggleAiPanel: () => void
  setAiLoading: (loading: boolean) => void
  setAiOutput: (output: string) => void
  clearAiOutput: () => void

  setAutoWriteMode: (mode: AutoWriteMode) => void
  setShowInnovation: (show: boolean) => void

  setGenPhase: (phase: AutoWritePhase) => void
  setGenProgress: (progress: { current: number; total: number }) => void
  addGenLog: (log: string) => void
  setGenError: (error: string) => void
  resetGenState: () => void
  setGeneratedOutline: (outline: StoryOutline | null) => void
}

export const useUiStore = create<UiState>((set) => ({
  aiPanelOpen: false,
  aiLoading: false,
  aiOutput: '',
  autoWriteMode: 'idle',
  showInnovation: false,
  genPhase: 'outline',
  genProgress: { current: 0, total: 0 },
  genLogs: [],
  genError: '',
  generatedOutline: null,

  toggleAiPanel: () => set(state => ({ aiPanelOpen: !state.aiPanelOpen })),

  setAiLoading: (loading: boolean) => set({ aiLoading: loading }),

  setAiOutput: (output: string) => set({ aiOutput: output }),

  clearAiOutput: () => set({ aiOutput: '' }),

  setAutoWriteMode: (mode: AutoWriteMode) => set({ autoWriteMode: mode }),

  setShowInnovation: (show: boolean) => set({ showInnovation: show }),

  setGenPhase: (phase: AutoWritePhase) => set({ genPhase: phase }),

  setGenProgress: (progress) => set({ genProgress: progress }),

  addGenLog: (log: string) => set(state => ({ genLogs: [...state.genLogs, log] })),

  setGenError: (error: string) => set({ genError: error }),

  setGeneratedOutline: (outline) => set({ generatedOutline: outline }),

  resetGenState: () => set({
    genPhase: 'outline',
    genProgress: { current: 0, total: 0 },
    genLogs: [],
    genError: '',
    autoWriteMode: 'idle',
    generatedOutline: null,
  }),
}))
