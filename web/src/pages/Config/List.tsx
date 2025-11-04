/**
 * 配置列表页面 - 简化版（适合小白用户）
 */

import React, { useRef, useState } from 'react';
import { Button, Space, Tag, Modal, message, Card, Typography, Alert } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
} from '@ant-design/icons';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { useNavigate } from 'react-router-dom';
import {
  getConfigs,
  deleteConfig,
  updateConfig,
} from '@/api/config';
import type { Configuration } from '@/types';
import { ConfigType, ConfigStatus } from '@/types';

const { confirm } = Modal;
const { Title, Paragraph } = Typography;

// 配置类型映射 - 简化版
const CONFIG_TYPE_MAP = {
  [ConfigType.EXCHANGE]: { text: '交易所', color: '#3B82F6', icon: '🏦' },
  [ConfigType.NOTIFICATION]: { text: '通知', color: '#10B981', icon: '🔔' },
};

const ConfigList: React.FC = () => {
  const navigate = useNavigate();
  const actionRef = useRef<ActionType>(null);
  const [showSensitive, setShowSensitive] = useState<Record<number, boolean>>({});

  // 表格列定义
  const columns: ProColumns<Configuration>[] = [
    {
      title: '名称',
      dataIndex: 'display_name',
      width: 250,
      ellipsis: true,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500, color: '#111827', marginBottom: 4 }}>
            {record.display_name}
          </div>
          <div style={{ fontSize: 12, color: '#6B7280' }}>
            {record.config_key}
          </div>
        </div>
      ),
    },
    {
      title: '配置值',
      dataIndex: 'config_value',
      width: 300,
      search: false,
      ellipsis: true,
      render: (_, record) => {
        const isSensitive = record.is_sensitive;
        const isShown = showSensitive[record.id];

        if (isSensitive && !isShown) {
          return (
            <Space>
              <span style={{ fontFamily: 'monospace', color: '#6B7280' }}>••••••••</span>
              <Button
                type="link"
                size="small"
                icon={<EyeOutlined />}
                onClick={() => setShowSensitive({ ...showSensitive, [record.id]: true })}
              >
                显示
              </Button>
            </Space>
          );
        }

        return (
          <Space>
            <span style={{ fontFamily: 'monospace', fontSize: 13 }}>
              {record.config_value.length > 50
                ? `${record.config_value.substring(0, 50)}...`
                : record.config_value}
            </span>
            {isSensitive && (
              <Button
                type="link"
                size="small"
                icon={<EyeInvisibleOutlined />}
                onClick={() => setShowSensitive({ ...showSensitive, [record.id]: false })}
              >
                隐藏
              </Button>
            )}
          </Space>
        );
      },
    },
    {
      title: '类型',
      dataIndex: 'config_type',
      width: 100,
      valueType: 'select',
      valueEnum: Object.fromEntries(
        Object.entries(CONFIG_TYPE_MAP).map(([key, value]) => [
          key,
          { text: value.text },
        ])
      ),
      render: (_, record) => {
        const typeInfo = CONFIG_TYPE_MAP[record.config_type] || { text: record.config_type, color: '#9CA3AF', icon: '⚙️' };
        return (
          <Tag color={typeInfo.color}>
            <span style={{ marginRight: 4 }}>{typeInfo.icon}</span>
            {typeInfo.text}
          </Tag>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      valueType: 'select',
      valueEnum: {
        [ConfigStatus.ACTIVE]: { text: '已启用', status: 'Success' },
        [ConfigStatus.INACTIVE]: { text: '已停用', status: 'Default' },
      },
      render: (_, record) => {
        const isActive = record.status === ConfigStatus.ACTIVE;
        return (
          <Tag color={isActive ? 'success' : 'default'}>
            {isActive ? '✓ 已启用' : '已停用'}
          </Tag>
        );
      },
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      fixed: 'right',
      render: (_, record) => [
        <Button
          key="edit"
          type="link"
          size="small"
          icon={<EditOutlined />}
          onClick={() => navigate(`/configs/${record.id}`)}
        >
          编辑
        </Button>,
        record.status === ConfigStatus.ACTIVE ? (
          <Button
            key="inactive"
            type="link"
            size="small"
            icon={<CloseCircleOutlined />}
            onClick={() => handleToggleStatus(record, ConfigStatus.INACTIVE)}
            style={{ color: '#F59E0B' }}
          >
            停用
          </Button>
        ) : (
          <Button
            key="active"
            type="link"
            size="small"
            icon={<CheckCircleOutlined />}
            onClick={() => handleToggleStatus(record, ConfigStatus.ACTIVE)}
            style={{ color: '#10B981' }}
          >
            启用
          </Button>
        ),
        <Button
          key="delete"
          type="link"
          size="small"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record)}
        >
          删除
        </Button>,
      ],
    },
  ];

  // 切换配置状态
  const handleToggleStatus = async (record: Configuration, newStatus: string) => {
    try {
      await updateConfig(record.id, { status: newStatus as any });
      message.success(newStatus === ConfigStatus.ACTIVE ? '已启用配置' : '已停用配置');
      actionRef.current?.reload();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 删除配置
  const handleDelete = (record: Configuration) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除这个配置吗？</p>
          <p style={{ color: '#6B7280', fontSize: 14, marginTop: 8 }}>
            {record.display_name}
          </p>
          <p style={{ color: '#EF4444', fontSize: 12, marginTop: 12 }}>
            ⚠️ 删除后无法恢复，请谨慎操作！
          </p>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteConfig(record.id);
          message.success('删除成功');
          actionRef.current?.reload();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  // 请求数据
  const request = async (params: any) => {
    try {
      const response = await getConfigs({
        page: params.current,
        page_size: params.pageSize,
        search: params.keyword,
        type: params.config_type,
        status: params.status,
      });

      return {
        data: response.items,
        success: true,
        total: response.total,
      };
    } catch (error) {
      message.error('数据加载失败');
      return {
        data: [],
        success: false,
        total: 0,
      };
    }
  };

  return (
    <div>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ marginBottom: 8, color: '#111827' }}>
          系统配置
        </Title>
        <Paragraph style={{ fontSize: 15, color: '#6B7280', marginBottom: 0 }}>
          在这里可以管理交易所连接、消息通知等基础设置
        </Paragraph>
      </div>

      {/* 新增配置提示卡片 */}
      <div
        style={{
          marginBottom: 24,
          borderRadius: 12,
          background: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
          border: 'none',
          cursor: 'pointer',
          boxShadow: '0 4px 16px rgba(59, 130, 246, 0.4)',
          padding: '24px 28px',
          transition: 'all 0.3s ease',
        }}
        onClick={() => navigate('/configs/new')}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 8px 24px rgba(59, 130, 246, 0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 4px 16px rgba(59, 130, 246, 0.4)';
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 14,
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              }}
            >
              <PlusOutlined style={{ fontSize: 28, color: '#FFFFFF', fontWeight: 'bold' }} />
            </div>
            <div>
              <div style={{
                fontSize: 20,
                fontWeight: 800,
                color: '#FFFFFF',
                marginBottom: 8,
                textShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
                letterSpacing: '0.5px',
              }}>
                添加新配置
              </div>
              <div style={{
                fontSize: 16,
                color: '#FFFFFF',
                fontWeight: 600,
                textShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                opacity: 1,
              }}>
                点击这里配置交易所或通知方式
              </div>
            </div>
          </div>
          <Button
            type="primary"
            size="large"
            icon={<PlusOutlined />}
            style={{
              background: '#FFFFFF',
              borderColor: '#FFFFFF',
              color: '#2563EB',
              height: 48,
              fontSize: 16,
              fontWeight: 700,
              padding: '0 32px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            }}
          >
            立即添加
          </Button>
        </div>
      </div>

      {/* 配置列表表格 */}
      <ProTable<Configuration>
        columns={columns}
        actionRef={actionRef}
        request={request}
        rowKey="id"
        search={{
          labelWidth: 'auto',
          defaultCollapsed: false,
        }}
        pagination={{
          defaultPageSize: 20,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50'],
        }}
        dateFormatter="string"
        toolBarRender={false}
        cardProps={{
          style: {
            borderRadius: 12,
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
          },
        }}
        options={{
          reload: true,
          density: false,
          setting: false,
        }}
      />
    </div>
  );
};

export default ConfigList;
