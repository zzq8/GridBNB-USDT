/**
 * 配置列表页面 - 企业级配置管理
 */

import React, { useRef, useState } from 'react';
import { Button, Space, Tag, Modal, message, Tooltip, Upload } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  DownloadOutlined,
  UploadOutlined,
  SyncOutlined,
} from '@ant-design/icons';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { useNavigate } from 'react-router-dom';
import {
  getConfigs,
  deleteConfig,
  updateConfig,
  reloadConfigs,
  exportConfigs,
  importConfigs,
} from '@/api/config';
import type { Configuration } from '@/types';
import { ConfigType, ConfigStatus } from '@/types';

const { confirm } = Modal;

// 配置类型映射
const CONFIG_TYPE_MAP = {
  [ConfigType.EXCHANGE]: { text: '交易所配置', color: 'blue' },
  [ConfigType.TRADING]: { text: '交易策略', color: 'green' },
  [ConfigType.RISK]: { text: '风控配置', color: 'orange' },
  [ConfigType.AI]: { text: 'AI策略', color: 'purple' },
  [ConfigType.NOTIFICATION]: { text: '通知配置', color: 'cyan' },
  [ConfigType.SYSTEM]: { text: '系统配置', color: 'default' },
};

// 配置状态映射
const CONFIG_STATUS_MAP = {
  [ConfigStatus.DRAFT]: { text: '草稿', color: 'default' },
  [ConfigStatus.ACTIVE]: { text: '已激活', color: 'success' },
  [ConfigStatus.INACTIVE]: { text: '已停用', color: 'warning' },
  [ConfigStatus.ARCHIVED]: { text: '已归档', color: 'error' },
};

