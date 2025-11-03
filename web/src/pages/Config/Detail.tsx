/**
 * 配置详情页面 - 编辑配置和查看历史
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  Select,
  Switch,
  Button,
  Space,
  message,
  Spin,
  Divider,
  Timeline,
  Typography,
  Modal,
  Tag,
  Row,
  Col,
  Alert,
} from 'antd';
import {
  SaveOutlined,
  RollbackOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { ProCard } from '@ant-design/pro-components';
import {
  getConfig,
  updateConfig,
  createConfig,
  getConfigHistory,
  rollbackConfig,
} from '@/api/config';
import type { Configuration, ConfigurationHistory } from '@/types';
import { ConfigType, ConfigStatus } from '@/types';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;
const { confirm } = Modal;

const ConfigDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<Configuration | null>(null);
  const [history, setHistory] = useState<ConfigurationHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const isNew = id === 'new';

  // 加载配置详情
  useEffect(() => {
    if (!isNew) {
      loadConfig();
      loadHistory();
    }
  }, [id]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const data = await getConfig(Number(id));
      setConfig(data);
      form.setFieldsValue(data);
    } catch (error) {
      message.error('加载配置失败');
      navigate('/configs');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const response = await getConfigHistory(Number(id), {
        page: 1,
        page_size: 20,
      });
      setHistory(response.items);
    } catch (error) {
      console.error('加载历史失败', error);
    } finally {
      setHistoryLoading(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      if (isNew) {
        await createConfig(values);
        message.success('配置创建成功');
      } else {
        await updateConfig(Number(id), values);
        message.success('配置更新成功');
        loadHistory(); // 重新加载历史
      }

      navigate('/configs');
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单填写');
      } else {
        message.error(isNew ? '创建失败' : '更新失败');
      }
    } finally {
      setSaving(false);
    }
  };

  // 回滚到历史版本
  const handleRollback = (historyItem: ConfigurationHistory) => {
    confirm({
      title: '确认回滚',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要回滚到版本 <strong>v{historyItem.version}</strong> 吗？</p>
          <p>变更时间: {dayjs(historyItem.changed_at).format('YYYY-MM-DD HH:mm:ss')}</p>
          <Divider style={{ margin: '12px 0' }} />
          <Text type="secondary">新值:</Text>
          <Paragraph
            code
            copyable
            ellipsis={{ rows: 3, expandable: true }}
            style={{ marginTop: 8 }}
          >
            {historyItem.new_value}
          </Paragraph>
        </div>
      ),
      okText: '确认回滚',
      cancelText: '取消',
      onOk: async () => {
        try {
          await rollbackConfig(Number(id), historyItem.version);
          message.success('回滚成功');
          loadConfig();
          loadHistory();
        } catch (error) {
          message.error('回滚失败');
        }
      },
    });
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <div>
      {/* 页面标题 */}
      <Title level={3}>{isNew ? '新增配置' : '编辑配置'}</Title>

      <Row gutter={24}>
        {/* 左侧：配置表单 */}
        <Col span={16}>
          <Card>
            {!isNew && config?.requires_restart && (
              <Alert
                message="重要提示"
                description="修改此配置后需要重启系统才能生效！"
                type="warning"
                showIcon
                icon={<ExclamationCircleOutlined />}
                style={{ marginBottom: 24 }}
              />
            )}

            <Form
              form={form}
              layout="vertical"
              initialValues={{
                status: ConfigStatus.DRAFT,
                config_type: ConfigType.SYSTEM,
                is_required: false,
                is_sensitive: false,
                requires_restart: false,
              }}
            >
              <Form.Item
                name="config_key"
                label="配置键"
                rules={[
                  { required: true, message: '请输入配置键' },
                  { pattern: /^[A-Z_]+$/, message: '只允许大写字母和下划线' },
                ]}
                extra="格式：UPPER_CASE_WITH_UNDERSCORES"
              >
                <Input
                  placeholder="例如: API_KEY, MAX_RETRY_COUNT"
                  disabled={!isNew}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item
                name="display_name"
                label="显示名称"
                rules={[{ required: true, message: '请输入显示名称' }]}
              >
                <Input placeholder="用于前端展示的友好名称" />
              </Form.Item>

              <Form.Item
                name="config_type"
                label="配置类型"
                rules={[{ required: true, message: '请选择配置类型' }]}
              >
                <Select>
                  <Option value={ConfigType.EXCHANGE}>交易所配置</Option>
                  <Option value={ConfigType.TRADING}>交易策略</Option>
                  <Option value={ConfigType.RISK}>风控配置</Option>
                  <Option value={ConfigType.AI}>AI策略</Option>
                  <Option value={ConfigType.NOTIFICATION}>通知配置</Option>
                  <Option value={ConfigType.SYSTEM}>系统配置</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="config_value"
                label="配置值"
                rules={[{ required: true, message: '请输入配置值' }]}
              >
                <TextArea
                  rows={4}
                  placeholder="配置的实际值（支持JSON格式）"
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item name="default_value" label="默认值">
                <Input
                  placeholder="留空表示无默认值"
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>

              <Form.Item name="description" label="描述">
                <TextArea rows={3} placeholder="详细说明此配置的用途" />
              </Form.Item>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="status"
                    label="状态"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={ConfigStatus.DRAFT}>草稿</Option>
                      <Option value={ConfigStatus.ACTIVE}>已激活</Option>
                      <Option value={ConfigStatus.INACTIVE}>已停用</Option>
                      <Option value={ConfigStatus.ARCHIVED}>已归档</Option>
                    </Select>
                  </Form.Item>
                </Col>

                <Col span={8}>
                  <Form.Item
                    name="is_required"
                    label="必填项"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="是" unCheckedChildren="否" />
                  </Form.Item>
                </Col>

                <Col span={8}>
                  <Form.Item
                    name="is_sensitive"
                    label="敏感数据"
                    valuePropName="checked"
                  >
                    <Switch checkedChildren="是" unCheckedChildren="否" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="requires_restart"
                label="修改后需重启"
                valuePropName="checked"
              >
                <Switch checkedChildren="需要" unCheckedChildren="不需要" />
              </Form.Item>

              <Divider />

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={handleSave}
                    loading={saving}
                  >
                    保存
                  </Button>
                  <Button onClick={() => navigate('/configs')}>取消</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：配置信息和历史记录 */}
        <Col span={8}>
          {!isNew && config && (
            <>
              {/* 配置信息卡片 */}
              <ProCard title="配置信息" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text type="secondary">ID:</Text>
                    <Text strong style={{ marginLeft: 8 }}>{config.id}</Text>
                  </div>
                  <div>
                    <Text type="secondary">创建时间:</Text>
                    <Text style={{ marginLeft: 8 }}>
                      {dayjs(config.created_at).format('YYYY-MM-DD HH:mm:ss')}
                    </Text>
                  </div>
                  <div>
                    <Text type="secondary">更新时间:</Text>
                    <Text style={{ marginLeft: 8 }}>
                      {dayjs(config.updated_at).format('YYYY-MM-DD HH:mm:ss')}
                    </Text>
                  </div>
                </Space>
              </ProCard>

              {/* 历史记录卡片 */}
              <ProCard
                title={
                  <Space>
                    <HistoryOutlined />
                    变更历史
                  </Space>
                }
                loading={historyLoading}
              >
                {history.length === 0 ? (
                  <Text type="secondary">暂无历史记录</Text>
                ) : (
                  <Timeline
                    items={history.map((item) => ({
                      dot: <ClockCircleOutlined />,
                      children: (
                        <div>
                          <Space>
                            <Tag>v{item.version}</Tag>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {dayjs(item.changed_at).format('MM-DD HH:mm')}
                            </Text>
                          </Space>
                          <div style={{ marginTop: 8 }}>
                            <Paragraph
                              ellipsis={{ rows: 2, expandable: true }}
                              code
                              style={{ fontSize: 12, marginBottom: 8 }}
                            >
                              {item.new_value}
                            </Paragraph>
                            {item.change_reason && (
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                原因: {item.change_reason}
                              </Text>
                            )}
                          </div>
                          <Button
                            type="link"
                            size="small"
                            icon={<RollbackOutlined />}
                            onClick={() => handleRollback(item)}
                            style={{ padding: 0, marginTop: 4 }}
                          >
                            回滚到此版本
                          </Button>
                        </div>
                      ),
                    }))}
                  />
                )}
              </ProCard>
            </>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default ConfigDetail;
