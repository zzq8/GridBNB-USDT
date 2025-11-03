/**
 * 配置模板列表页面
 */

import React, { useRef, useState } from 'react';
import { Button, Space, Tag, Modal, message, Typography, Descriptions } from 'antd';
import {
  ThunderboltOutlined,
  EyeOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { getTemplates, applyTemplate } from '@/api/config';
import type { ConfigurationTemplate } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { confirm } = Modal;

const TemplateList: React.FC = () => {
  const actionRef = useRef<ActionType>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<ConfigurationTemplate | null>(null);

  // 表格列定义
  const columns: ProColumns<ConfigurationTemplate>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
      search: false,
    },
    {
      title: '模板名称',
      dataIndex: 'template_name',
      width: 150,
      copyable: true,
      render: (_, record) => (
        <Space>
          <Text strong>{record.display_name}</Text>
          {record.is_system && <Tag color="blue">系统模板</Tag>}
        </Space>
      ),
    },
    {
      title: '模板类型',
      dataIndex: 'template_type',
      width: 120,
      valueType: 'select',
      valueEnum: {
        exchange: { text: '交易所配置', status: 'Processing' },
        trading: { text: '交易策略', status: 'Success' },
        risk: { text: '风控配置', status: 'Warning' },
        ai: { text: 'AI策略', status: 'Default' },
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      search: false,
      ellipsis: true,
      width: 300,
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      width: 100,
      search: false,
      sorter: true,
      render: (count) => (
        <Tag color={Number(count) > 10 ? 'green' : 'default'}>{count}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 100,
      valueType: 'select',
      valueEnum: {
        true: { text: '启用', status: 'Success' },
        false: { text: '禁用', status: 'Default' },
      },
      render: (_, record) =>
        record.is_active ? (
          <Tag icon={<CheckCircleOutlined />} color="success">
            启用
          </Tag>
        ) : (
          <Tag color="default">禁用</Tag>
        ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      valueType: 'dateTime',
      search: false,
    },
    {
      title: '操作',
      valueType: 'option',
      width: 180,
      fixed: 'right',
      render: (_, record) => [
        <Button
          key="view"
          type="link"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => {
            setCurrentTemplate(record);
            setDetailVisible(true);
          }}
        >
          查看详情
        </Button>,
        <Button
          key="apply"
          type="link"
          size="small"
          icon={<ThunderboltOutlined />}
          disabled={!record.is_active}
          onClick={() => handleApplyTemplate(record)}
        >
          应用模板
        </Button>,
      ],
    },
  ];

  // 应用模板
  const handleApplyTemplate = (template: ConfigurationTemplate) => {
    confirm({
      title: '确认应用模板',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>
            确定要应用模板 <strong>{template.display_name}</strong> 吗？
          </p>
          <p style={{ color: '#ff4d4f', fontSize: 12 }}>
            应用模板会覆盖当前配置！请确保已备份重要配置。
          </p>
          {template.description && (
            <>
              <div style={{ marginTop: 12 }}>
                <Text type="secondary">模板描述:</Text>
              </div>
              <Paragraph style={{ marginTop: 8, fontSize: 12 }}>
                {template.description}
              </Paragraph>
            </>
          )}
        </div>
      ),
      okText: '确认应用',
      okType: 'primary',
      cancelText: '取消',
      onOk: async () => {
        try {
          const result = await applyTemplate(template.id);
          message.success(
            `模板应用成功！已更新 ${result.applied} 个配置项。`
          );
          // 提示可能需要重启
          Modal.info({
            title: '提示',
            content: (
              <div>
                <p>模板已成功应用！</p>
                <p>如果配置中包含需要重启的项目，请及时重启系统使配置生效。</p>
              </div>
            ),
          });
        } catch (error) {
          message.error('模板应用失败');
        }
      },
    });
  };

  // 请求数据
  const request = async (params: any) => {
    try {
      const response = await getTemplates({
        type: params.template_type,
        is_system: params.is_system,
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
    <>
      <ProTable<ConfigurationTemplate>
        columns={columns}
        actionRef={actionRef}
        request={request}
        rowKey="id"
        search={{
          labelWidth: 'auto',
        }}
        pagination={{
          defaultPageSize: 20,
          showSizeChanger: true,
        }}
        dateFormatter="string"
        headerTitle="配置模板"
        toolBarRender={() => [
          <Button
            key="reload"
            icon={<ReloadOutlined />}
            onClick={() => actionRef.current?.reload()}
          >
            刷新
          </Button>,
        ]}
      />

      {/* 模板详情抽屉 */}
      <Modal
        title={`模板详情 - ${currentTemplate?.display_name}`}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>
            关闭
          </Button>,
          <Button
            key="apply"
            type="primary"
            icon={<ThunderboltOutlined />}
            disabled={!currentTemplate?.is_active}
            onClick={() => {
              if (currentTemplate) {
                handleApplyTemplate(currentTemplate);
                setDetailVisible(false);
              }
            }}
          >
            应用模板
          </Button>,
        ]}
      >
        {currentTemplate && (
          <div>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="模板ID">
                {currentTemplate.id}
              </Descriptions.Item>
              <Descriptions.Item label="模板名称">
                {currentTemplate.template_name}
              </Descriptions.Item>
              <Descriptions.Item label="显示名称">
                {currentTemplate.display_name}
              </Descriptions.Item>
              <Descriptions.Item label="模板类型">
                <Tag>{currentTemplate.template_type}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="系统模板">
                {currentTemplate.is_system ? '是' : '否'}
              </Descriptions.Item>
              <Descriptions.Item label="状态">
                {currentTemplate.is_active ? (
                  <Tag color="success">启用</Tag>
                ) : (
                  <Tag>禁用</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="使用次数">
                {currentTemplate.usage_count}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {currentTemplate.created_at}
              </Descriptions.Item>
            </Descriptions>

            {currentTemplate.description && (
              <div style={{ marginTop: 16 }}>
                <Title level={5}>模板描述</Title>
                <Paragraph>{currentTemplate.description}</Paragraph>
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <Title level={5}>配置内容</Title>
              <Paragraph>
                <pre
                  style={{
                    background: '#f5f5f5',
                    padding: 16,
                    borderRadius: 4,
                    maxHeight: 400,
                    overflow: 'auto',
                  }}
                >
                  {JSON.stringify(currentTemplate.config_json, null, 2)}
                </pre>
              </Paragraph>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

export default TemplateList;
