const { contextBridge, ipcRenderer } = require('electron');

// 보안을 위한 컨텍스트 브리지
contextBridge.exposeInMainWorld('electronAPI', {
  // 앱 버전 가져오기
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // 메시지 박스 표시
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  // 플랫폼 정보
  platform: process.platform,
  
  // 앱 정보
  appInfo: {
    name: 'AutoAvatar',
    description: 'AI Video Generator Desktop App'
  }
});

// 보안 강화
window.addEventListener('DOMContentLoaded', () => {
  // 개발자 도구 비활성화 (프로덕션)
  if (!process.env.ELECTRON_IS_DEV) {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'F12' || 
          (e.ctrlKey && e.shiftKey && e.key === 'I') ||
          (e.ctrlKey && e.shiftKey && e.key === 'C')) {
        e.preventDefault();
      }
    });
    
    document.addEventListener('contextmenu', (e) => {
      e.preventDefault();
    });
  }
}); 