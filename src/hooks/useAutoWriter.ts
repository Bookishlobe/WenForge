import { useCallback, useRef } from 'react'
import { useProjectStore } from '../stores/projectStore'
import { useUiStore } from '../stores/uiStore'
import type { AutoWriteConfig } from '../components/AutoCreateWizard'
import * as api from '../lib/api'

interface ComposedFramework {
  title?: string
  hook?: string
  world_setting?: string
  core_conflict?: string
  story_arcs?: string[]
  note?: string
  compose_score?: number
}

export function useAutoWriter() {
  const project = useProjectStore(s => s.project)
  const loadChapters = useProjectStore(s => s.loadChapters)
  const {
    addGenLog,
    setGenPhase,
    setGenProgress,
    setGenError,
    setAutoWriteMode,
    setGeneratedOutline,
    resetGenState,
  } = useUiStore()
  const cancelRef = useRef(false)

  // Generation state
  const batchRef = useRef({
    outline: null as api.StoryOutline | null,
    remainingOutlines: [] as string[],
    summaries: [] as string[],
    nextChapterIndex: 1,
    genre: '',
    style: '',
    chapterLength: 'medium' as string,
  })

  // ── Phase 1: Generate outline → show review ──────────────

  const handleAutoWriteStart = useCallback(async (config: AutoWriteConfig) => {
    const currentProject = useProjectStore.getState().project
    if (!currentProject) return

    setAutoWriteMode('generating')
    setGenPhase('outline')
    addGenLog('开始 AI 自动创作流程...')
    setGenError('')
    cancelRef.current = false

    try {
      addGenLog('正在生成故事大纲...')
      const outlineResult = await api.autoGenerateOutline({
        genre: currentProject.genre || '玄幻',
        premise: config.premise,
        protagonist: config.protagonist,
        style: config.style,
        total_chapters: config.totalChapters,
        chapter_length: config.chapterLength,
      })

      if (!outlineResult.success) {
        throw new Error(outlineResult.error || '大纲生成失败')
      }

      const outline = outlineResult.outline
      const chapterOutlines: string[] = outline.chapter_outlines || []
      addGenLog(`大纲完成：${outline.title}（${chapterOutlines.length} 章）`)

      if (cancelRef.current) { setAutoWriteMode('idle'); return }

      // Save outline to store and switch to review mode
      setGeneratedOutline(outline)
      setAutoWriteMode('outline_review')
      setGenPhase('outline')

      // Store context for chapter generation
      batchRef.current = {
        outline,
        remainingOutlines: chapterOutlines,
        summaries: [],
        nextChapterIndex: 1,
        genre: currentProject.genre || '玄幻',
        style: config.style,
        chapterLength: config.chapterLength,
      }

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '大纲生成过程中出现错误'
      setGenPhase('error')
      setGenError(msg)
      addGenLog(`❌ 错误: ${msg}`)
    }
  }, [addGenLog, setGenPhase, setGenProgress, setGenError, setAutoWriteMode, setGeneratedOutline])

  // ── Phase 2: Generate N chapters (initial 3 or 1-at-a-time) ──

  const doGenerateBatch = useCallback(async (count: number) => {
    const currentProject = useProjectStore.getState().project
    if (!currentProject) return

    const bc = batchRef.current
    const { outline, remainingOutlines, genre, style, chapterLength } = bc

    if (!outline || remainingOutlines.length === 0) {
      setGenPhase('done')
      addGenLog('所有章节已生成完毕')
      return
    }

    const batch = remainingOutlines.splice(0, count)

    setAutoWriteMode('generating')
    setGenPhase('writing')
    setGenProgress({ current: 1, total: batch.length })

    for (let i = 0; i < batch.length; i++) {
      if (cancelRef.current) {
        addGenLog('⏸ 生成已暂停')
        setAutoWriteMode('idle')
        batchRef.current.remainingOutlines = [...batch.slice(i), ...remainingOutlines]
        return
      }

      const chapterIndex = bc.nextChapterIndex
      bc.nextChapterIndex++
      setGenProgress({ current: i + 1, total: batch.length })
      addGenLog(`正在生成第 ${chapterIndex} 章...`)

      try {
        const chapterResult = await api.autoGenerateChapter({
          outline,
          chapter_index: chapterIndex,
          chapter_outline: batch[i],
          previous_summaries: bc.summaries,
          config: { genre, style, chapter_length: chapterLength },
        })

        if (!chapterResult.success) {
          throw new Error(chapterResult.error || `第 ${chapterIndex} 章生成失败`)
        }

        const title = chapterResult.title || `第${chapterIndex}章`
        try {
          const fileName = await api.createChapter(currentProject.name, title)
          await api.saveChapter(currentProject.name, fileName, chapterResult.text)
        } catch (err) {
          addGenLog(`⚠ 保存第 ${chapterIndex} 章失败: ${err}`)
        }

        const summary = chapterResult.text.replace(/#+ .*\n/g, '').trim().slice(0, 150)
        bc.summaries.push(summary)
        addGenLog(`✅ 第 ${chapterIndex} 章完成（${chapterResult.text.length} 字）`)
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : `第 ${chapterIndex} 章生成失败`
        setGenPhase('error')
        setGenError(msg)
        addGenLog(`❌ 错误: ${msg}`)
        return
      }
    }

    await loadChapters(currentProject.name)

    const totalDone = bc.summaries.length
    const remaining = bc.remainingOutlines.length
    setGenPhase('done')
    setGenProgress({ current: totalDone, total: totalDone })

    if (remaining > 0) {
      addGenLog(`🎉 第 ${totalDone} 章完成！还有 ${remaining} 章待续写`)
    } else {
      addGenLog(`🎉 全部 ${totalDone} 章创作完成！`)
    }
  }, [loadChapters, addGenLog, setGenPhase, setGenProgress, setGenError, setAutoWriteMode])

  // ── Start: generate first 3 chapters ──────────────────

  const handleStartChapters = useCallback(async () => {
    const bc = batchRef.current
    const count = Math.min(3, bc.remainingOutlines.length)
    if (count === 0) return
    await doGenerateBatch(count)
  }, [doGenerateBatch])

  // ── Continue: write next chapter ──────────────────────

  const handleWriteNextChapter = useCallback(async () => {
    await doGenerateBatch(1)
  }, [doGenerateBatch])

  // ── Cancel ───────────────────────────────────────────

  const handleAutoWriteCancel = useCallback(() => {
    cancelRef.current = true
    resetGenState()
  }, [resetGenState])

  // ── Open wizard ──────────────────────────────────────

  const handleAutoWriteOpen = useCallback(() => {
    setAutoWriteMode('wizard')
    resetGenState()
    cancelRef.current = false
  }, [setAutoWriteMode, resetGenState])

  // ── View chapters ────────────────────────────────────

  const handleAutoWriteViewChapters = useCallback(async () => {
    setAutoWriteMode('idle')
    const p = useProjectStore.getState().project
    if (p) {
      return await loadChapters(p.name)
    }
  }, [loadChapters, setAutoWriteMode])

  // ── From compose framework ──────────────────────────

  const handleAutoWriteFromCompose = useCallback(async (framework: ComposedFramework, genre: string) => {
    const premiseParts = [framework.hook, framework.world_setting, framework.core_conflict].filter(Boolean)
    const premise = premiseParts.join('\n\n') || '基于灵犀组合框架创作的故事'

    await handleAutoWriteStart({
      premise,
      protagonist: '',
      style: '流畅直白',
      totalChapters: 20,
      chapterLength: 'medium',
    })
  }, [handleAutoWriteStart])

  return {
    cancelRef,
    handleAutoWriteStart,
    handleAutoWriteCancel,
    handleAutoWriteOpen,
    handleAutoWriteViewChapters,
    handleAutoWriteFromCompose,
    handleStartChapters,
    handleWriteNextChapter,
  }
}
