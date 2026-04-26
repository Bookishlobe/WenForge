export type {
  AuthorProfile,
  AuthorStyleSettings,
  WritingStyle,
  StyleProfile,
  AuthorSpace,
} from './author'

export type {
  BookMeta,
  BookStatus,
  ChapterFile,
  BookOutline,
  VolumeOutline,
  ChapterOutline,
} from './book'

export type {
  VersionRecord,
  VersionType,
  ChapterVersion,
  VersionIndex,
  VersionDiff,
  PatchEntry,
} from './version'

// Re-export existing types from types.ts for backward compatibility
export type {
  Project,
  Chapter,
  ModelConfig,
  AppSettings,
  UserSettings,
  WindowAPI,
} from '../types'
