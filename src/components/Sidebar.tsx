import { useState } from 'react'
import type { Project, Chapter } from '../types'

interface Props {
  project: Project
  chapters: Chapter[]
  currentChapter: Chapter | null
  onSelectChapter: (ch: Chapter) => void
  onCreateChapter: (title: string) => void
  onDeleteChapter: (file: string) => void
  onBack: () => void
  onOpenSettings: () => void
  onAutoWrite: () => void
  onInnovation: () => void
  pythonReady: boolean
}

export function Sidebar({
  project, chapters, currentChapter,
  onSelectChapter, onCreateChapter, onDeleteChapter,
  onBack, onOpenSettings, onAutoWrite, onInnovation, pythonReady
}: Props) {
  const [newTitle, setNewTitle] = useState('')
  const [showNew, setShowNew] = useState(false)

  const handleCreate = () => {
    if (!newTitle.trim()) return
    onCreateChapter(newTitle.trim())
    setNewTitle('')
    setShowNew(false)
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2 title={project.title}>{project.title}</h2>
        <button className="back-btn" onClick={onBack}>← 返回</button>
      </div>

      <div className="chapter-list">
        {chapters.map(ch => (
          <div
            key={ch.file}
            className={`chapter-item ${currentChapter?.file === ch.file ? 'active' : ''}`}
            onClick={() => onSelectChapter(ch)}
          >
            <span>{ch.name}</span>
            <button
              className="delete-btn"
              onClick={(e) => { e.stopPropagation(); onDeleteChapter(ch.file); }}
              title="删除章节"
            >×</button>
          </div>
        ))}
        {chapters.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: 13, padding: '16px 12px', textAlign: 'center' }}>
            还没有章节，点击下方创建
          </p>
        )}
      </div>

      {showNew && (
        <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border)' }}>
          <input
            value={newTitle}
            onChange={e => setNewTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
            placeholder="章节名称"
            style={{ width: '100%', padding: '8px', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)' }}
            autoFocus
          />
          <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
            <button onClick={handleCreate} style={{ flex: 1, padding: '4px 8px', background: 'var(--accent)', border: 'none', color: 'white', borderRadius: '4px', cursor: 'pointer', fontSize: 12 }}>确定</button>
            <button onClick={() => setShowNew(false)} style={{ padding: '4px 8px', background: 'var(--bg-surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)', borderRadius: '4px', cursor: 'pointer', fontSize: 12 }}>取消</button>
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        <button className="btn-auto-write" onClick={onAutoWrite}>🤖 AI 自动创作</button>
        <button onClick={onInnovation}>💡 灵犀</button>
        <button onClick={() => setShowNew(!showNew)}>+ 新建章节</button>
        <button onClick={onOpenSettings}>⚙ 设置</button>
        <div className="status">
          <span className={`status-dot ${pythonReady ? 'online' : 'offline'}`} />
          AI 引擎: {pythonReady ? '就绪' : '连接中...'}
        </div>
      </div>
    </aside>
  )
}
