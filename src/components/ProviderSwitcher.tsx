import type { UserSettings } from '../types'

interface Props {
  settings: UserSettings
  onOpenSettings: () => void
}

// ── Provider info ────────────────────────────────────────

const PROVIDER_META: Record<string, { label: string; icon: string; color: string }> = {
  openai: { label: 'OpenAI', icon: '○', color: '#10a37f' },
  claude: { label: 'Claude', icon: '✦', color: '#d97706' },
  deepseek: { label: 'DeepSeek', icon: '◈', color: '#4f46e5' },
  local: { label: '本地模型', icon: '⬡', color: '#6b7280' },
}

function getProviderForModel(model: string): string {
  const ml = model.toLowerCase()
  if (ml.includes('gpt') || ml.includes('o1') || ml.includes('o3')) return 'openai'
  if (ml.includes('claude')) return 'claude'
  if (ml.includes('deepseek')) return 'deepseek'
  return 'local'
}

// ── Component ────────────────────────────────────────────

export function ProviderSwitcher({ settings, onOpenSettings }: Props) {
  const writingModel = settings.writingModel || ''
  const polishingModel = settings.polishingModel || ''

  const writingProv = getProviderForModel(writingModel)
  const polishingProv = getProviderForModel(polishingModel)

  const wMeta = PROVIDER_META[writingProv] || PROVIDER_META.claude
  const pMeta = PROVIDER_META[polishingProv] || PROVIDER_META.claude

  const getKeyStatus = (prov: string): boolean => {
    if (prov === 'local') return true
    const keyField = `${prov}Key` as keyof UserSettings
    return !!(settings[keyField] as string)
  }

  return (
    <div className="provider-switcher">
      <div className="provider-switcher-info">
        <div className="ps-item" title={`写作: ${writingModel}`}>
          <span className="ps-icon" style={{ color: wMeta.color }}>{wMeta.icon}</span>
          <span className="ps-label">写作</span>
          <span className="ps-name">{wMeta.label}</span>
          {!getKeyStatus(writingProv) && <span className="ps-warn">⚠</span>}
        </div>
        <span className="ps-sep">|</span>
        <div className="ps-item" title={`润色: ${polishingModel}`}>
          <span className="ps-icon" style={{ color: pMeta.color }}>{pMeta.icon}</span>
          <span className="ps-label">润色</span>
          <span className="ps-name">{pMeta.label}</span>
          {!getKeyStatus(polishingProv) && <span className="ps-warn">⚠</span>}
        </div>
      </div>
      <button className="ps-edit-btn" onClick={onOpenSettings} title="管理提供商">
        ⚙
      </button>
    </div>
  )
}
