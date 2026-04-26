import { useState } from 'react'

interface Props {
  open: boolean
  loading: boolean
  output: string
  onContinue: (instruction?: string) => void
  onGenerate: (prompt: string) => void
  onApply: () => void
  hasContent: boolean
}

export function AIPanel({ open, loading, output, onContinue, onGenerate, onApply, hasContent }: Props) {
  const [prompt, setPrompt] = useState('')
  const [instruction, setInstruction] = useState('')
  const [tab, setTab] = useState<'continue' | 'generate'>('continue')

  const handleSubmit = () => {
    if (tab === 'continue') {
      onContinue(instruction || undefined)
    } else {
      if (!prompt.trim()) return
      onGenerate(prompt.trim())
    }
  }

  return (
    <div className={`ai-panel ${open ? 'expanded' : 'collapsed'}`}>
      <div className="ai-panel-header" onClick={() => !open && onContinue()}>
        <span>🤖 AI 写作助手 {loading && '(生成中...)'}</span>
        <button className="toggle-btn" onClick={(e) => { e.stopPropagation(); }}>
          {open ? '▼' : '▲'}
        </button>
      </div>

      {open && (
        <div className="ai-panel-body">
          <div className="ai-panel-actions">
            <button
              className={tab === 'continue' ? 'primary' : ''}
              onClick={() => setTab('continue')}
              disabled={loading}
            >
              续写
            </button>
            <button
              className={tab === 'generate' ? 'primary' : ''}
              onClick={() => setTab('generate')}
              disabled={loading}
            >
              自由生成
            </button>
          </div>

          <div style={{ padding: '8px 16px', display: 'flex', gap: 8, borderBottom: '1px solid var(--border)' }}>
            {tab === 'continue' ? (
              <>
                <input
                  value={instruction}
                  onChange={e => setInstruction(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                  placeholder="写作方向（可选）：如「主角发现了一个秘密」..."
                  style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)' }}
                  disabled={loading}
                />
                <button
                  onClick={handleSubmit}
                  disabled={loading || !hasContent}
                  style={{ padding: '8px 20px', background: loading ? 'var(--text-muted)' : 'var(--accent)', border: 'none', color: 'white', borderRadius: 'var(--radius)', cursor: loading || !hasContent ? 'not-allowed' : 'pointer', fontSize: 13 }}
                >
                  {loading ? '生成中...' : '续写'}
                </button>
              </>
            ) : (
              <>
                <input
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                  placeholder="输入创作指令，如「写一段主角突破修为的场景」..."
                  style={{ flex: 1, padding: '8px 12px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)' }}
                  disabled={loading}
                />
                <button
                  onClick={handleSubmit}
                  disabled={loading || !prompt.trim()}
                  style={{ padding: '8px 20px', background: loading || !prompt.trim() ? 'var(--text-muted)' : 'var(--accent)', border: 'none', color: 'white', borderRadius: 'var(--radius)', cursor: loading || !prompt.trim() ? 'not-allowed' : 'pointer', fontSize: 13 }}
                >
                  {loading ? '生成中...' : '生成'}
                </button>
              </>
            )}
          </div>

          <div className="ai-panel-output">
            {loading && (
              <div className="loading">AI 正在创作中...</div>
            )}
            {!loading && !output && (
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                {tab === 'continue'
                  ? '点击"续写"让AI基于当前内容继续写作，或输入写作方向指导AI。'
                  : '输入创作指令，AI将生成新的内容。'}
              </div>
            )}
            {output && (
              <>
                <div>{output}</div>
                <button className="apply-btn" onClick={onApply}>
                  ✓ 应用到编辑器
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
