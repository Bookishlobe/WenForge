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

  // Batch generation state
  const batchRef = useRef({
    outline: null as api.StoryOutline | null,
    chapterOutlines: [] as string[],
    summaries: [] as string[],
    totalChapters: 0,
    batchSize: 3,
    genre: '',
    style: '',
    chapterLength: 'medium' as string,
    config: null as AutoWriteConfig | null,
  })

  // ── Phase 1: Generate outline → show review ──────────────

  const handleAutoWriteStart = useCallback(async (config: AutoWriteConfig) => {
    const currentProject = useProjectStore.getState().project
    if (!currentProject) return

    setAutoWriteMode('generating')
    setGenPhase('outline')
    setGenProgress({ current: 0, total: config.totalChapters })
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
      addGenLog(`世界观：${outline.world_setting || ''}`)

      if (cancelRef.current) { setAutoWriteMode('idle'); return }

      // Save outline to store and switch to review mode
      setGeneratedOutline(outline)
      setAutoWriteMode('outline_review')
      setGenPhase('outline')

      // Store batch context for later use
      batchRef.current = {
        outline,
        chapterOutlines,
        summaries: [],
        totalChapters: 0,
        batchSize: 3,
        genre: currentProject.genre || '玄幻',
        style: config.style,
        chapterLength: config.chapterLength,
        config,
      }

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '大纲生成过程中出现错误'
      setGenPhase('error')
      setGenError(msg)
      addGenLog(`❌ 错误: ${msg}`)
    }
  }, [addGenLog, setGenPhase, setGenProgress, setGenError, setAutoWriteMode, setGeneratedOutline])

  // ── Phase 2: Generate chapters in batches ──────────────

  const doGenerateBatch = useCallback(async () => {
    const currentProject = useProjectStore.getState().project
    if (!currentProject) return

    const bc = batchRef.current
    const { outline, chapterOutlines, batchSize, genre, style, chapterLength } = bc

    if (!outline || chapterOutlines.length === 0) {
      setGenPhase('done')
      addGenLog('没有更多章节需要生成')
      return
    }

    // Take up to batchSize chapters from the remaining list
    const batch = chapterOutlines.splice(0, Math.min(batchSize, 3))
    const currentTotal = bc.summaries.length
    const grandTotal = bc.totalChapters || chapterOutlines.length + batch.length

    setAutoWriteMode('generating')
    setGenPhase('writing')

    for (let i = 0; i < batch.length; i++) {
      if (cancelRef.current) {
        addGenLog('⏸ 生成已暂停')
        setAutoWriteMode('idle')
        batchRef.current.chapterOutlines = [...batch.slice(i), ...chapterOutlines] // put remaining back
        return
      }

      const chapterIndex = currentTotal + i + 1
      setGenProgress({ current: chapterIndex, total: grandTotal })
      addGenLog(`正在生成第 ${chapterIndex} 章...`)

      try {
        const chapterResult = await api.autoGenerateChapter({
          outline,
          chapter_index: chapterIndex,
          chapter_outline: batch[i],
          previous_summaries: bc.summaries,
          config: {
            genre,
            style,
            chapter_length: chapterLength,
          },
        })

        if (!chapterResult.success) {
          throw new Error(chapterResult.error || `第 ${chapterIndex} 章生成失败`)
        }

        const title = chapterResult.title || `第${chapterIndex}章`
        let fileName = ''
        try {
          fileName = await api.createChapter(currentProject.name, title)
          await api.saveChapter(currentProject.name, fileName, chapterResult.text)
        } catch (err) {
          addGenLog(`⚠ 保存第 ${chapterIndex} 章失败: ${err}`)
        }

        const summary = chapterResult.text.replace(/#+ .*\n/g, '').trim().slice(0, 150)
        bc.summaries.push(summary)

        addGenLog(`✅ 第 ${chapterIndex} 章完成（${chapterResult.text.length} 字）`)

        if (chapterIndex % 3 === 0) {
          await loadChapters(currentProject.name)
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : `第 ${chapterIndex} 章生成失败`
        setGenPhase('error')
        setGenError(msg)
        addGenLog(`❌ 错误: ${msg}`)
        return
      }
    }

    await loadChapters(currentProject.name)

    // Check if there are more chapters to generate
    if (chapterOutlines.length > 0) {
      setGenPhase('paused')
      setGenProgress({ current: grandTotal - chapterOutlines.length, total: grandTotal })
      addGenLog(`📌 已完成 ${grandTotal - chapterOutlines.length}/${grandTotal} 章，点击继续生成下一批`)
    } else {
      setGenPhase('done')
      setGenProgress({ current: grandTotal, total: grandTotal })
      addGenLog(`🎉 全部 ${grandTotal} 章创作完成！`)
      await loadChapters(currentProject.name)
    }
  }, [loadChapters, addGenLog, setGenPhase, setGenProgress, setGenError, setAutoWriteMode])

  // ── Start chapter generation from outline review ──────

  const handleStartChapters = useCallback(async (totalChapters: number, batchSize: number) => {
    const outline = useUiStore.getState().generatedOutline
    if (!outline) return

    const allOutlines = outline.chapter_outlines || []
    const capped = Math.min(totalChapters, allOutlines.length)

    batchRef.current.totalChapters = capped
    batchRef.current.batchSize = Math.min(Math.max(1, batchSize), 3)
    batchRef.current.chapterOutlines = allOutlines.slice(0, capped)
    batchRef.current.summaries = []
    batchRef.current.outline = outline

    await doGenerateBatch()
  }, [doGenerateBatch])

  // ── Continue next batch ──────────────────────────────

  const handleContinueBatch = useCallback(async () => {
    await doGenerateBatch()
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
    handleContinueBatch,
  }
}
