(function () {
  'use strict';

  if (window.wenforge) return;

  const API_BASE = '';

  async function apiFetch(url, options) {
    const res = await fetch(API_BASE + url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) throw new Error('API error: ' + res.status);
    return res.json();
  }

  window.wenforge = {
    getDataDir() {
      return 'WenForge';
    },

    async loadSettings() {
      return apiFetch('/api/storage/settings');
    },

    async saveSettings(settings) {
      return apiFetch('/api/storage/settings', {
        method: 'POST',
        body: JSON.stringify(settings),
      });
    },

    async listProjects() {
      return apiFetch('/api/storage/projects');
    },

    async createProject(data) {
      return apiFetch('/api/storage/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    async listChapters(projectName) {
      return apiFetch('/api/storage/projects/' + encodeURIComponent(projectName) + '/chapters');
    },

    async readChapter(projectName, chapterFile) {
      return apiFetch('/api/storage/projects/' + encodeURIComponent(projectName) + '/chapters/' + encodeURIComponent(chapterFile));
    },

    async saveChapter(projectName, chapterFile, content) {
      return apiFetch('/api/storage/projects/' + encodeURIComponent(projectName) + '/chapters/' + encodeURIComponent(chapterFile), {
        method: 'PUT',
        body: JSON.stringify({ content }),
      });
    },

    async createChapter(projectName, title) {
      return apiFetch('/api/storage/projects/' + encodeURIComponent(projectName) + '/chapters', {
        method: 'POST',
        body: JSON.stringify({ title }),
      });
    },

    async deleteChapter(projectName, chapterFile) {
      return apiFetch('/api/storage/projects/' + encodeURIComponent(projectName) + '/chapters/' + encodeURIComponent(chapterFile), {
        method: 'DELETE',
      });
    },

    async pythonRequest(endpoint, data) {
      return apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    async selectDirectory() {
      return '';
    },
  };
})();
