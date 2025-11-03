/**
 * 登录页面 - 现代化科技风格
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, message } from 'antd';
import { UserOutlined, LockOutlined, BulbOutlined, BulbFilled, ThunderboltOutlined } from '@ant-design/icons';
import { login } from '@/api/auth';
import { useTheme } from '@/contexts/ThemeContext';
import { modernTheme } from '@/styles/modernTheme';
import GlassCard from '@/components/GlassCard';
import type { LoginRequest } from '@/types';
import './Login.css';

const { Title } = Typography;

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = React.useState(false);
  const { theme, toggleTheme } = useTheme();

  // 获取重定向路径（如果有的话）
  const from = (location.state as any)?.from?.pathname || '/';

  const onFinish = async (values: LoginRequest) => {
    setLoading(true);
    try {
      const response = await login(values);

      // 保存token和用户信息
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      message.success('登录成功');

      // 跳转回原页面或首页
      navigate(from, { replace: true });
    } catch (error) {
      message.error('登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container" style={{
      background: modernTheme.gradients.background,
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
    }}>
      {/* 主题切换按钮 */}
      <Button
        className="theme-toggle"
        type="text"
        size="large"
        icon={theme === 'dark' ? <BulbFilled style={{ color: modernTheme.colors.primary }} /> : <BulbOutlined style={{ color: modernTheme.colors.primary }} />}
        onClick={toggleTheme}
        title={theme === 'dark' ? '切换到亮色模式' : '切换到暗色模式'}
        style={{
          position: 'absolute',
          top: 24,
          right: 24,
          zIndex: 10,
        }}
      />

      <GlassCard glow style={{
        width: '100%',
        maxWidth: 450,
        margin: '0 20px',
        padding: '40px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 80,
            height: 80,
            borderRadius: '50%',
            background: modernTheme.gradients.blue,
            marginBottom: 20,
            boxShadow: modernTheme.shadows.glow,
          }}>
            <ThunderboltOutlined style={{
              fontSize: 40,
              color: '#fff'
            }} />
          </div>
          <Title
            level={2}
            style={{
              background: modernTheme.gradients.blue,
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              marginBottom: 8,
            }}
          >
            GridBNB Trading System
          </Title>
          <p style={{
            color: modernTheme.colors.textSecondary,
            fontSize: 14,
          }}>
            企业级网格交易配置管理系统
          </p>
        </div>

        <Form
          name="login"
          initialValues={{ username: 'admin', password: 'admin123' }}
          onFinish={onFinish}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined style={{ color: modernTheme.colors.primary }} />}
              placeholder="用户名"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${modernTheme.colors.border}`,
                color: modernTheme.colors.textPrimary,
              }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: modernTheme.colors.primary }} />}
              placeholder="密码"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: `1px solid ${modernTheme.colors.border}`,
                color: modernTheme.colors.textPrimary,
              }}
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                background: modernTheme.gradients.blue,
                border: 'none',
                height: 48,
                fontSize: 16,
                fontWeight: 'bold',
                boxShadow: modernTheme.shadows.glow,
              }}
            >
              {loading ? '登��中...' : '登录'}
            </Button>
          </Form.Item>
        </Form>

        <div style={{
          textAlign: 'center',
          padding: '20px 0 0',
          borderTop: `1px solid ${modernTheme.colors.border}`,
        }}>
          <p style={{
            color: modernTheme.colors.textMuted,
            fontSize: 12,
            margin: 0,
          }}>
            默认账号：admin / admin123
          </p>
        </div>
      </GlassCard>
    </div>
  );
};

export default Login;
