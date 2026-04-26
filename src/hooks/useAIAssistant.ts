import { useCallback } from 'react'
import { useProjectStore } from '../stores/projectStore'
import { useUiStore } from '../stores/uiStore'
import * as api from '../lib/api'

export function useAIAssistant() {
  const chapterContent = useProjectStore(s => s.chapterContent)
  const saveChapter = useProjectStore(s => s.saveChapter)
  const { aiOutput, setAiLoading, setAiOutput, clearAiOutput } = useUiStore()

  const handleAiContinue = useCallback(async (instruction?: string) => {
    if (!chapterContent) return
    setAiLoading(true)
    clearAiOutput()
    try {
      const result = await api.aiContinue(chapterContent, instruction)
      setAiOutput(result.text)
    } catch (err: unknown) {
      setAiOutput(`错误: ${err instanceof Error ? err.message : '请检查 Python 后端是否运行'}`)
    }
    setAiLoading(false)
  }, [chapterContent, setAiLoading, clearAiOutput, setAiOutput])

  const handleAiGenerate = useCallback(async (prompt: string) => {
    setAiLoading(true)
    clearAiOutput()
    try {
      const result = await api.aiGenerate({ prompt, temperature: 0.8 })
      setAiOutput(result.text)
    } catch (err: unknown) {
      setAiOutput(`错误: ${err instanceof Error ? err.message : '请检查 Python 后端和 API 配置'}`)
    }
    setAiLoading(false)
  }, [setAiLoading, clearAiOutput, setAiOutput])

  const handleApplyAiOutput = useCallback(() => {
    if (aiOutput) {
      const newContent = chapterContent + '\n\n' + aiOutput
      saveChapter(newContent)
      clearAiOutput()
    }
  }, [aiOutput, chapterContent, saveChapter, clearAiOutput])

  return {
    aiOutput,
    handleAiContinue,
    handleAiGenerate,
    handleApplyAiOutput,
  }
}
