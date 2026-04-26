import { useCallback } from 'react'
import { useProjectStore } from '../stores/projectStore'
import { useUiStore } from '../stores/uiStore'
import * as api from '../lib/api'
import type { Project } from '../types'

export function useProjectManager() {
  const project = useProjectStore(s => s.project)
  const chapters = useProjectStore(s => s.chapters)
  const currentChapter = useProjectStore(s => s.currentChapter)
  const chapterContent = useProjectStore(s => s.chapterContent)
  const selectProject = useProjectStore(s => s.selectProject)
  const loadChapters = useProjectStore(s => s.loadChapters)
  const selectChapter = useProjectStore(s => s.selectChapter)
  const createChapter = useProjectStore(s => s.createChapter)
  const deleteChapter = useProjectStore(s => s.deleteChapter)
  const saveChapter = useProjectStore(s => s.saveChapter)
  const clearProject = useProjectStore(s => s.clearProject)
  const setAutoWriteMode = useUiStore(s => s.setAutoWriteMode)
  const resetGenState = useUiStore(s => s.resetGenState)

  const handleSelectProject = useCallback(async (p: Project) => {
    selectProject(p)
    setAutoWriteMode('idle')
    resetGenState()

    const list = await loadChapters(p.name)
    if (list.length === 0) {
      setAutoWriteMode('wizard')
    }
  }, [selectProject, loadChapters, setAutoWriteMode, resetGenState])

  const handleCreateProject = useCallback(async (title: string, author?: string, genre?: string) => {
    const p = await api.createProject(title, author, genre)
    await handleSelectProject(p)
  }, [handleSelectProject])

  const handleBackToProjects = useCallback(() => {
    clearProject()
    setAutoWriteMode('idle')
    resetGenState()
  }, [clearProject, setAutoWriteMode, resetGenState])

  return {
    project,
    chapters,
    currentChapter,
    chapterContent,
    handleSelectProject,
    handleCreateProject,
    handleSelectChapter: selectChapter,
    handleCreateChapter: createChapter,
    handleDeleteChapter: deleteChapter,
    handleSaveChapter: saveChapter,
    handleBackToProjects,
  }
}
