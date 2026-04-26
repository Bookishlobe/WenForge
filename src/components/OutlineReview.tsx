import { useState } from 'react'
import type { StoryOutline } from '../lib/api'

interface OutlineReviewProps {
  outline: StoryOutline
  onStart: (totalChapters: number, batchSize: number) => void
  onCancel: () => void
}

export function OutlineReview({ outline, onStart, onCancel }: OutlineReviewProps) {
  const totalAvailable = outline.chapter_outlines?.length || 0
  const [totalChapters, setTotalChapters] = useState(Math.min(10, totalAvailable))
  const [batchSize, setBatchSize] = useState(3)

  return (
    <div className="outline-review">
      <div className="outline-review-header">
        <h2>故事大纲预览</h2>
        <p className="outline-review-subtitle">请审阅 AI 生成的故事大纲，确认后选择要生成的章节数量</p>
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
            <div
              key={i}
              className={`outline-chapter-item ${i >= totalChapters ? 'outline-chapter-disabled' : ''}`}
            >
              <span className="outline-chapter-num">{i + 1}</span>
              <span className="outline-chapter-desc">{co}</span>
              {i >= totalChapters && <span className="outline-chapter-badge">不生成</span>}
            </div>
          ))}
        </div>
      </div>

      <div className="outline-settings">
        <div className="outline-setting">
          <label>生成章节数</label>
          <div className="outline-slider-row">
            <input
              type="range"
              min={1}
              max={totalAvailable}
              value={totalChapters}
              onChange={e => setTotalChapters(Number(e.target.value))}
              className="outline-slider"
            />
            <span className="outline-slider-value">{totalChapters} 章</span>
          </div>
        </div>
        <div className="outline-setting">
          <label>每批生成</label>
          <div className="outline-batch-options">
            {[1, 2, 3].map(n => (
              <button
                key={n}
                className={`outline-batch-btn ${batchSize === n ? 'active' : ''}`}
                onClick={() => setBatchSize(n)}
              >
                {n} 章
              </button>
            ))}
          </div>
          <p className="outline-setting-hint">每批不超过 3 章，生成后可预览结果再继续</p>
        </div>
      </div>

      <div className="outline-actions">
        <button className="btn-secondary" onClick={onCancel}>返回修改</button>
        <button className="btn-primary" onClick={() => onStart(totalChapters, batchSize)}>
          开始生成 {totalChapters} 章
        </button>
      </div>
    </div>
  )
}
