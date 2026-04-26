const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;

const PYTHON_PORT = 8765;
const PYTHON_URL = `http://localhost:${PYTHON_PORT}`;

function startPythonSidecar() {
  const pythonDir = path.join(__dirname, '..', 'python');
  const pythonExe = process.platform === 'win32' ? 'python' : 'python3';

  pythonProcess = spawn(pythonExe, ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(PYTHON_PORT)], {
    cwd: pythonDir,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`[Python] ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.log(`[Python] ${data}`);
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python sidecar:', err);
  });

  pythonProcess.on('exit', (code) => {
    console.log(`Python sidecar exited with code ${code}`);
    pythonProcess = null;
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'WenForge - 锻造文学',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Try multiple paths to find dist/index.html
  const possiblePaths = [
    path.join(__dirname, '..', 'dist', 'index.html'),
    path.join(process.cwd(), 'dist', 'index.html'),
    path.join(app.getAppPath(), 'dist', 'index.html'),
  ];
  let distPath = null;
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) { distPath = p; break; }
  }

  const useDevServer = process.argv.includes('--dev');

  if (useDevServer) {
    console.log('[WenForge] Dev mode: loading from http://localhost:5173');
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else if (distPath) {
    console.log('[WenForge] Loading from ' + distPath);
    mainWindow.loadFile(distPath);
  } else {
    console.log('[WenForge] No dist/ found, trying dev server at http://localhost:5173');
    mainWindow.loadURL('http://localhost:5173');
  }
}

app.whenReady().then(() => {
  ensureDataDirs();
  startPythonSidecar();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  if (process.platform !== 'darwin') app.quit();
});

// ---- IPC Handlers ----

// ---- Local Data Storage ----
// All data stored locally on user's machine
const userDataDir = path.join(app.getPath('documents'), 'WenForge');
const projectsDir = path.join(userDataDir, 'stories');
const settingsFile = path.join(userDataDir, 'settings.json');

// Create data directories on startup
function ensureDataDirs() {
  if (!fs.existsSync(userDataDir)) fs.mkdirSync(userDataDir, { recursive: true });
  if (!fs.existsSync(projectsDir)) fs.mkdirSync(projectsDir, { recursive: true });
}

ipcMain.handle('list-projects', async () => {
  try {
    const dirs = fs.readdirSync(projectsDir, { withFileTypes: true });
    const projects = dirs.filter(d => d.isDirectory()).map(d => {
      const metaPath = path.join(projectsDir, d.name, 'meta.json');
      if (fs.existsSync(metaPath)) {
        return JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
      }
      return { name: d.name, title: d.name };
    });
    return projects;
  } catch (e) {
    return [];
  }
});

ipcMain.handle('create-project', async (event, { title, author, genre }) => {
  const dirName = title.replace(/[\\/:*?"<>|]/g, '_');
  const projectDir = path.join(projectsDir, dirName);
  if (!fs.existsSync(projectDir)) {
    fs.mkdirSync(projectDir, { recursive: true });
    fs.mkdirSync(path.join(projectDir, 'chapters'), { recursive: true });
  }
  const meta = { name: dirName, title, author: author || '', genre: genre || '', createdAt: new Date().toISOString() };
  fs.writeFileSync(path.join(projectDir, 'meta.json'), JSON.stringify(meta, null, 2));
  return meta;
});

ipcMain.handle('list-chapters', async (event, projectName) => {
  const chaptersDir = path.join(projectsDir, projectName, 'chapters');
  if (!fs.existsSync(chaptersDir)) return [];
  const files = fs.readdirSync(chaptersDir).filter(f => f.endsWith('.md')).sort();
  return files.map(f => {
    const stat = fs.statSync(path.join(chaptersDir, f));
    return { name: f.replace('.md', ''), file: f, updatedAt: stat.mtime.toISOString() };
  });
});

ipcMain.handle('read-chapter', async (event, projectName, chapterFile) => {
  const filePath = path.join(projectsDir, projectName, 'chapters', chapterFile);
  if (fs.existsSync(filePath)) {
    return fs.readFileSync(filePath, 'utf-8');
  }
  return '';
});

ipcMain.handle('save-chapter', async (event, projectName, chapterFile, content) => {
  const filePath = path.join(projectsDir, projectName, 'chapters', chapterFile);
  fs.writeFileSync(filePath, content, 'utf-8');
  return true;
});

ipcMain.handle('create-chapter', async (event, projectName, title) => {
  const fileName = title.replace(/[\\/:*?"<>|]/g, '_') + '.md';
  const filePath = path.join(projectsDir, projectName, 'chapters', fileName);
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, `# ${title}\n\n`, 'utf-8');
  }
  return fileName;
});

ipcMain.handle('delete-chapter', async (event, projectName, chapterFile) => {
  const filePath = path.join(projectsDir, projectName, 'chapters', chapterFile);
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }
  return true;
});

// Local settings storage (not localStorage, persisted to disk)
ipcMain.handle('get-data-dir', () => userDataDir);

ipcMain.handle('load-settings', () => {
  try {
    if (fs.existsSync(settingsFile)) {
      return JSON.parse(fs.readFileSync(settingsFile, 'utf-8'));
    }
  } catch (e) {
    console.error('Failed to load settings:', e.message);
  }
  return {};
});

ipcMain.handle('save-settings', async (event, settings) => {
  try {
    fs.writeFileSync(settingsFile, JSON.stringify(settings, null, 2), 'utf-8');
    return true;
  } catch (e) {
    console.error('Failed to save settings:', e.message);
    return false;
  }
});

// Python sidecar proxy
ipcMain.handle('python-request', async (event, { endpoint, data }) => {
  try {
    const http = require('http');
    return new Promise((resolve, reject) => {
      const postData = JSON.stringify(data);
      const options = {
        hostname: '127.0.0.1',
        port: PYTHON_PORT,
        path: endpoint,
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(postData) },
      };
      const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(body)); }
          catch { resolve({ error: 'Invalid response', raw: body }); }
        });
      });
      req.on('error', (e) => resolve({ error: e.message }));
      req.write(postData);
      req.end();
    });
  } catch (e) {
    return { error: e.message };
  }
});

ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] });
  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});
