const { app, BrowserWindow, Menu, dialog, shell, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');
const findFreePort = require('find-free-port');

let mainWindow;
let streamlitProcess;
let streamlitPort = 8501;

// 메뉴 비활성화 (프로덕션 모드에서)
if (!isDev) {
  Menu.setApplicationMenu(null);
}

// 포트 찾기
async function findAvailablePort() {
  try {
    const [port] = await findFreePort(8501, 8600);
    streamlitPort = port;
    console.log(`Using port: ${streamlitPort}`);
  } catch (error) {
    console.log('Using default port 8501');
  }
}

// Streamlit 서버 시작
function startStreamlitServer() {
  return new Promise((resolve, reject) => {
    console.log('Starting Streamlit server...');
    
    const pythonCmd = isDev ? 'python' : path.join(process.resourcesPath, 'python', 'python.exe');
    const appPath = isDev ? 'app.py' : path.join(process.resourcesPath, 'app', 'app.py');
    
    streamlitProcess = spawn(pythonCmd, [
      '-m', 'streamlit', 'run', appPath,
      '--server.port', streamlitPort.toString(),
      '--server.headless', 'true',
      '--server.address', 'localhost',
      '--browser.gatherUsageStats', 'false'
    ], {
      cwd: isDev ? process.cwd() : path.join(process.resourcesPath, 'app')
    });

    streamlitProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Streamlit:', output);
      
      if (output.includes('You can now view your Streamlit app')) {
        console.log('Streamlit server is ready!');
        resolve();
      }
    });

    streamlitProcess.stderr.on('data', (data) => {
      console.error('Streamlit Error:', data.toString());
    });

    streamlitProcess.on('close', (code) => {
      console.log(`Streamlit process exited with code ${code}`);
    });

    // 타임아웃 설정 (30초)
    setTimeout(() => {
      console.log('Streamlit server timeout, proceeding anyway...');
      resolve();
    }, 30000);
  });
}

// 메인 창 생성
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: 'AutoAvatar - AI Video Generator',
    show: false,
    titleBarStyle: 'default'
  });

  // 창이 준비되면 보여주기
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Streamlit 앱 로드
  const startUrl = `http://localhost:${streamlitPort}`;
  mainWindow.loadURL(startUrl);

  // 외부 링크는 기본 브라우저에서 열기
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // 창 닫기 이벤트
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // 로딩 실패 시 재시도
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.log('Failed to load, retrying in 2 seconds...');
    setTimeout(() => {
      mainWindow.loadURL(startUrl);
    }, 2000);
  });
}

// 앱 준비 완료
app.whenReady().then(async () => {
  await findAvailablePort();
  await startStreamlitServer();
  createWindow();
});

// 모든 창이 닫혔을 때
app.on('window-all-closed', () => {
  if (streamlitProcess) {
    streamlitProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 앱 활성화 (macOS)
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// 앱 종료 전 정리
app.on('before-quit', () => {
  if (streamlitProcess) {
    streamlitProcess.kill();
  }
});

// 보안 설정
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});

// IPC 핸들러
ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
}); 