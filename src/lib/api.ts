import type { Project, Chapter } from '../types';

const api = window.wenforge;

// Project API
export async function listProjects(): Promise<Project[]> {
  return api.listProjects();
}

export async function createProject(title: string, author?: string, genre?: string): Promise<Project> {
  return api.createProject({ title, author, genre });
}

// Chapter API
export async function listChapters(projectName: string): Promise<Chapter[]> {
  return api.listChapters(projectName);
}

export async function readChapter(projectName: string, chapterFile: string): Promise<string> {
  return api.readChapter(projectName, chapterFile);
}

export async function saveChapter(projectName: string, chapterFile: string, content: string): Promise<boolean> {
  return api.saveChapter(projectName, chapterFile, content);
}

export async function createChapter(projectName: string, title: string): Promise<string> {
  return api.createChapter(projectName, title);
}

export async function deleteChapter(projectName: string, chapterFile: string): Promise<boolean> {
  return api.deleteChapter(projectName, chapterFile);
}

// AI API via Python sidecar
export async function pythonRequest<T>(endpoint: string, data: unknown): Promise<T> {
  return api.pythonRequest<T>(endpoint, data);
}

export async function aiGenerate(params: {
  prompt: string;
  context?: string;
  model?: string;
  provider?: string;
  temperature?: number;
  maxTokens?: number;
}): Promise<{ text: string; tokenCount?: number; cost?: number }> {
  return pythonRequest('/api/generate', params);
}

export async function aiContinue(
  precedingText: string,
  style?: string
): Promise<{ text: string }> {
  return pythonRequest('/api/continue', { text: precedingText, style });
}

export async function checkHealth(): Promise<boolean> {
  try {
    const result = await pythonRequest<{ status: string }>('/api/health', {});
    return result.status === 'ok';
  } catch {
    return false;
  }
}

// Innovation Library API (灵犀)
export interface InnovationIdea {
  id: string;
  type: string;
  title: string;
  description: string;
  hook: string;
  innovation_score: number;
  market_potential: string;
  similar_works: string[];
  tags: string[];
  avoid_patterns: string[];
  source: string;
}

export async function innovationGenerate(params: {
  idea_type?: string;
  genre?: string;
  style?: string;
  keywords?: string[];
  avoid_patterns?: string[];
  count?: number;
}): Promise<{ ideas: Record<string, InnovationIdea[]>; success: boolean }> {
  return pythonRequest('/api/innovation/generate', params);
}

export async function innovationExpand(idea: InnovationIdea): Promise<InnovationExpanded> {
  return pythonRequest('/api/innovation/expand', { idea });
}

export async function innovationCompose(params: {
  ideas: InnovationIdea[];
  genre?: string;
  style?: string;
}): Promise<InnovationFramework> {
  return pythonRequest('/api/innovation/compose', params);
}

export async function innovationScore(ideas: InnovationIdea[]): Promise<{
  ideas: InnovationIdea[]; success: boolean
}> {
  return pythonRequest('/api/innovation/score', { ideas });
}

// ── Auto-write types ─────────────────────────────────────

export interface StoryOutline {
  title: string
  world_setting: string
  chapter_outlines: string[]
  main_characters: Array<{ name: string; role: string; description: string }>
}

export interface ChapterResult {
  text: string
  title?: string
  success: boolean
  error?: string
}

export interface InnovationExpanded {
  outline: Record<string, unknown>
  success: boolean
  error?: string
}

export interface InnovationFramework {
  framework: Record<string, unknown>
  success: boolean
  error?: string
}
export async function autoGenerateOutline(config: {
  genre: string;
  premise: string;
  protagonist: string;
  style: string;
  total_chapters: number;
  chapter_length: string;
}): Promise<{ outline: StoryOutline; success: boolean; error?: string }> {
  return pythonRequest('/api/auto/outline', config);
}

export async function autoGenerateChapter(params: {
  outline: StoryOutline;
  chapter_index: number;
  chapter_outline: string;
  previous_summaries: string[];
  config: {
    genre: string;
    style: string;
    chapter_length: string;
  };
}): Promise<ChapterResult> {
  return pythonRequest('/api/auto/chapter', params);
}
