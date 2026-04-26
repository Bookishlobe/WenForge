import type { StoryOutline } from '../lib/api'

interface OutlineReviewProps {
  outline: StoryOutline
  onStart: () => void
  onCancel: () => void
}

export function OutlineReview({ outline, onStart, onCancel }: OutlineReviewProps) {
  const totalAvailable = outline.chapter_outlines?.length || 0
  const initialCount = Math.min(3, totalAvailable)

  return (
    <div className="outline-review">
      <div className="outline-review-header">
        <h2>故事大纲预览</h2>
        <p className="outline-review-subtitle">请审阅 AI 生成的故事大纲，确认后先创作前 {initialCount} 章</p>
      </div>

      <div className="outline-info">
        <div className="outline-info-item">
          <span className="outline-info-label">书名</span>
          <span className="outline-info-value">{outline.title}</span>
        </div>
        <div className="outline-info-item">
          <span className="outline-info-label">世界观</span>
          <span className="outline-info-value">{outline.world_setting}</span>
        </div>
        {outline.main_characters?.length > 0 && (
          <div className="outline-info-item">
            <span className="outline-info-label">主要角色</span>
            <div className="outline-characters">
              {outline.main_characters.map((c, i) => (
                <span key={i} className="outline-character-tag">
                  {c.name}（{c.role}）
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="outline-chapters-section">
        <h3>章节大纲（共 {totalAvailable} 章）</h3>
        <div className="outline-chapter-list">
          {outline.chapter_outlines?.map((co, i) => (
            <div key={i} className="outline-chapter-item">
              <span className={`outline-chapter-num ${i >= initialCount ? 'outline-chapter-future' : ''}`}>
                {i + 1}
              </span>
              <span className="outline-chapter-desc">{co}</span>
              {i < initialCount && <span className="outline-chapter-badge outline-badge-active">先创作</span>}
              {i >= initialCount && <span className="outline-chapter-badge">后续续写</span>}
            </div>
          ))}
        </div>
        <p className="outline-chapter-hint">先创作前 {initialCount} 章，完成后可继续续写后续章节</p>
      </div>

      <div className="outline-actions">
        <button className="btn-secondary" onClick={onCancel}>返回修改</button>
        <button className="btn-primary" onClick={onStart}>
          开始生成前 {initialCount} 章
        </button>
      </div>
    </div>
  )
}
