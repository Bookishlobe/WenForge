import { create } from 'zustand'
import type { Project, Chapter } from '../types'
import * as api from '../lib/api'

interface ProjectState {
  project: Project | null
  chapters: Chapter[]
  currentChapter: Chapter | null
  chapterContent: string

  loadChapters: (projectName: string) => Promise<Chapter[]>
  selectProject: (p: Project) => void
  selectChapter: (ch: Chapter) => Promise<string>
  createChapter: (title: string) => Promise<void>
  deleteChapter: (chapterFile: string) => Promise<void>
  saveChapter: (content: string) => Promise<void>
  clearProject: () => void
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  project: null,
  chapters: [],
  currentChapter: null,
  chapterContent: '',

  loadChapters: async (projectName: string) => {
    const list = await api.listChapters(projectName)
    set({ chapters: list })
    return list
  },

  selectProject: (p: Project) => {
    set({
      project: p,
      currentChapter: null,
      chapterContent: '',
    })
  },

  selectChapter: async (ch: Chapter) => {
    const project = get().project
    if (!project) return ''
    const content = await api.readChapter(project.name, ch.file)
    set({ currentChapter: ch, chapterContent: content })
    return content
  },

  createChapter: async (title: string) => {
    const project = get().project
    if (!project) return
    const fileName = await api.createChapter(project.name, title)
    const chaptersList = await api.listChapters(project.name)
    set({ chapters: chaptersList })
    const newChapter = chaptersList.find(c => c.file === fileName)
    if (newChapter) {
      const content = await api.readChapter(project.name, newChapter.file)
      set({ currentChapter: newChapter, chapterContent: content })
    }
  },

  deleteChapter: async (chapterFile: string) => {
    const project = get().project
    const current = get().currentChapter
    if (!project) return
    await api.deleteChapter(project.name, chapterFile)
    if (current?.file === chapterFile) {
      set({ currentChapter: null, chapterContent: '' })
    }
    const list = await api.listChapters(project.name)
    set({ chapters: list })
  },

  saveChapter: async (content: string) => {
    const project = get().project
    const current = get().currentChapter
    if (!project || !current) return
    await api.saveChapter(project.name, current.file, content)
    set({ chapterContent: content })
  },

  clearProject: () => {
    set({
      project: null,
      chapters: [],
      currentChapter: null,
      chapterContent: '',
    })
  },
}))
