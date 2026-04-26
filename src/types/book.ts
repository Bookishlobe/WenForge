import type { WritingStyle } from './author'

export interface BookMeta {
  title: string
  authorName: string
  genre: string
  subGenre?: string
  createdAt: string
  updatedAt: string
  totalChapters: number
  totalWords: number
  status: BookStatus
  style?: WritingStyle
  description?: string
}

export type BookStatus = 'draft' | 'writing' | 'finished'

export interface ChapterFile {
  name: string
  file: string
  updatedAt: string
  wordCount?: number
  order: number
}

export interface BookOutline {
  title: string
  premise: string
  volumes: VolumeOutline[]
}

export interface VolumeOutline {
  title: string
  summary: string
  chapters: ChapterOutline[]
}

export interface ChapterOutline {
  title: string
  summary: string
  expectedWords: number
}
