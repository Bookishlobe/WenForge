export interface VersionRecord {
  id: string
  timestamp: string
  message: string
  type: VersionType
}

export type VersionType = 'ai_draft' | 'user_edit'

export interface ChapterVersion {
  versions: VersionRecord[]
  current: string
}

export interface VersionIndex {
  chapters: Record<string, ChapterVersion>
}

export interface VersionDiff {
  versionId: string
  chapterFile: string
  timestamp: string
  patches: PatchEntry[]
}

export interface PatchEntry {
  startLine: number
  oldText: string
  newText: string
}