const ConfigList: React.FC = () => {
  const navigate = useNavigate();
  const actionRef = useRef<ActionType>(null);
  const [showSensitive, setShowSensitive] = useState<Record<number, boolean>>({});
  const [reloading, setReloading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);

  // 重新加载配置
  const handleReload = async () => {
    confirm({
      title: '重新加载配置',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>将从数据库重新加载配置到内存缓存。</p>
          <p style={{ color: '#1890ff', fontSize: 12 }}>
            ✓ 标记为"不需要重启"的配置将立即生效
          </p>
          <p style={{ color: '#faad14', fontSize: 12 }}>
            ⚠️ 标记为"需要重启"的配置仍需重启系统才能生效
          </p>
        </div>
      ),
      okText: '确认重新加载',
      cancelText: '取消',
      onOk: async () => {
        setReloading(true);
        try {
          const result = await reloadConfigs();
          message.success(
            `配置已重新加载！缓存中共有 ${result.cache_size} 个配置项`
          );
          if (result.warning) {
            message.warning(result.warning, 5);
          }
        } catch (error) {
          message.error('配置重新加载失败');
        } finally {
          setReloading(false);
        }
      },
    });
  };

  // 导出配置
  const handleExport = async (configType?: string) => {
    confirm({
      title: '导出配置',
      icon: <DownloadOutlined />,
      content: (
        <div>
          <p>导出配置为JSON文件。</p>
          {configType ? (
            <p>将导出类型为 <strong>{CONFIG_TYPE_MAP[configType as keyof typeof CONFIG_TYPE_MAP]?.text}</strong> 的配置</p>
          ) : (
            <p>将导出所有配置</p>
          )}
          <p style={{ color: '#faad14', fontSize: 12 }}>
            注意：敏感配置（如Token）默认不会导出
          </p>
        </div>
      ),
      okText: '确认导出',
      cancelText: '取消',
      onOk: async () => {
        setExporting(true);
        try {
          const blob = await exportConfigs({
            config_type: configType,
            include_sensitive: false,
          });

          // 创建下载链接
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;

          // 生成文件名
          const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
          const suffix = configType ? `_${configType}` : '_all';
          link.download = `gridbnb_config${suffix}_${timestamp}.json`;

          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);

          message.success('配置导出成功');
        } catch (error) {
          message.error('配置导出失败');
        } finally {
          setExporting(false);
        }
      },
    });
  };

  // 导入配置
  const handleImport = async (file: File) => {
    confirm({
      title: '导入配置',
      icon: <UploadOutlined />,
      content: (
        <div>
          <p>从文件导入配置。</p>
          <p>文件名：<strong>{file.name}</strong></p>
          <p style={{ color: '#1890ff', fontSize: 12 }}>
            ✓ 导入前会自动创建备份
          </p>
          <p style={{ color: '#faad14', fontSize: 12 }}>
            ⚠️ 将覆盖已存在的配置
          </p>
        </div>
      ),
      okText: '确认导入',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        setImporting(true);
        try {
          const result = await importConfigs(file, {
            overwrite: true,
            create_backup: true,
          });

          // 显示导入结果
          Modal.success({
            title: '配置导入完成',
            width: 600,
            content: (
              <div>
                <p>导入成功：<strong style={{ color: '#52c41a' }}>{result.imported}</strong> 项</p>
                <p>跳过：<strong>{result.skipped}</strong> 项</p>
                <p>失败：<strong style={{ color: '#ff4d4f' }}>{result.failed}</strong> 项</p>
                {result.requires_restart && (
                  <p style={{ color: '#faad14', marginTop: 16 }}>
                    ⚠️ 部分配置需要重启系统才能生效
                  </p>
                )}
                {result.details.length > 0 && (
                  <div style={{ marginTop: 16, maxHeight: 300, overflow: 'auto' }}>
                    <p style={{ fontWeight: 'bold' }}>详细信息：</p>
                    {result.details.slice(0, 10).map((detail, index) => (
                      <div key={index} style={{ fontSize: 12, padding: '4px 0' }}>
                        <Tag color={
                          detail.status === 'updated' ? 'success' :
                          detail.status === 'skipped' ? 'default' : 'error'
                        }>
                          {detail.status}
                        </Tag>
                        <span>{detail.key}</span>
                        {detail.reason && <span style={{ color: '#999' }}> - {detail.reason}</span>}
                        {detail.error && <span style={{ color: '#ff4d4f' }}> - {detail.error}</span>}
                      </div>
                    ))}
                    {result.details.length > 10 && (
                      <p style={{ color: '#999', fontSize: 12, marginTop: 8 }}>
                        ... 还有 {result.details.length - 10} 项
                      </p>
                    )}
                  </div>
                )}
              </div>
            ),
          });

          // 刷新列表
          actionRef.current?.reload();
        } catch (error: any) {
          message.error(error.message || '配置导入失败');
        } finally {
          setImporting(false);
        }
      },
    });

    return false; // 阻止默认上传行为
  };

  // 表格列定义
  const columns: ProColumns<Configuration>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
      search: false,
      sorter: true,
    },
    {
      title: '配置键',
      dataIndex: 'config_key',
      width: 200,
      ellipsis: true,
      copyable: true,
      render: (_, record) => (
        <Tooltip title={record.description}>
          <span style={{ fontFamily: 'monospace' }}>{record.config_key}</span>
        </Tooltip>
      ),
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '配置值',
      dataIndex: 'config_value',
      width: 200,
      search: false,
      ellipsis: true,
      render: (_, record) => {
        const isSensitive = record.is_sensitive;
        const isShown = showSensitive[record.id];

        if (isSensitive && !isShown) {
          return (
            <Space>
              <span style={{ fontFamily: 'monospace' }}>********</span>
              <Button
                type="link"
                size="small"
                icon={<EyeOutlined />}
                onClick={() => setShowSensitive({ ...showSensitive, [record.id]: true })}
              />
            </Space>
          );
        }

        return (
          <Space>
            <span style={{ fontFamily: 'monospace' }}>
              {record.config_value.length > 30
                ? `${record.config_value.substring(0, 30)}...`
                : record.config_value}
            </span>
            {isSensitive && (
              <Button
                type="link"
                size="small"
                icon={<EyeInvisibleOutlined />}
                onClick={() => setShowSensitive({ ...showSensitive, [record.id]: false })}
              />
            )}
          </Space>
        );
      },
    },
    {
      title: '配置类型',
      dataIndex: 'config_type',
      width: 120,
      valueType: 'select',
      valueEnum: Object.fromEntries(
        Object.entries(CONFIG_TYPE_MAP).map(([key, value]) => [
          key,
          { text: value.text },
        ])
      ),
      render: (_, record) => {
        const typeInfo = CONFIG_TYPE_MAP[record.config_type];
        return <Tag color={typeInfo.color}>{typeInfo.text}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      valueType: 'select',
      valueEnum: Object.fromEntries(
        Object.entries(CONFIG_STATUS_MAP).map(([key, value]) => [
          key,
          { text: value.text },
        ])
      ),
      render: (_, record) => {
        const statusInfo = CONFIG_STATUS_MAP[record.status];
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
      },
    },
    {
      title: '需要重启',
      dataIndex: 'requires_restart',
      width: 100,
      search: false,
      valueType: 'select',
      valueEnum: {
        true: { text: '是', status: 'Warning' },
        false: { text: '否', status: 'Default' },
      },
      render: (_, record) =>
        record.requires_restart ? (
          <Tag icon={<ExclamationCircleOutlined />} color="warning">
            需要
          </Tag>
        ) : (
          <Tag color="default">不需要</Tag>
        ),
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      width: 160,
      valueType: 'dateTime',
      search: false,
      sorter: true,
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
            danger
            icon={<CloseCircleOutlined />}
            onClick={() => handleToggleStatus(record, ConfigStatus.INACTIVE)}
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
          >
            激活
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
      message.success(
        newStatus === ConfigStatus.ACTIVE ? '配置已激活' : '配置已停用'
      );
      actionRef.current?.reload();
    } catch (error) {
      message.error('状态切换失败');
    }
  };

  // 删除配置
  const handleDelete = (record: Configuration) => {
    confirm({
      title: '确认删除',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除配置 <strong>{record.display_name}</strong> 吗？</p>
          <p style={{ color: '#ff4d4f', fontSize: 12 }}>
            此操作不可恢复，配置历史也会被删除！
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
    <ProTable<Configuration>
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
        showQuickJumper: true,
        pageSizeOptions: ['10', '20', '50', '100'],
      }}
      dateFormatter="string"
      headerTitle="配置管理"
      toolBarRender={() => [
        <Button
          key="reload_cache"
          icon={<SyncOutlined spin={reloading} />}
          onClick={handleReload}
          loading={reloading}
        >
          重新加载
        </Button>,
        <Button
          key="export"
          icon={<DownloadOutlined />}
          onClick={() => handleExport()}
          loading={exporting}
        >
          导出配置
        </Button>,
        <Upload
          key="import"
          accept=".json"
          showUploadList={false}
          beforeUpload={handleImport}
        >
          <Button
            icon={<UploadOutlined />}
            loading={importing}
          >
            导入配置
          </Button>
        </Upload>,
        <Button
          key="reload"
          icon={<ReloadOutlined />}
          onClick={() => actionRef.current?.reload()}
        >
          刷新列表
        </Button>,
        <Button
          key="create"
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/configs/new')}
        >
          新增配置
        </Button>,
      ]}
    />
  );
};

export default ConfigList;
