interface Props {
  phase: 'outline' | 'writing' | 'done' | 'error'
  progress: { current: number; total: number }
  logs: string[]
  errorMessage?: string
  hasMoreChapters?: boolean
  onCancel: () => void
  onViewChapters: () => void
  onWriteNextChapter?: () => void
}

export function AutoWritingProgress({
  phase, progress, logs, errorMessage,
  hasMoreChapters, onCancel, onViewChapters, onWriteNextChapter,
}: Props) {
  const pct = progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0

  return (
    <div className="auto-progress">
      <div className="progress-header">
        <h2>AI 自动创作中</h2>
        <p className="progress-subtitle">
          {phase === 'outline' && '正在构思故事大纲...'}
          {phase === 'writing' && `正在创作第 ${progress.current}/${progress.total} 章...`}
          {phase === 'done' && (hasMoreChapters
            ? `已完成 ${progress.current} 章，可继续续写`
            : '创作完成！')}
          {phase === 'error' && '创作过程中出现错误'}
        </p>
      </div>

      {phase !== 'error' && (
        <div className="progress-bar-container">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${phase === 'outline' ? 5 : pct}%` }}
            />
          </div>
          <span className="progress-text">
            {phase === 'outline' ? '大纲生成中...' : `${progress.current}/${progress.total} 章`}
          </span>
        </div>
      )}

      <div className="progress-log">
        {logs.map((log, i) => (
          <div key={i} className="log-entry">
            <span className="log-time">{String(i + 1).padStart(2, '0')}</span>
            <span className="log-msg">{log}</span>
          </div>
        ))}
        {phase === 'writing' && (
          <div className="log-entry log-active">
            <span className="log-time">→</span>
            <span className="log-msg">正在生成第 {progress.current} 章...</span>
          </div>
        )}
        {phase === 'outline' && (
          <div className="log-entry log-active">
            <span className="log-time">→</span>
            <span className="log-msg">AI 正在设计世界观和人物...</span>
          </div>
        )}
      </div>

      {phase === 'error' && errorMessage && (
        <div className="progress-error">
          <p>❌ {errorMessage}</p>
        </div>
      )}

      <div className="progress-actions">
        {phase === 'writing' && (
          <button className="btn-secondary" onClick={onCancel}>
            停止生成
          </button>
        )}
        {phase === 'outline' && (
          <button className="btn-secondary" onClick={onCancel}>
            取消
          </button>
        )}
        {phase === 'done' && (
          <>
            {hasMoreChapters && onWriteNextChapter && (
              <button className="btn-primary" onClick={onWriteNextChapter}>
                续写下一章
              </button>
            )}
            <button className={hasMoreChapters ? 'btn-secondary' : 'btn-primary'} onClick={onViewChapters}>
              📖 查看已生成的章节
            </button>
          </>
        )}
        {phase === 'error' && (
          <button className="btn-primary" onClick={onViewChapters}>
            查看已生成的章节
          </button>
        )}
      </div>
    </div>
  )
}
