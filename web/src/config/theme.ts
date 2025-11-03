/**
 * Ant Design 主题配置
 */

import type { ThemeConfig } from 'antd';

// 亮色主题
export const lightTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#f5222d',
    colorInfo: '#1890ff',
    colorBgBase: '#ffffff',
    colorTextBase: '#000000',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      colorBgHeader: '#ffffff',
      colorBgBody: '#f0f2f5',
      colorBgTrigger: '#002140',
    },
    Menu: {
      colorItemBg: 'transparent',
      colorItemBgSelected: '#1890ff',
      colorItemTextSelected: '#ffffff',
    },
  },
};

// 暗色主题
export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#f5222d',
    colorInfo: '#1890ff',
    colorBgBase: '#141414',
    colorTextBase: '#ffffff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      colorBgHeader: '#1f1f1f',
      colorBgBody: '#000000',
      colorBgTrigger: '#1f1f1f',
    },
    Menu: {
      colorItemBg: 'transparent',
      colorItemBgSelected: '#1890ff',
      colorItemTextSelected: '#ffffff',
    },
  },
  algorithm: 'dark' as any, // 使用暗色算法
};
