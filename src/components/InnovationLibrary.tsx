import { useState, useCallback, useRef, useEffect } from 'react'
import type { InnovationIdea } from '../lib/api'
import * as api from '../lib/api'

// ── Constants ─────────────────────────────────────────────

const IDEA_TYPES = [
  { value: '', label: '全部维度', desc: '五个创新维度各生成1-2个灵感' },
  { value: 'genre_fusion', label: '题材融合', desc: '将不同题材核心要素交叉融合' },
  { value: 'golden_finger', label: '金手指创新', desc: '突破泛滥模式的新概念外挂' },
  { value: 'world_twist', label: '世界观反转', desc: '在熟悉设定中完成颠覆反转' },
  { value: 'character_innovation', label: '人物创新', desc: '非标准主角与创新关系组合' },
  { value: 'plot_innovation', label: '情节创新', desc: '非线性叙事与反套路结构' },
]

const TYPE_LABELS: Record<string, string> = {
  genre_fusion: '题材融合',
  golden_finger: '金手指',
  world_twist: '反转',
  character_innovation: '人物',
  plot_innovation: '情节',
}

const TYPE_COLORS: Record<string, string> = {
  genre_fusion: '#8b5cf6',
  golden_finger: '#f59e0b',
  world_twist: '#10b981',
  character_innovation: '#3b82f6',
  plot_innovation: '#ef4444',
}

// ── Random fill pools ─────────────────────────────────────

const RANDOM_GENRES = ['玄幻', '仙侠', '悬疑', '科幻', '都市', '武侠', '历史', '奇幻', '末日', '游戏', '轻小说', '西方奇幻']
const STYLE_OPTIONS = ['流畅直白', '细腻描写', '幽默诙谐', '严肃正剧', '古风典雅', '轻松爽文']
const RANDOM_KEYWORD_SETS = [
  '赛博朋克,修仙,系统流',
  '穿越,重生,废柴逆袭',
  '克苏鲁,修仙,武道',
  '星际,机甲,文明进化',
  '灵气复苏,异能,学院',
  '神话复苏,古代文明,封印',
  '无限流,副本,面板数据',
  '都市异能,日常,温馨',
]
const RANDOM_AVOID_SETS = [
  '签到系统,神豪流,赘婿',
  '龙王回归,战神归来,歪嘴',
  '兵王,神医,透视眼',
  '无脑爽,后宫,种马',
  '套路化升级,数值膨胀',
]

// ── Score Badge Color ─────────────────────────────────────

function scoreColor(score: number): string {
  if (score >= 8) return '#10b981'
  if (score >= 5) return '#f59e0b'
  return '#6b7280'
}

function scoreLabel(score: number): string {
  if (score >= 8) return '高度创新'
  if (score >= 5) return '中度创新'
  if (score >= 2) return '常规套路'
  return '过度使用'
}

// ── Types for expand/compose results ──────────────────────

interface ExpandedOutline {
  title?: string
  hook?: string
  world_setting?: string
  prototype?: string
  protagonist?: { name: string; description: string }
  story_arcs?: string | string[]
  target_audience?: string
  estimated_chapters?: number
  chapter_outlines?: string[]
  error?: string
  [key: string]: unknown
}

interface ComposedFramework {
  title?: string
  hook?: string
  world_setting?: string
  core_conflict?: string
  story_arcs?: string[]
  note?: string
  compose_score?: number
  [key: string]: unknown
}

