const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('wenforge', {
  // --- Local Data (stored on user's machine) ---
  getDataDir: () => ipcRenderer.invoke('get-data-dir'),
  loadSettings: () => ipcRenderer.invoke('load-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),

  // Project operations (stored in Documents/WenForge/stories/)
  listProjects: () => ipcRenderer.invoke('list-projects'),
  createProject: (data) => ipcRenderer.invoke('create-project', data),
  listChapters: (projectName) => ipcRenderer.invoke('list-chapters', projectName),
  readChapter: (projectName, chapterFile) => ipcRenderer.invoke('read-chapter', projectName, chapterFile),
  saveChapter: (projectName, chapterFile, content) => ipcRenderer.invoke('save-chapter', projectName, chapterFile, content),
  createChapter: (projectName, title) => ipcRenderer.invoke('create-chapter', projectName, title),
  deleteChapter: (projectName, chapterFile) => ipcRenderer.invoke('delete-chapter', projectName, chapterFile),

  // Python sidecar proxy
  pythonRequest: (endpoint, data) => ipcRenderer.invoke('python-request', { endpoint, data }),

  // Dialog
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
});
