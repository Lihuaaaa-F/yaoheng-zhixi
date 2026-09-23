import { createRoot } from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import './style.css';
import './workbench.css';
createRoot(document.getElementById('root')!).render(
  <ConfigProvider locale={zhCN} theme={{ token: {
    colorPrimary: '#227c81', colorInfo: '#227c81', colorInfoBg: '#f2f8f8', colorInfoBorder: '#cde1e0', colorText: '#22343e', colorTextSecondary: '#596e7b', colorTextTertiary: '#617682', colorTextPlaceholder: '#617682',
    colorBgLayout: '#f4f7f9', colorBorder: '#dbe5e9', fontSize: 14, borderRadius: 6, controlHeight: 36,
    fontFamily: '"Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif',
  } }}><App /></ConfigProvider>
);
