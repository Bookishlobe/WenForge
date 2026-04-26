import { useState, useEffect } from 'react'
import * as api from '../lib/api'
import type { Project } from '../types'

interface Props {
  onSelectProject: (p: Project) => void
  onCreateProject: (title: string, author?: string, genre?: string) => void
  onOpenSettings: () => void
  pythonReady: boolean
}

export function WelcomePage({ onSelectProject, onCreateProject, onOpenSettings, pythonReady }: Props) {
  const [projects, setProjects] = useState<Project[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [genre, setGenre] = useState('')

  useEffect(() => {
    api.listProjects().then(setProjects)
  }, [])

  const handleCreate = () => {
    if (!title.trim()) return
    onCreateProject(title.trim(), author.trim() || undefined, genre || undefined)
    setShowCreate(false)
    setTitle('')
    setAuthor('')
    setGenre('')
  }

  return (
    <div className="welcome">
      <h1>WenForge</h1>
      <p className="subtitle">锻造文学 · AI 网文创作助手</p>
      <p className="status-bar">
        <span className={`status-dot ${pythonReady ? 'online' : 'offline'}`} />
        AI 引擎: {pythonReady ? '就绪' : '连接中...'}
      </p>

      <div className="actions">
        <button className="btn-primary" onClick={() => setShowCreate(!showCreate)}>
          + 新建作品
        </button>
        <button className="btn-secondary" onClick={onOpenSettings}>
          设置
        </button>
      </div>

      {showCreate && (
        <div style={{ width: '100%', maxWidth: 400, marginBottom: 32, background: 'var(--bg-surface)', padding: 20, borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
          <div className="setting-row">
            <label>作品名称 *</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="输入作品名称" autoFocus />
          </div>
          <div className="setting-row">
            <label>作者</label>
            <input value={author} onChange={e => setAuthor(e.target.value)} placeholder="笔名" />
          </div>
          <div className="setting-row">
            <label>题材</label>
            <select value={genre} onChange={e => setGenre(e.target.value)}>
              <option value="">选择题材</option>
              <option value="玄幻">玄幻</option>
              <option value="仙侠">仙侠</option>
              <option value="悬疑">悬疑</option>
              <option value="都市">都市</option>
              <option value="科幻">科幻</option>
              <option value="历史">历史</option>
              <option value="言情">言情</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
            <button className="modal-footer .btn-secondary" style={{ padding: '8px 20px', background: 'var(--bg-surface)', border: '1px solid var(--border)', color: 'var(--text-primary)', borderRadius: 'var(--radius)', cursor: 'pointer' }} onClick={() => setShowCreate(false)}>取消</button>
            <button className="modal-footer .btn-primary" style={{ padding: '8px 20px', background: 'var(--accent)', border: 'none', color: 'white', borderRadius: 'var(--radius)', cursor: 'pointer' }} onClick={handleCreate}>创建</button>
          </div>
        </div>
      )}

      {projects.length > 0 && (
        <div className="project-list">
          <h3>最近作品</h3>
          {projects.map(p => (
            <div key={p.name} className="project-card" onClick={() => onSelectProject(p)}>
              <div className="title">{p.title}</div>
              <div className="meta">{p.author && `${p.author} · `}{p.genre || '未分类'}{p.createdAt && ` · ${new Date(p.createdAt).toLocaleDateString('zh-CN')}`}</div>
            </div>
          ))}
        </div>
      )}

      {projects.length === 0 && !showCreate && (
        <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>还没有作品，点击"新建作品"开始创作</p>
      )}
    </div>
  )
}
