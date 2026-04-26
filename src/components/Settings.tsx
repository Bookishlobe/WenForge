import { useState, useEffect } from 'react'
import type { UserSettings } from '../types'

interface Props {
  onClose: () => void
  onSettingsChange?: (settings: UserSettings) => void
}

const DEFAULT_SETTINGS: UserSettings = {
  openaiKey: '',
  openaiModel: 'gpt-4o-mini',
  claudeKey: '',
  claudeModel: 'claude-sonnet-4-20250514',
  deepseekKey: '',
  deepseekModel: 'deepseek-v4-flash',
  deepseekEndpoint: 'https://api.deepseek.com',
  writingModel: 'claude-haiku-3-5-20251022',
  polishingModel: 'claude-opus-4-20250514',
  localEndpoint: 'http://localhost:11434',
  localModel: 'qwen2.5:7b',
  activeProvider: {
    writing: 'claude',
    polishing: 'claude',
    outline: 'claude',
  },
}

// ── Provider definitions ─────────────────────────────────

type ProviderId = 'openai' | 'claude' | 'deepseek' | 'local'

interface ProviderDef {
  key: ProviderId
  label: string
  icon: string
  color: string
  apiKeyLabel: string
  models: { value: string; label: string }[]
  docUrl?: string
}

const PROVIDERS: ProviderDef[] = [
  {
    key: 'openai',
    label: 'OpenAI',
    icon: '○',
    color: '#10a37f',
    apiKeyLabel: 'API Key (sk-...)',
    models: [
      { value: 'gpt-4o', label: 'GPT-4o' },
      { value: 'gpt-4o-mini', label: 'GPT-4o-mini' },
      { value: 'o3-mini', label: 'o3-mini' },
    ],
    docUrl: 'https://platform.openai.com/api-keys',
  },
  {
    key: 'claude',
    label: 'Anthropic Claude',
    icon: '✦',
    color: '#d97706',
    apiKeyLabel: 'API Key (sk-ant-...)',
    models: [
      { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4' },
      { value: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
      { value: 'claude-haiku-3-5-20251022', label: 'Claude Haiku 3.5' },
    ],
    docUrl: 'https://console.anthropic.com/',
  },
  {
    key: 'deepseek',
    label: 'DeepSeek',
    icon: '◈',
    color: '#4f46e5',
    apiKeyLabel: 'API Key (sk-...)',
    models: [
      { value: 'deepseek-v4-flash', label: 'DeepSeek-V4-Flash (deepseek-v4-flash)' },
      { value: 'deepseek-v4-pro', label: 'DeepSeek-V4-Pro (deepseek-v4-pro)' },
      { value: 'deepseek-chat', label: 'DeepSeek-V3 (deepseek-chat)' },
      { value: 'deepseek-reasoner', label: 'DeepSeek-R1 (deepseek-reasoner)' },
    ],
    docUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    key: 'local',
    label: '本地模型 (Ollama)',
    icon: '⬡',
    color: '#6b7280',
    apiKeyLabel: '',
    models: [
      { value: 'qwen2.5:7b', label: 'Qwen2.5-7B' },
      { value: 'qwen2.5:3b', label: 'Qwen2.5-3B' },
      { value: 'qwen2.5:1.5b', label: 'Qwen2.5-1.5B' },
      { value: 'deepseek-r1:7b', label: 'DeepSeek-R1-7B' },
    ],
  },
]

// ── Task definitions for model routing ───────────────────

const TASKS = [
  { key: 'writing' as const, label: '✍ 日常写作（经济模型）', defaultModel: 'claude-haiku-3-5-20251022' },
  { key: 'polishing' as const, label: '✦ 精修润色（旗舰模型）', defaultModel: 'claude-opus-4-20250514' },
  { key: 'outline' as const, label: '◎ 大纲/设定生成', defaultModel: 'claude-haiku-3-5-20251022' },
]

// ── Component ────────────────────────────────────────────

export function SettingsModal({ onClose, onSettingsChange }: Props) {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS)
  const [dataDir, setDataDir] = useState('')
  const [loading, setLoading] = useState(true)
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})

  useEffect(() => {
    async function load() {
      try {
        const [saved, dir] = await Promise.all([
          window.wenforge.loadSettings(),
          window.wenforge.getDataDir(),
        ])
        if (saved && Object.keys(saved).length > 0) {
          setSettings({ ...DEFAULT_SETTINGS, ...saved })
        }
        setDataDir(dir)
      } catch {
        const saved = localStorage.getItem('wenforge-settings')
        if (saved) setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(saved) })
      }
      setLoading(false)
    }
    load()
  }, [])

  const handleSave = async () => {
    // Persist to disk
    try {
      await window.wenforge.saveSettings(settings)
    } catch {
      localStorage.setItem('wenforge-settings', JSON.stringify(settings))
    }
    // Sync to Python sidecar
    try {
      await window.wenforge.pythonRequest('/api/configure', {
        openai_key: settings.openaiKey || '',
        openai_model: settings.openaiModel || '',
        claude_key: settings.claudeKey || '',
        claude_model: settings.claudeModel || '',
        deepseek_key: settings.deepseekKey || '',
        deepseek_model: settings.deepseekModel || '',
        deepseek_endpoint: settings.deepseekEndpoint || '',
        writing_model: settings.writingModel || '',
        polishing_model: settings.polishingModel || '',
        local_endpoint: settings.localEndpoint || '',
        local_model: settings.localModel || '',
      })
    } catch {}
    onSettingsChange?.(settings)
    onClose()
  }

  const update = (key: keyof UserSettings, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const updateActiveProvider = (task: string, provider: string) => {
    setSettings(prev => ({
      ...prev,
      activeProvider: { ...prev.activeProvider, [task]: provider },
    }))
  }

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal" onClick={e => e.stopPropagation()}>
          <div className="modal-body"><p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>加载中...</p></div>
        </div>
      </div>
    )
  }

  // ── Determine which provider a model belongs to ────

  const getProviderForModel = (model: string): string => {
    const ml = model.toLowerCase()
    if (ml.includes('gpt') || ml.includes('o1') || ml.includes('o3')) return 'openai'
    if (ml.includes('claude')) return 'claude'
    if (ml.includes('deepseek')) return 'deepseek'
    return 'local'
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-wide" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>⚙ 设置 - 提供商管理</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>
            数据存储目录: {dataDir || '本地'} &nbsp;|&nbsp; API Key 仅存储在本地，不会上传
          </p>

          {/* ── Provider Cards ────────────────────────────── */}
          <div className="provider-grid">
            {PROVIDERS.map(p => {
              const keyField = `${p.key}Key` as keyof UserSettings
              const modelField = `${p.key}Model` as keyof UserSettings
              const endpointField = p.key === 'local'
                ? 'localEndpoint'
                : p.key === 'deepseek'
                  ? 'deepseekEndpoint'
                  : null
              const showKey = showKeys[p.key] ?? false
              const hasKey = !!(settings[keyField] ?? '')

              return (
                <div key={p.key} className={`provider-card ${hasKey ? 'configured' : ''}`}>
                  <div className="provider-card-header" style={{ borderLeftColor: p.color }}>
                    <span className="provider-icon" style={{ color: p.color }}>{p.icon}</span>
                    <span className="provider-name">{p.label}</span>
                    {hasKey && <span className="provider-status-dot" style={{ background: p.color }} />}
                  </div>

                  <div className="provider-card-body">
                    {p.apiKeyLabel && (
                      <div className="setting-row compact">
                        <label>{p.apiKeyLabel}</label>
                        <div className="password-input-wrap">
                          <input
                            type={showKey ? 'text' : 'password'}
                            value={(settings[keyField] as string) || ''}
                            onChange={e => update(keyField, e.target.value)}
                            placeholder={showKey ? '输入 API Key...' : '••••••••••••••••'}
                          />
                          <button
                            className="toggle-vis-btn"
                            onClick={() => setShowKeys(prev => ({ ...prev, [p.key]: !prev[p.key] }))}
                            title={showKey ? '隐藏' : '显示'}
                          >
                            {showKey ? '🙈' : '👁'}
                          </button>
                        </div>
                      </div>
                    )}

                    <div className="setting-row compact">
                      <label>模型选择</label>
                      <select
                        value={(settings[modelField] as string) || ''}
                        onChange={e => update(modelField, e.target.value)}
                      >
                        {p.models.map(m => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                    </div>

                    {endpointField && (
                      <div className="setting-row compact">
                        <label>API 端点</label>
                        <input
                          value={(settings[endpointField as keyof UserSettings] as string) || ''}
                          onChange={e => update(endpointField as keyof UserSettings, e.target.value)}
                          placeholder={p.key === 'local' ? 'http://localhost:11434' : 'https://api.deepseek.com'}
                        />
                      </div>
                    )}

                    {p.docUrl && (
                      <a href={p.docUrl} target="_blank" rel="noopener noreferrer" className="provider-doc-link">
                        获取 API Key →
                      </a>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* ── Active Provider Switch ─────────────────────── */}
          <div className="setting-group">
            <h3>🔀 活跃提供商切换 <span style={{ fontWeight: 400, fontSize: 12, color: 'var(--text-muted)' }}>— 各任务当前使用的模型</span></h3>
            <div className="active-provider-switch">
              {TASKS.map(task => {
                const activeProv = settings.activeProvider?.[task.key] || getProviderForModel(
                  task.key === 'writing' ? settings.writingModel || '' :
                  task.key === 'polishing' ? settings.polishingModel || '' : ''
                )
                const currentModel = task.key === 'writing' ? settings.writingModel :
                  task.key === 'polishing' ? settings.polishingModel :
                  settings.writingModel

                return (
                  <div key={task.key} className="active-provider-row">
                    <span className="active-provider-label">{task.label}</span>
                    <div className="active-provider-controls">
                      <select
                        value={activeProv}
                        onChange={e => {
                          updateActiveProvider(task.key, e.target.value)
                          // Set default model for the selected provider
                          const prov = PROVIDERS.find(p => p.key === e.target.value)
                          if (prov && prov.models.length > 0) {
                            const modelKey = task.key === 'writing' ? 'writingModel' :
                              task.key === 'polishing' ? 'polishingModel' : 'writingModel'
                            update(modelKey as keyof UserSettings, prov.models[0].value)
                          }
                        }}
                        className="provider-select"
                      >
                        {PROVIDERS.map(p => (
                          <option key={p.key} value={p.key} disabled={!settings[`${p.key}Key` as keyof UserSettings] && p.key !== 'local'}>
                            {p.icon} {p.label} {!settings[`${p.key}Key` as keyof UserSettings] && p.key !== 'local' ? '(未配置)' : ''}
                          </option>
                        ))}
                      </select>
                      <select
                        value={currentModel || ''}
                        onChange={e => {
                          const modelKey = task.key === 'writing' ? 'writingModel' :
                            task.key === 'polishing' ? 'polishingModel' : 'writingModel'
                          update(modelKey as keyof UserSettings, e.target.value)
                        }}
                        className="model-select"
                      >
                        {PROVIDERS.find(p => p.key === activeProv)?.models.map(m => (
                          <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* ── Model Routing Table ────────────────────────── */}
          <div className="setting-group">
            <h3>📋 当前配置摘要</h3>
            <div className="routing-summary">
              {TASKS.map(task => {
                const modelName = task.key === 'writing' ? settings.writingModel :
                  task.key === 'polishing' ? settings.polishingModel : settings.writingModel
                const provName = getProviderForModel(modelName || '')
                const prov = PROVIDERS.find(p => p.key === provName)
                const hasKey = !!settings[`${provName}Key` as keyof UserSettings]
                return (
                  <div key={task.key} className="routing-row">
                    <span className="routing-task">{task.label}</span>
                    <span className="routing-arrow">→</span>
                    <span className="routing-provider" style={{ color: prov?.color }}>
                      {prov?.icon} {prov?.label || provName}
                    </span>
                    <span className="routing-model">{modelName}</span>
                    <span className={`routing-status ${hasKey || provName === 'local' ? 'ok' : 'missing'}`}>
                      {hasKey || provName === 'local' ? '✓' : '✗ Key'}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>取消</button>
          <button className="btn-primary" onClick={handleSave}>保存设置</button>
        </div>
      </div>
    </div>
  )
}
