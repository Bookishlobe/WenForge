import { useEffect, useCallback, useRef } from 'react'
import { useProjectStore } from './stores/projectStore'
import { Sidebar } from './components/Sidebar'
import { Editor } from './components/Editor'
import { AIPanel } from './components/AIPanel'
import { SettingsModal } from './components/Settings'
import { WelcomePage } from './components/WelcomePage'
import { AutoCreateWizard } from './components/AutoCreateWizard'
import { AutoWritingProgress } from './components/AutoWritingProgress'
import { OutlineReview } from './components/OutlineReview'
import { InnovationLibrary } from './components/InnovationLibrary'
import { ProviderSwitcher } from './components/ProviderSwitcher'
import * as api from './lib/api'
import { useSettingsStore } from './stores/settingsStore'
import { useUiStore } from './stores/uiStore'
import type { Chapter } from './types'

interface ComposedFramework {
  title?: string
  hook?: string
  world_setting?: string
  core_conflict?: string
  story_arcs?: string[]
  note?: string
  compose_score?: number
}
import { useProjectManager } from './hooks/useProjectManager'
import { useAutoWriter } from './hooks/useAutoWriter'
import { useAIAssistant } from './hooks/useAIAssistant'
import './App.css'

export default function App() {
  // Stores
  const pythonReady = useSettingsStore(s => s.pythonReady)
  const showSettings = useSettingsStore(s => s.showSettings)
  const loadSettings = useSettingsStore(s => s.loadSettings)
  const setPythonReady = useSettingsStore(s => s.setPythonReady)
  const toggleSettings = useSettingsStore(s => s.toggleSettings)

  const aiPanelOpen = useUiStore(s => s.aiPanelOpen)
  const aiLoading = useUiStore(s => s.aiLoading)
  const autoWriteMode = useUiStore(s => s.autoWriteMode)
  const showInnovation = useUiStore(s => s.showInnovation)
  const genPhase = useUiStore(s => s.genPhase)
  const genProgress = useUiStore(s => s.genProgress)
  const genLogs = useUiStore(s => s.genLogs)
  const genError = useUiStore(s => s.genError)
  const generatedOutline = useUiStore(s => s.generatedOutline)
  const settings = useSettingsStore(s => s.settings)
  const setShowInnovation = useUiStore(s => s.setShowInnovation)
  const setAutoWriteMode = useUiStore(s => s.setAutoWriteMode)

  // Hooks
  const {
    project, chapters, currentChapter, chapterContent,
    handleSelectProject, handleCreateProject, handleSelectChapter,
    handleCreateChapter, handleDeleteChapter, handleSaveChapter,
    handleBackToProjects,
  } = useProjectManager()

  const {
    aiOutput: aiAssistantOutput,
    handleAiContinue, handleAiGenerate, handleApplyAiOutput,
  } = useAIAssistant()

  const {
    handleAutoWriteStart, handleAutoWriteCancel,
    handleAutoWriteOpen, handleAutoWriteViewChapters,
    handleAutoWriteFromCompose,
    handleStartChapters,
    handleContinueBatch,
  } = useAutoWriter()

  // Load settings and check Python on mount
  useEffect(() => { loadSettings() }, [loadSettings])

  useEffect(() => {
    let attempts = 0
    const check = setInterval(async () => {
      try {
        if (await api.checkHealth()) {
          setPythonReady(true)
          clearInterval(check)
        }
      } catch { /* ignore */ }
      if (++attempts > 30) clearInterval(check)
    }, 1000)
    return () => clearInterval(check)
  }, [setPythonReady])

  const handleSelectChapterWrapper = useCallback(async (ch: Chapter) => {
    setAutoWriteMode('idle')
    await handleSelectChapter(ch)
  }, [handleSelectChapter, setAutoWriteMode])

  // ── Create project from compose framework ────────────

  const handleCreateFromCompose = useCallback(async (title: string, framework: ComposedFramework, genre?: string) => {
    try {
      const p = await api.createProject(title, undefined, genre)
      useProjectStore.getState().selectProject(p)
      useProjectStore.getState().loadChapters(p.name)
      setShowInnovation(false)
      handleAutoWriteFromCompose(framework, p.genre || '')
    } catch (err) {
      console.error('Failed to create project from compose:', err)
    }
  }, [setShowInnovation, handleAutoWriteFromCompose])

  // ── Render ──────────────────────────────────────────────
  if (!project) {
    return (
      <div className="app">
        <WelcomePage
          onSelectProject={handleSelectProject}
          onCreateProject={handleCreateProject}
          onOpenSettings={toggleSettings}
          pythonReady={pythonReady}
        />
        {showSettings && <SettingsModal onClose={toggleSettings} />}
      </div>
    )
  }

  return (
    <div className="app">
      <Sidebar
        project={project}
        chapters={chapters}
        currentChapter={currentChapter}
        onSelectChapter={handleSelectChapterWrapper}
        onCreateChapter={handleCreateChapter}
        onDeleteChapter={handleDeleteChapter}
        onBack={handleBackToProjects}
        onOpenSettings={toggleSettings}
        onAutoWrite={handleAutoWriteOpen}
        onInnovation={() => setShowInnovation(true)}
        pythonReady={pythonReady}
      />
      <main className="main-area">
        {showInnovation && autoWriteMode === 'idle' && (
          <InnovationLibrary
            onClose={() => setShowInnovation(false)}
            onCreateProject={(title, framework, genre) => {
              if (framework) {
                handleCreateFromCompose(title, framework, genre)
              } else {
                handleCreateProject(title)
              }
            }}
          />
        )}
        {autoWriteMode === 'wizard' && (
          <AutoCreateWizard
            projectName={project.title}
            genre={project.genre || ''}
            onStart={handleAutoWriteStart}
            onCancel={() => setAutoWriteMode('idle')}
          />
        )}
        {autoWriteMode === 'outline_review' && generatedOutline && (
          <OutlineReview
            outline={generatedOutline}
            onStart={handleStartChapters}
            onCancel={handleAutoWriteCancel}
          />
        )}
        {autoWriteMode === 'generating' && (
          <AutoWritingProgress
            phase={genPhase}
            progress={genProgress}
            logs={genLogs}
            errorMessage={genError}
            onCancel={handleAutoWriteCancel}
            onViewChapters={handleAutoWriteViewChapters}
            onContinue={handleContinueBatch}
          />
        )}
        {autoWriteMode === 'idle' && !showInnovation && (
          <>
            <div className="editor-top-bar">
              <ProviderSwitcher
                settings={settings}
                onOpenSettings={toggleSettings}
              />
            </div>
            <div className="editor-container">
              <Editor
                content={chapterContent}
                chapterName={currentChapter?.name || ''}
                onSave={handleSaveChapter}
              />
            </div>
            <AIPanel
              open={aiPanelOpen}
              loading={aiLoading}
              output={aiAssistantOutput}
              onContinue={handleAiContinue}
              onGenerate={handleAiGenerate}
              onApply={handleApplyAiOutput}
              hasContent={!!chapterContent}
            />
          </>
        )}
      </main>
      {showSettings && <SettingsModal onClose={toggleSettings} />}
    </div>
  )
}