function getApiError(err: unknown, fallback: string): string {
  if (err instanceof Error) return err.message
  if (err && typeof err === 'object') {
    const detail = (err as Record<string, unknown>).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

// ── Props ────────────────────────────────────────────────

interface Props {
  onInsertOutline?: (outline: ExpandedOutline) => void
  onClose?: () => void
  onCreateProject?: (title: string, outline?: ComposedFramework, genre?: string) => void
}

// ── Component ────────────────────────────────────────────

export function InnovationLibrary({ onInsertOutline, onClose, onCreateProject }: Props) {
  // Form state
  const [genre, setGenre] = useState('玄幻')
  const [style, setStyle] = useState('流畅直白')
  const [keywords, setKeywords] = useState('')
  const [avoidPatterns, setAvoidPatterns] = useState('')
  const [ideaType, setIdeaType] = useState('')

  // Generation state
  const [generating, setGenerating] = useState(false)
  const [ideas, setIdeas] = useState<InnovationIdea[]>([])
  const [error, setError] = useState('')

  // View state
  const [selectedIdea, setSelectedIdea] = useState<InnovationIdea | null>(null)
  const [expandedOutline, setExpandedOutline] = useState<ExpandedOutline | null>(null)
  const [expanding, setExpanding] = useState(false)

  // Compose state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [composing, setComposing] = useState(false)
  const [composedFramework, setComposedFramework] = useState<ComposedFramework | null>(null)
  const [editingCompose, setEditingCompose] = useState(false)
  const [draftFramework, setDraftFramework] = useState<ComposedFramework | null>(null)

  // Compose scroll ref
  const composeRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to compose result when it appears
  useEffect(() => {
    if (composedFramework && composeRef.current) {
      composeRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [composedFramework])

  // Favorites (in-memory for MVP)
  const [favorites, setFavorites] = useState<Set<string>>(new Set())

  // ── Random fill ───────────────────────────────────────

  const handleRandom = useCallback(() => {
    setGenre(RANDOM_GENRES[Math.floor(Math.random() * RANDOM_GENRES.length)])
    setStyle(STYLE_OPTIONS[Math.floor(Math.random() * STYLE_OPTIONS.length)])
    setKeywords(RANDOM_KEYWORD_SETS[Math.floor(Math.random() * RANDOM_KEYWORD_SETS.length)])
    setAvoidPatterns(RANDOM_AVOID_SETS[Math.floor(Math.random() * RANDOM_AVOID_SETS.length)])
    const nonEmptyTypes = IDEA_TYPES.filter(t => t.value !== '')
    setIdeaType(nonEmptyTypes[Math.floor(Math.random() * nonEmptyTypes.length)].value)
  }, [])

  // ── Generate ───────────────────────────────────────────

  const handleGenerate = useCallback(async () => {
    setGenerating(true)
    setError('')
    setSelectedIdea(null)
    setExpandedOutline(null)
    // Don't reset composedFramework or selectedIds — let users keep results across generations

    try {
      const kwList = keywords.split(/[,，、]/).map(s => s.trim()).filter(Boolean)
      const avList = avoidPatterns.split(/[,，、]/).map(s => s.trim()).filter(Boolean)

      const result = await api.innovationGenerate({
        idea_type: ideaType || undefined,
        genre,
        style,
        keywords: kwList.length > 0 ? kwList : undefined,
        avoid_patterns: avList.length > 0 ? avList : undefined,
        count: 3,
      })

      // Flatten the result into a single list
      const flatIdeas: InnovationIdea[] = []
      for (const [, items] of Object.entries(result.ideas)) {
        flatIdeas.push(...(items as InnovationIdea[]))
      }

      if (flatIdeas.length === 0) {
        setError('暂无生成结果，请调整参数后重试')
      } else {
        // Append new ideas to existing ones instead of replacing
        setIdeas(prev => [...prev, ...flatIdeas])
      }
    } catch (err: unknown) {
      setError(getApiError(err, '生成失败，请检查 Python 后端和 API 配置'))
    }

    setGenerating(false)
  }, [genre, style, keywords, avoidPatterns, ideaType])

  // ── Expand ─────────────────────────────────────────────

  const handleExpand = useCallback(async (idea: InnovationIdea) => {
    setSelectedIdea(idea)
    setExpanding(true)
    setExpandedOutline(null)

    try {
      const result = await api.innovationExpand(idea)
      if (result.success) {
        setExpandedOutline(result.outline)
      } else {
        setExpandedOutline({ error: result.error || '展开失败' })
      }
    } catch (err: unknown) {
      setExpandedOutline({ error: getApiError(err, '展开失败') })
    }

    setExpanding(false)
  }, [])

  // ── Compose ────────────────────────────────────────────

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleCompose = useCallback(async () => {
    if (selectedIds.size < 2) return

    const selectedIdeas = ideas.filter(i => selectedIds.has(i.id))
    setComposing(true)
    setComposedFramework(null)

    try {
      const result = await api.innovationCompose({
        ideas: selectedIdeas,
        genre,
        style,
      })
      if (result.success) {
        setComposedFramework(result.framework)
      } else {
        setError(result.error || '组合失败')
      }
    } catch (err: unknown) {
      setError(getApiError(err, '组合失败'))
    }

    setComposing(false)
  }, [selectedIds, ideas, genre, style])

  // ── Create project from compose result ─────────────────

  const handleCreateFromCompose = useCallback(() => {
    if (composedFramework && onCreateProject) {
      const title = composedFramework.title || '未命名作品'
      onCreateProject(title, composedFramework, genre)
      onClose?.()
    }
  }, [composedFramework, onCreateProject, onClose, genre])

  // ── Save to materials library ──────────────────────────

  const handleSaveToLibrary = useCallback(() => {
    if (composedFramework) {
      try {
        const saved = JSON.parse(localStorage.getItem('wenforge-materials') || '[]')
        saved.push({
          id: `mat_${Date.now()}`,
          savedAt: new Date().toISOString(),
          framework: composedFramework,
        })
        localStorage.setItem('wenforge-materials', JSON.stringify(saved))
        alert('已保存到素材库！')
      } catch {
        alert('保存失败，请重试')
      }
    }
  }, [composedFramework])

  // ── Toggle favorite ────────────────────────────────────

  const toggleFavorite = useCallback((id: string) => {
    setFavorites(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  // ── Insert outline into editor ─────────────────────────

  const handleInsertOutline = useCallback(() => {
    if (expandedOutline && onInsertOutline) {
      onInsertOutline(expandedOutline)
      onClose?.()
    }
  }, [expandedOutline, onInsertOutline, onClose])

  // ── Render expanded detail ─────────────────────────────

  const renderDetail = () => {
    if (!selectedIdea) return null
    return (
      <div className="innovation-detail">
        <div className="innovation-detail-header">
          <button className="innovation-back-btn" onClick={() => { setSelectedIdea(null); setExpandedOutline(null) }}>
            ← 返回列表
          </button>
          <h3>{selectedIdea.title}</h3>
          <div className="innovation-detail-meta">
            <span className="innovation-type-badge" style={{ background: TYPE_COLORS[selectedIdea.type] || '#6b7280' }}>
              {TYPE_LABELS[selectedIdea.type] || selectedIdea.type}
            </span>
            <span className="innovation-score-badge" style={{ background: scoreColor(selectedIdea.innovation_score) }}>
              {selectedIdea.innovation_score}分
            </span>
          </div>
        </div>

        {/* Compose result banner in detail view */}
        {composedFramework && (
          <div className="innovation-compose-banner" onClick={() => { setSelectedIdea(null); setExpandedOutline(null) }}>
            <span className="innovation-compose-banner-icon">✓</span>
            <span>已有组合结果，</span>
            <span className="innovation-compose-banner-link">点击返回列表查看 →</span>
          </div>
        )}

        <div className="innovation-detail-section">
          <label>详细描述</label>
          <p>{selectedIdea.description}</p>
        </div>

        <div className="innovation-detail-section">
          <label>一句话卖点</label>
          <p className="innovation-hook-text">{selectedIdea.hook}</p>
        </div>

        {selectedIdea.tags.length > 0 && (
          <div className="innovation-detail-section">
            <label>标签</label>
            <div className="innovation-tags">
              {selectedIdea.tags.map(t => <span key={t} className="innovation-tag">{t}</span>)}
            </div>
          </div>
        )}

        {selectedIdea.similar_works.length > 0 && (
          <div className="innovation-detail-section">
            <label>类似作品</label>
            <ul className="innovation-similar-list">
              {selectedIdea.similar_works.map(w => <li key={w}>{w}</li>)}
            </ul>
          </div>
        )}

        {selectedIdea.avoid_patterns.length > 0 && (
          <div className="innovation-detail-section">
            <label>需避免的套路</label>
            <ul className="innovation-avoid-list">
              {selectedIdea.avoid_patterns.map(p => <li key={p}>{p}</li>)}
            </ul>
          </div>
        )}

        {/* Expanded outline */}
        {expanding && (
          <div className="innovation-loading">正在展开为完整大纲...</div>
        )}

        {expandedOutline && !expanding && (
          <div className="innovation-outline-card">
            <h4>故事大纲</h4>
            {expandedOutline.error ? (
              <p className="innovation-error-text">{expandedOutline.error}</p>
            ) : (
              <>
                <div className="innovation-outline-field">
                  <label>作品标题</label>
                  <p>{expandedOutline.title || '未命名'}</p>
                </div>
                <div className="innovation-outline-field">
                  <label>核心卖点</label>
                  <p>{expandedOutline.hook || '无'}</p>
                </div>
                <div className="innovation-outline-field">
                  <label>世界观设定</label>
                  <p>{expandedOutline.world_setting || '无'}</p>
                </div>
                {expandedOutline.prototype && (
                  <div className="innovation-outline-field">
                    <label>主角设定</label>
                    <p>{expandedOutline.prototype}</p>
                  </div>
                )}
                {expandedOutline.protagonist && (
                  <div className="innovation-outline-field">
                    <label>主角</label>
                    <p>{expandedOutline.protagonist.name} — {expandedOutline.protagonist.description}</p>
                  </div>
                )}
                {expandedOutline.story_arcs && (
                  <div className="innovation-outline-field">
                    <label>故事主线</label>
                    <p>{typeof expandedOutline.story_arcs === 'string' ? expandedOutline.story_arcs : expandedOutline.story_arcs.join(' → ')}</p>
                  </div>
                )}
                {expandedOutline.target_audience && (
                  <div className="innovation-outline-field">
                    <label>目标读者</label>
                    <p>{expandedOutline.target_audience}</p>
                  </div>
                )}
                {expandedOutline.estimated_chapters && (
                  <div className="innovation-outline-field">
                    <label>预计篇幅</label>
                    <p>{expandedOutline.estimated_chapters} 章</p>
                  </div>
                )}
                {expandedOutline.chapter_outlines && expandedOutline.chapter_outlines.length > 0 && (
                  <div className="innovation-outline-field">
                    <label>章节大纲</label>
                    <ol className="innovation-chapter-list">
                      {expandedOutline.chapter_outlines.map((c: string, i: number) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ol>
                  </div>
                )}
                {onInsertOutline && (
                  <button className="innovation-insert-btn" onClick={handleInsertOutline}>
                    使用此大纲
                  </button>
                )}
              </>
            )}
          </div>
        )}

        <button className="innovation-expand-btn" onClick={() => handleExpand(selectedIdea)} disabled={expanding}>
          {expanding ? '展开中...' : '重新生成大纲'}
        </button>
      </div>
    )
  }

  // ── Render compose view ────────────────────────────────

  const updateDraftField = useCallback((field: string, value: string) => {
    setDraftFramework(prev => prev ? { ...prev, [field]: value } : prev)
  }, [])

  const handleEditCompose = useCallback(() => {
    if (composedFramework) {
      setDraftFramework(JSON.parse(JSON.stringify(composedFramework)))
      setEditingCompose(true)
    }
  }, [composedFramework])

  const handleSaveCompose = useCallback(() => {
    if (draftFramework) {
      setComposedFramework(draftFramework)
    }
    setEditingCompose(false)
  }, [draftFramework])

  const handleCancelCompose = useCallback(() => {
    setEditingCompose(false)
    setDraftFramework(null)
  }, [])

  const renderCompose = () => {
    const fw = editingCompose ? draftFramework : composedFramework
    if (!fw) return null
    const isEditing = editingCompose

    return (
      <div className="innovation-compose-result" ref={composeRef}>
        <h4>组合故事框架</h4>
        <div className="innovation-compose-score">
          组合创新度: <strong style={{ color: scoreColor(fw.compose_score || 5) }}>
            {fw.compose_score}/10
          </strong>
        </div>

        {/* Title */}
        <div className="innovation-outline-field">
          <label>标题</label>
          {isEditing ? (
            <input className="innovation-compose-input" value={fw.title || ''} onChange={e => updateDraftField('title', e.target.value)} />
          ) : (
            <p>{fw.title}</p>
          )}
        </div>

        {/* Hook */}
        <div className="innovation-outline-field">
          <label>核心卖点</label>
          {isEditing ? (
            <textarea className="innovation-compose-textarea" rows={2} value={fw.hook || ''} onChange={e => updateDraftField('hook', e.target.value)} />
          ) : (
            <p>{fw.hook}</p>
          )}
        </div>

        {/* World setting */}
        <div className="innovation-outline-field">
          <label>世界观</label>
          {isEditing ? (
            <textarea className="innovation-compose-textarea" rows={3} value={fw.world_setting || ''} onChange={e => updateDraftField('world_setting', e.target.value)} />
          ) : (
            <p>{fw.world_setting}</p>
          )}
        </div>

        {/* Core conflict */}
        <div className="innovation-outline-field">
          <label>核心冲突</label>
          {isEditing ? (
            <textarea className="innovation-compose-textarea" rows={2} value={fw.core_conflict || ''} onChange={e => updateDraftField('core_conflict', e.target.value)} />
          ) : (
            <p>{fw.core_conflict}</p>
          )}
        </div>

        {/* Story arcs */}
        {(fw.story_arcs && fw.story_arcs.length > 0) || isEditing ? (
          <div className="innovation-outline-field">
            <label>{isEditing ? '故事弧（每行一个）' : '故事弧'}</label>
            {isEditing ? (
              <textarea className="innovation-compose-textarea" rows={4}
                value={(fw.story_arcs || []).join('\n')}
                onChange={e => setDraftFramework(prev => prev ? { ...prev, story_arcs: e.target.value.split('\n').filter(Boolean) } : prev)} />
            ) : (
              <ol className="innovation-chapter-list">
                {fw.story_arcs!.map((a: string, i: number) => <li key={i}>{a}</li>)}
              </ol>
            )}
          </div>
        ) : null}

        {/* Note */}
        {isEditing || fw.note ? (
          <div className="innovation-outline-field">
            <label>组合说明</label>
            {isEditing ? (
              <textarea className="innovation-compose-textarea" rows={2} value={fw.note || ''} onChange={e => updateDraftField('note', e.target.value)} />
            ) : (
              <p className="innovation-compose-note">{fw.note}</p>
            )}
          </div>
        ) : null}

        {/* Actions */}
        <div className="innovation-compose-actions">
          {isEditing ? (
            <>
              <button className="innovation-create-btn" onClick={handleSaveCompose}>保存修改</button>
              <button className="innovation-compose-cancel-btn" onClick={handleCancelCompose}>取消</button>
            </>
          ) : (
            <>
              <button className="innovation-create-btn" onClick={handleCreateFromCompose}>创建为小说</button>
              <button className="innovation-save-btn" onClick={handleSaveToLibrary}>保存到素材库</button>
              <button className="innovation-edit-btn" onClick={handleEditCompose}>编辑</button>
            </>
          )}
        </div>
      </div>
    )
  }

  // ── Render idea card ───────────────────────────────────

  const renderIdeaCard = (idea: InnovationIdea) => {
    const isSelected = selectedIds.has(idea.id)
    const isFavorite = favorites.has(idea.id)

    return (
      <div key={idea.id} className={`innovation-card ${isSelected ? 'selected' : ''}`}>
        <div className="innovation-card-header">
          <div className="innovation-card-title-row">
            {selectedIds.size > 0 && (
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => toggleSelect(idea.id)}
                className="innovation-checkbox"
              />
            )}
            <span className="innovation-type-badge" style={{ background: TYPE_COLORS[idea.type] || '#6b7280' }}>
              {TYPE_LABELS[idea.type] || idea.type}
            </span>
            <h4 className="innovation-card-title">{idea.title}</h4>
          </div>
          <div className="innovation-card-actions-top">
            <span className="innovation-score-badge" style={{ background: scoreColor(idea.innovation_score) }}
              title={scoreLabel(idea.innovation_score)}>
              {idea.innovation_score}
            </span>
            <button
              className={`innovation-fav-btn ${isFavorite ? 'faved' : ''}`}
              onClick={() => toggleFavorite(idea.id)}
              title={isFavorite ? '取消收藏' : '收藏'}
            >
              {isFavorite ? '★' : '☆'}
            </button>
          </div>
        </div>

        <p className="innovation-card-desc">{idea.description}</p>
        <p className="innovation-card-hook">卖点: {idea.hook}</p>

        {idea.tags.length > 0 && (
          <div className="innovation-tags">
            {idea.tags.map(t => <span key={t} className="innovation-tag">{t}</span>)}
          </div>
        )}

        <div className="innovation-card-actions">
          <button className="innovation-btn" onClick={() => handleExpand(idea)}>
            展开大纲
          </button>
          <button
            className={`innovation-btn ${isSelected ? 'active' : ''}`}
            onClick={() => toggleSelect(idea.id)}
          >
            {isSelected ? '已选择' : '选择组合'}
          </button>
        </div>
      </div>
    )
  }

  // ── Main render ────────────────────────────────────────

  return (
    <div className="innovation-library">
      {/* Header */}
      <div className="innovation-header">
        <div className="innovation-header-top">
          <h2>灵犀</h2>
          {onClose && (
            <button className="innovation-close-btn" onClick={onClose}>×</button>
          )}
        </div>
        <p className="innovation-subtitle">
          灵犀 — AI驱动的创意灵感引擎，基于网文市场分析、经典套路解构和差异化搜索
        </p>
      </div>

      {/* Generation Form */}
      <div className="innovation-form">
        <div className="innovation-form-row">
          <div className="innovation-field">
            <label>题材</label>
            <input
              value={genre}
              onChange={e => setGenre(e.target.value)}
              placeholder="如：玄幻、仙侠、悬疑"
              className="innovation-input"
            />
          </div>
          <div className="innovation-field">
            <label>风格</label>
            <select value={style} onChange={e => setStyle(e.target.value)} className="innovation-select">
              <option value="流畅直白">流畅直白</option>
              <option value="细腻描写">细腻描写</option>
              <option value="幽默诙谐">幽默诙谐</option>
              <option value="严肃正剧">严肃正剧</option>
              <option value="古风典雅">古风典雅</option>
              <option value="轻松爽文">轻松爽文</option>
            </select>
          </div>
          <div className="innovation-field">
            <label>创新维度</label>
            <select value={ideaType} onChange={e => setIdeaType(e.target.value)} className="innovation-select">
              {IDEA_TYPES.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="innovation-form-row">
          <div className="innovation-field flex-2">
            <label>关键词（逗号分隔）</label>
            <input
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              placeholder="如：赛博朋克、修仙、系统流"
              className="innovation-input"
            />
          </div>
          <div className="innovation-field flex-2">
            <label>需避免的套路</label>
            <input
              value={avoidPatterns}
              onChange={e => setAvoidPatterns(e.target.value)}
              placeholder="如：签到系统、神豪流"
              className="innovation-input"
            />
          </div>
        </div>

        <div className="innovation-form-actions">
          <div className="innovation-form-actions-left">
            <button
              className="innovation-random-btn"
              onClick={handleRandom}
              type="button"
              title="随机填写所有参数"
            >
              🎲 随机填写
            </button>
          </div>
          <button
            className="innovation-generate-btn"
            onClick={handleGenerate}
            disabled={generating || !genre.trim()}
          >
            {generating ? '生成中...' : '✨ 生成灵感'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && <div className="innovation-error">{error}</div>}

      {/* Idea Cards or Detail View */}
      {selectedIdea ? (
        renderDetail()
      ) : (
        <>
          {/* Selection tools */}
          {ideas.length > 0 && (
            <div className="innovation-toolbar">
              <div className="innovation-toolbar-left">
                <span className="innovation-count">{ideas.length} 个灵感</span>
                <button
                  className="innovation-toolbar-btn text-warn"
                  onClick={() => { setIdeas([]); setSelectedIds(new Set()); setComposedFramework(null) }}
                  title="清空所有灵感"
                >
                  清空列表
                </button>
              </div>
              <div className="innovation-toolbar-actions">
                <button
                  className="innovation-toolbar-btn"
                  onClick={() => setSelectedIds(new Set(ideas.map(i => i.id)))}
                >
                  全选
                </button>
                <button
                  className="innovation-toolbar-btn"
                  onClick={() => setSelectedIds(new Set())}
                >
                  取消选择
                </button>
                <button
                  className="innovation-compose-btn"
                  onClick={handleCompose}
                  disabled={selectedIds.size < 2 || composing}
                >
                  {composing ? '组合中...' : `组合所选 (${selectedIds.size})`}
                </button>
              </div>
            </div>
          )}

          {/* Idea List */}
          <div className="innovation-list">
            {ideas.map(renderIdeaCard)}

            {ideas.length === 0 && !generating && !error && (
              <div className="innovation-empty">
                <p>填写上方参数，点击"生成灵感"开始</p>
                <p className="innovation-empty-hint">
                  灵犀支持五大创新维度：题材融合、金手指创新、世界观反转、人物设定创新、情节结构创新
                </p>
              </div>
            )}

            {generating && (
              <div className="innovation-loading">
                <span>AI 正在构思创意...</span>
              </div>
            )}
          </div>

          {/* Compose Result */}
          {composedFramework && renderCompose()}
        </>
      )}
    </div>
  )
}
