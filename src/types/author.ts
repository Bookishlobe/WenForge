export interface AuthorProfile {
  name: string
  penName: string
  createdAt: string
  bio?: string
}

export interface AuthorStyleSettings {
  defaultGenre?: string
  defaultStyle?: WritingStyle
  defaultWordCountPerChapter?: number
}

export type WritingStyle =
  | 'fluent'
  | 'detailed'
  | 'humorous'
  | 'light'
  | 'serious'
  | 'classical'

export interface StyleProfile {
  vocabulary: {
    freqWords: Record<string, number>
    rareWords: string[]
    functionWordRatio: number
  }
  syntax: {
    avgSentenceLength: number
    clauseRatio: number
    avgParagraphLength: number
    dialogueRatio: number
    descriptionRatio: number
  }
  lastUpdated: string
  sampleCount: number
}

export interface AuthorSpace {
  path: string
  profile: AuthorProfile
  styleSettings: AuthorStyleSettings
  styleProfile: StyleProfile
}
