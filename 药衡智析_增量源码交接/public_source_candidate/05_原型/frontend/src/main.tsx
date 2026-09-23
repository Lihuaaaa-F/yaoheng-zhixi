import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import './style.css';
import './workbench.css';
import './three-panel.css';
createRoot(document.getElementById('root')!).render(
  <ConfigProvider locale={zhCN} theme={{ token: {
    colorPrimary: '#087f88', colorInfo: '#087f88', colorInfoBg: '#f0f8f8', colorInfoBorder: '#d2e7e6', colorText: '#172c38', colorTextSecondary: '#596e7b', colorTextTertiary: '#617682', colorTextPlaceholder: '#617682',
    colorBgLayout: '#eef2f5', colorBorder: '#dfe6eb', fontSize: 14, borderRadius: 9, controlHeight: 34,
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", system-ui, sans-serif',
  } }}><App /></ConfigProvider>
);
