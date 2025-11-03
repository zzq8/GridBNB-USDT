/**
 * 现代化主题配置 - 科技感深色主题
 */

export const modernTheme = {
  // 主色调 - 科技蓝
  colors: {
    primary: '#00D4FF',
    primaryDark: '#0066FF',
    primaryLight: '#33E0FF',

    // 辅助色
    secondary: '#00FFB9',
    accent: '#9D4EDD',
    warning: '#FFB800',

    // 涨跌色
    success: '#00FF88',
    danger: '#FF4757',

    // 背景色
    bgPrimary: '#0a0e27',
    bgSecondary: '#1a1f3a',
    bgTertiary: '#252b48',

    // 文字色
    textPrimary: '#FFFFFF',
    textSecondary: '#B8C1EC',
    textMuted: '#6B7280',

    // 边框色
    border: 'rgba(255, 255, 255, 0.1)',
    borderLight: 'rgba(255, 255, 255, 0.05)',

    // 玻璃态效果
    glass: 'rgba(255, 255, 255, 0.05)',
    glassHover: 'rgba(255, 255, 255, 0.08)',
  },

  // 渐变色
  gradients: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    blue: 'linear-gradient(135deg, #00D4FF 0%, #0066FF 100%)',
    green: 'linear-gradient(135deg, #00FFB9 0%, #00FF88 100%)',
    purple: 'linear-gradient(135deg, #9D4EDD 0%, #C77DFF 100%)',
    background: 'linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0a0e27 100%)',
    card: 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
  },

  // 阴影
  shadows: {
    sm: '0 2px 8px rgba(0, 0, 0, 0.15)',
    md: '0 4px 16px rgba(0, 0, 0, 0.2)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.3)',
    xl: '0 12px 48px rgba(0, 0, 0, 0.4)',
    glow: '0 0 20px rgba(0, 212, 255, 0.3)',
    glowStrong: '0 0 30px rgba(0, 212, 255, 0.5)',
  },

  // 圆角
  borderRadius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    full: '9999px',
  },

  // 动画
  transitions: {
    fast: '0.15s ease-in-out',
    normal: '0.3s ease-in-out',
    slow: '0.5s ease-in-out',
  },

  // 毛玻璃效果
  backdropFilter: 'blur(10px)',

  // Z-index层级
  zIndex: {
    base: 1,
    dropdown: 1000,
    sticky: 1100,
    fixed: 1200,
    modal: 1300,
    popover: 1400,
    tooltip: 1500,
  },
};

// CSS变量形式（用于全局注入）
export const modernThemeVars = {
  '--color-primary': modernTheme.colors.primary,
  '--color-primary-dark': modernTheme.colors.primaryDark,
  '--color-secondary': modernTheme.colors.secondary,
  '--color-success': modernTheme.colors.success,
  '--color-danger': modernTheme.colors.danger,
  '--bg-primary': modernTheme.colors.bgPrimary,
  '--bg-secondary': modernTheme.colors.bgSecondary,
  '--text-primary': modernTheme.colors.textPrimary,
  '--text-secondary': modernTheme.colors.textSecondary,
  '--border-color': modernTheme.colors.border,
  '--gradient-background': modernTheme.gradients.background,
  '--backdrop-filter': modernTheme.backdropFilter,
};

export default modernTheme;
