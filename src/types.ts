export interface Project {
  name: string;
  title: string;
  author?: string;
  genre?: string;
  createdAt?: string;
}

export interface Chapter {
  name: string;
  file: string;
  updatedAt: string;
}

export interface ModelConfig {
  provider: string;
  apiKey: string;
  model: string;
  endpoint?: string;
}

export interface AppSettings {
  models: {
    writing: ModelConfig;
    polishing: ModelConfig;
    outline: ModelConfig;
  };
  styleProfile: {
    samples: string[];
    enabled: boolean;
  };
}

export interface UserSettings {
  openaiKey?: string;
  openaiModel?: string;
  claudeKey?: string;
  claudeModel?: string;
  deepseekKey?: string;
  deepseekModel?: string;
  deepseekEndpoint?: string;
  writingModel?: string;
  polishingModel?: string;
  localEndpoint?: string;
  localModel?: string;

  /** Quick-switch: which provider to use as default for each task */
  activeProvider?: {
    writing?: string;    // provider name: "openai" | "claude" | "deepseek" | "local"
    polishing?: string;
    outline?: string;
  };
}

export interface WindowAPI {
  // Local data storage
  getDataDir: () => Promise<string>;
  loadSettings: () => Promise<UserSettings>;
  saveSettings: (settings: UserSettings) => Promise<boolean>;

  // Project operations
  listProjects: () => Promise<Project[]>;
  createProject: (data: { title: string; author?: string; genre?: string }) => Promise<Project>;
  listChapters: (projectName: string) => Promise<Chapter[]>;
  readChapter: (projectName: string, chapterFile: string) => Promise<string>;
  saveChapter: (projectName: string, chapterFile: string, content: string) => Promise<boolean>;
  createChapter: (projectName: string, title: string) => Promise<string>;
  deleteChapter: (projectName: string, chapterFile: string) => Promise<boolean>;
  pythonRequest: <T>(endpoint: string, data: unknown) => Promise<T>;
  selectDirectory: () => Promise<string | null>;
}

declare global {
  interface Window {
    wenforge: WindowAPI;
  }
}
