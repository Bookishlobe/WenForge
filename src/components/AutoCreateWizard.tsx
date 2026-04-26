import { useState } from 'react'

interface Props {
  projectName: string
  genre: string
  onStart: (config: AutoWriteConfig) => void
  onCancel: () => void
}

export interface AutoWriteConfig {
  premise: string
  protagonist: string
  style: string
  totalChapters: number
  chapterLength: 'short' | 'medium' | 'long'
}

const STYLE_OPTIONS = [
  { value: '流畅直白', label: '流畅直白', desc: '简洁明快，适合快速阅读' },
  { value: '细腻描写', label: '细腻描写', desc: '注重细节和心理刻画' },
  { value: '幽默诙谐', label: '幽默诙谐', desc: '对话风趣，情节轻松' },
  { value: '轻松爽文', label: '轻松爽文', desc: '节奏爽快，主角强势' },
  { value: '严肃正剧', label: '严肃正剧', desc: '情节严谨，有深度' },
  { value: '古风典雅', label: '古风典雅', desc: '文笔典雅，古典韵味' },
]

const LENGTH_OPTIONS = [
  { value: 10, label: '10 章', desc: '短篇，快速出成品' },
  { value: 20, label: '20 章', desc: '中篇，完整故事线' },
  { value: 30, label: '30 章', desc: '中长篇，情节丰富' },
  { value: 50, label: '50 章', desc: '长篇，宏大叙事' },
  { value: 100, label: '100 章', desc: '超长篇，世界观完整' },
]

const CHAPTER_LENGTH_OPTIONS = [
  { value: 'short' as const, label: '精简（~2000 字/章）', desc: '节奏快' },
  { value: 'medium' as const, label: '标准（~3000 字/章）', desc: '适中' },
  { value: 'long' as const, label: '丰富（~5000 字/章）', desc: '内容充实' },
]

export function AutoCreateWizard({ projectName, genre, onStart, onCancel }: Props) {
  const [step, setStep] = useState(1)
  const [premise, setPremise] = useState('')
  const [protagonist, setProtagonist] = useState('')
  const [style, setStyle] = useState('流畅直白')
  const [totalChapters, setTotalChapters] = useState(20)
  const [chapterLength, setChapterLength] = useState<'short' | 'medium' | 'long'>('medium')

  const handleStart = () => {
    if (!premise.trim()) return
    onStart({
      premise: premise.trim(),
      protagonist: protagonist.trim() || '未命名',
      style,
      totalChapters,
      chapterLength,
    })
  }

  return (
    <div className="auto-wizard">
      {/* Header */}
      <div className="wizard-header">
        <h2>AI 自动创作</h2>
        <p className="wizard-subtitle">
          填写以下信息，AI 将为你自动创作小说《{projectName}》
        </p>
      </div>

      {/* Step indicator */}
      <div className="wizard-steps">
        <div className={`wizard-step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'done' : ''}`}>
          <div className="step-number">{step > 1 ? '✓' : '1'}</div>
          <span>故事设定</span>
        </div>
        <div className="step-connector" />
        <div className={`wizard-step ${step >= 2 ? 'active' : ''}`}>
          <div className="step-number">{step > 2 ? '✓' : '2'}</div>
          <span>写作设置</span>
        </div>
      </div>

      {/* Step 1: Story Basics */}
      {step === 1 && (
        <div className="wizard-step-content">
          <div className="wizard-field">
            <label>
              <span className="field-label">题材</span>
              <span className="field-value">{genre || '未选择'}</span>
            </label>
          </div>

          <div className="wizard-field">
            <label>
              <span className="field-label">核心创意 <span className="required">*</span></span>
            </label>
            <textarea
              value={premise}
              onChange={e => setPremise(e.target.value)}
              placeholder="用几句话描述你的故事核心创意，例如：&#10;一位现代程序员穿越到修仙世界，用编程思维破解上古阵法..."
              rows={4}
              autoFocus
            />
            <p className="field-hint">故事的核心卖点，越具体 AI 创作越精准</p>
          </div>

          <div className="wizard-field">
            <label>
              <span className="field-label">主角名字</span>
            </label>
            <input
              value={protagonist}
              onChange={e => setProtagonist(e.target.value)}
              placeholder="如：林尘、苏瑶、叶凡..."
            />
            <p className="field-hint">留空则由 AI 自动生成</p>
          </div>

          <div className="wizard-actions">
            <button className="btn-secondary" onClick={onCancel}>取消</button>
            <button
              className="btn-primary"
              onClick={() => setStep(2)}
              disabled={!premise.trim()}
            >
              下一步 →
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Writing Settings */}
      {step === 2 && (
        <div className="wizard-step-content">
          <div className="wizard-field">
            <label className="field-label">写作风格</label>
            <div className="style-grid">
              {STYLE_OPTIONS.map(opt => (
                <div
                  key={opt.value}
                  className={`style-card ${style === opt.value ? 'selected' : ''}`}
                  onClick={() => setStyle(opt.value)}
                >
                  <div className="style-name">{opt.label}</div>
                  <div className="style-desc">{opt.desc}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="wizard-field">
            <label className="field-label">目标篇幅</label>
            <div className="chip-group">
              {LENGTH_OPTIONS.map(opt => (
                <div
                  key={opt.value}
                  className={`chip ${totalChapters === opt.value ? 'selected' : ''}`}
                  onClick={() => setTotalChapters(opt.value)}
                >
                  <div className="chip-label">{opt.label}</div>
                  <div className="chip-desc">{opt.desc}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="wizard-field">
            <label className="field-label">每章字数</label>
            <div className="chip-group">
              {CHAPTER_LENGTH_OPTIONS.map(opt => (
                <div
                  key={opt.value}
                  className={`chip ${chapterLength === opt.value ? 'selected' : ''}`}
                  onClick={() => setChapterLength(opt.value)}
                >
                  <div className="chip-label">{opt.label}</div>
                  <div className="chip-desc">{opt.desc}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="wizard-summary">
            <p>
              将创作 <strong>{totalChapters} 章</strong>，
              风格 <strong>{style}</strong>，
              每章约 <strong>{chapterLength === 'short' ? '2000' : chapterLength === 'medium' ? '3000' : '5000'}</strong> 字
            </p>
          </div>

          <div className="wizard-actions">
            <button className="btn-secondary" onClick={() => setStep(1)}>← 上一步</button>
            <button
              className="btn-start"
              onClick={handleStart}
              disabled={!premise.trim()}
            >
              🚀 开始 AI 自动创作
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
