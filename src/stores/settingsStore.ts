import { create } from 'zustand'
import type { UserSettings } from '../types'

interface SettingsState {
  settings: UserSettings
  pythonReady: boolean
  showSettings: boolean

  loadSettings: () => Promise<void>
  updateSettings: (s: UserSettings) => void
  setPythonReady: (ready: boolean) => void
  toggleSettings: () => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: {},
  pythonReady: false,
  showSettings: false,

  loadSettings: async () => {
    try {
      const saved = await window.wenforge.loadSettings()
      if (saved && Object.keys(saved).length > 0) {
        set({ settings: saved })
      }
    } catch {
      const saved = localStorage.getItem('wenforge-settings')
      if (saved) set({ settings: JSON.parse(saved) })
    }
  },

  updateSettings: (s: UserSettings) => {
    set({ settings: s })
  },

  setPythonReady: (ready: boolean) => {
    set({ pythonReady: ready })
  },

  toggleSettings: () => {
    set(state => ({ showSettings: !state.showSettings }))
  },
}))
