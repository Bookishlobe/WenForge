import '@testing-library/jest-dom'

const mockApi = {
  getDataDir: vi.fn().mockResolvedValue('/mock/data'),
  loadSettings: vi.fn().mockResolvedValue({}),
  saveSettings: vi.fn().mockResolvedValue(true),
  listProjects: vi.fn().mockResolvedValue([]),
  createProject: vi.fn().mockResolvedValue({ name: 'test', title: 'Test' }),
  listChapters: vi.fn().mockResolvedValue([]),
  readChapter: vi.fn().mockResolvedValue(''),
  saveChapter: vi.fn().mockResolvedValue(true),
  createChapter: vi.fn().mockResolvedValue('chapter-1.md'),
  deleteChapter: vi.fn().mockResolvedValue(true),
  pythonRequest: vi.fn().mockResolvedValue({ status: 'ok' }),
  selectDirectory: vi.fn().mockResolvedValue(null),
}

Object.defineProperty(window, 'wenforge', {
  value: mockApi,
  writable: true,
})
