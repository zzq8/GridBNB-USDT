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

// 交易所类型定义
const EXCHANGE_TYPES = {
  BINANCE: { value: 'binance', label: '币安 Binance', icon: '🟡' },
  OKX: { value: 'okx', label: '欧易 OKX', icon: '⚫' },
};

// 通知类型定义
const NOTIFICATION_TYPES = {
  WECHAT: { value: 'wechat', label: '微信通知', icon: '💬' },
  EMAIL: { value: 'email', label: '邮件通知', icon: '📧' },
  TELEGRAM: { value: 'telegram', label: 'Telegram', icon: '✈️' },
  WEBHOOK: { value: 'webhook', label: 'Webhook', icon: '🔗' },
};

// 交易所配置字段模板
const EXCHANGE_CONFIG_FIELDS = {
  binance: [
    { key: 'API_KEY', label: 'API Key', type: 'input', sensitive: true, required: true },
    { key: 'API_SECRET', label: 'API Secret', type: 'password', sensitive: true, required: true },
    { key: 'BASE_URL', label: 'API地址', type: 'input', sensitive: false, required: false, defaultValue: 'https://api.binance.com' },
  ],
  okx: [
    { key: 'API_KEY', label: 'API Key', type: 'input', sensitive: true, required: true },
    { key: 'API_SECRET', label: 'API Secret', type: 'password', sensitive: true, required: true },
    { key: 'PASSPHRASE', label: 'Passphrase', type: 'password', sensitive: true, required: true },
    { key: 'BASE_URL', label: 'API地址', type: 'input', sensitive: false, required: false, defaultValue: 'https://www.okx.com' },
  ],
};

// 通知配置字段模板
const NOTIFICATION_CONFIG_FIELDS = {
  wechat: [
    { key: 'CORP_ID', label: '企业ID', type: 'input', sensitive: false, required: true },
    { key: 'CORP_SECRET', label: '企业Secret', type: 'password', sensitive: true, required: true },
    { key: 'AGENT_ID', label: '应用AgentId', type: 'input', sensitive: false, required: true },
  ],
  email: [
    { key: 'SMTP_HOST', label: 'SMTP服务器', type: 'input', sensitive: false, required: true },
    { key: 'SMTP_PORT', label: 'SMTP端口', type: 'input', sensitive: false, required: true, defaultValue: '587' },
    { key: 'SMTP_USER', label: '发件邮箱', type: 'input', sensitive: false, required: true },
    { key: 'SMTP_PASSWORD', label: '邮箱密码/授权码', type: 'password', sensitive: true, required: true },
    { key: 'RECEIVER_EMAIL', label: '收件邮箱', type: 'input', sensitive: false, required: true },
  ],
  telegram: [
    { key: 'BOT_TOKEN', label: 'Bot Token', type: 'password', sensitive: true, required: true },
    { key: 'CHAT_ID', label: 'Chat ID', type: 'input', sensitive: false, required: true },
  ],
  webhook: [
    { key: 'WEBHOOK_URL', label: 'Webhook URL', type: 'input', sensitive: false, required: true },
    { key: 'WEBHOOK_SECRET', label: 'Webhook Secret', type: 'password', sensitive: true, required: false },
  ],
};

const ConfigDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<Configuration | null>(null);
  const [history, setHistory] = useState<ConfigurationHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // 新增：配置流程状态
  const [configType, setConfigType] = useState<string>(ConfigType.EXCHANGE);
  const [subType, setSubType] = useState<string>(''); // 交易所类型或通知类型

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
      // 验证必须选择了子类型
      if (!subType) {
        message.error('请选择具体的交易所或通知方式');
        return;
      }

      const values = await form.validateFields();
      setSaving(true);

      // 提取动态字段的值
      const dynamicFields: Record<string, any> = {};
      Object.keys(values).forEach((key) => {
        if (key.startsWith('dynamic_')) {
          const fieldKey = key.replace('dynamic_', '');
          dynamicFields[fieldKey] = values[key];
        }
      });

      // 生成配置键和显示名称
      const configKeyPrefix = configType === ConfigType.EXCHANGE
        ? subType.toUpperCase()
        : subType.toUpperCase();

      // 构建配置数据（多条配置，一次性创建）
      const configs = Object.entries(dynamicFields).map(([key, value]) => ({
        config_key: `${configKeyPrefix}_${key}`,
        display_name: `${EXCHANGE_TYPES[subType.toUpperCase() as keyof typeof EXCHANGE_TYPES]?.label || NOTIFICATION_TYPES[subType.toUpperCase() as keyof typeof NOTIFICATION_TYPES]?.label || subType} - ${key}`,
        config_value: value,
        config_type: configType,
        status: values.status,
        is_sensitive: key.toLowerCase().includes('secret') || key.toLowerCase().includes('password') || key.toLowerCase().includes('token'),
        is_required: true,
        requires_restart: configType === ConfigType.EXCHANGE,
      }));

      // 批量创建配置
      if (isNew) {
        for (const config of configs) {
          await createConfig(config);
        }
        message.success(`成功创建 ${configs.length} 条配置`);
      } else {
        // 编辑模式下，更新单条配置
        await updateConfig(Number(id), {
          config_value: Object.values(dynamicFields)[0],
          status: values.status,
        });
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
      <div style={{
        textAlign: 'center',
        padding: '100px 0',
        background: '#FFFFFF',
        borderRadius: 12,
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      }}>
        <Spin size="large" tip="加载中...">
          <div style={{ padding: '50px' }} />
        </Spin>
      </div>
    );
  }

  return (
    <div style={{ background: 'transparent' }}>
      {/* 页面标题 */}
      <Title level={3} style={{ marginBottom: 24, color: '#111827' }}>
        {isNew ? '新增配置' : '编辑配置'}
      </Title>

      <Row gutter={24}>
        {/* 左侧：配置表单 */}
        <Col span={16}>
          <Card
            variant="outlined"
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
            }}
          >
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
                status: ConfigStatus.ACTIVE,
                config_type: ConfigType.EXCHANGE,
              }}
              onValuesChange={(changedValues) => {
                if (changedValues.config_type) {
                  setConfigType(changedValues.config_type);
                  setSubType(''); // 重置子类型
                }
              }}
            >
              {/* 第一步：选择配置类型 */}
              <Form.Item
                name="config_type"
                label={<span style={{ fontSize: 15, fontWeight: 600 }}>配置类型</span>}
                rules={[{ required: true, message: '请选择配置类型' }]}
              >
                <Select
                  placeholder="选择配置类型"
                  size="large"
                  onChange={(value) => setConfigType(value)}
                  disabled={!isNew}
                  style={{ fontSize: 14 }}
                >
                  <Option value={ConfigType.EXCHANGE}>
                    <div style={{ display: 'flex', alignItems: 'center', padding: '4px 0' }}>
                      <span style={{ fontSize: 20, marginRight: 12 }}>🏦</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 14, color: '#111827' }}>交易所配置</div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          配置币安、欧易等交易所的API密钥
                        </Text>
                      </div>
                    </div>
                  </Option>
                  <Option value={ConfigType.NOTIFICATION}>
                    <div style={{ display: 'flex', alignItems: 'center', padding: '4px 0' }}>
                      <span style={{ fontSize: 20, marginRight: 12 }}>🔔</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 14, color: '#111827' }}>通知配置</div>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          配置微信、邮件、Telegram等通知方式
                        </Text>
                      </div>
                    </div>
                  </Option>
                </Select>
              </Form.Item>

              <Divider style={{ margin: '24px 0', borderColor: '#E5E7EB' }} />

              {/* 第二步：根据配置类型选择具体类型 */}
              {configType === ConfigType.EXCHANGE && (
                <Form.Item
                  label={<span style={{ fontSize: 15, fontWeight: 600 }}>选择交易所</span>}
                  required
                  style={{ marginBottom: 32 }}
                >
                  <Row gutter={16}>
                    {Object.values(EXCHANGE_TYPES).map((exchange) => (
                      <Col span={12} key={exchange.value}>
                        <Card
                          hoverable
                          onClick={() => setSubType(exchange.value)}
                          style={{
                            border: subType === exchange.value ? '2px solid #3B82F6' : '1px solid #E5E7EB',
                            background: subType === exchange.value ? '#EFF6FF' : '#FFFFFF',
                            cursor: 'pointer',
                            borderRadius: 8,
                            transition: 'all 0.3s ease',
                            minHeight: 120,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                          styles={{
                            body: {
                              padding: '24px 16px',
                              textAlign: 'center',
                              width: '100%',
                            },
                          }}
                        >
                          <div style={{ fontSize: 48, marginBottom: 12, lineHeight: 1 }}>{exchange.icon}</div>
                          <div style={{
                            fontWeight: 600,
                            fontSize: 16,
                            color: subType === exchange.value ? '#3B82F6' : '#111827',
                            lineHeight: 1.4,
                          }}>
                            {exchange.label}
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Form.Item>
              )}

              {configType === ConfigType.NOTIFICATION && (
                <Form.Item
                  label={<span style={{ fontSize: 15, fontWeight: 600 }}>选择通知方式</span>}
                  required
                  style={{ marginBottom: 32 }}
                >
                  <Row gutter={[16, 16]}>
                    {Object.values(NOTIFICATION_TYPES).map((notif) => (
                      <Col span={12} key={notif.value}>
                        <Card
                          hoverable
                          onClick={() => setSubType(notif.value)}
                          style={{
                            border: subType === notif.value ? '2px solid #3B82F6' : '1px solid #E5E7EB',
                            background: subType === notif.value ? '#EFF6FF' : '#FFFFFF',
                            cursor: 'pointer',
                            borderRadius: 8,
                            transition: 'all 0.3s ease',
                            minHeight: 110,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                          styles={{
                            body: {
                              padding: '20px 16px',
                              textAlign: 'center',
                              width: '100%',
                            },
                          }}
                        >
                          <div style={{ fontSize: 40, marginBottom: 10, lineHeight: 1 }}>{notif.icon}</div>
                          <div style={{
                            fontWeight: 600,
                            fontSize: 15,
                            color: subType === notif.value ? '#3B82F6' : '#111827',
                            lineHeight: 1.4,
                          }}>
                            {notif.label}
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Form.Item>
              )}

              {/* 第三步：根据选择的具体类型显示对应的配置字段 */}
              {subType && (
                <>
                  <Divider style={{ margin: '24px 0', borderColor: '#E5E7EB' }}>
                    <Text type="secondary" style={{ fontSize: 14, fontWeight: 500 }}>配置详情</Text>
                  </Divider>

                  {/* 动态渲染配置字段 */}
                  {configType === ConfigType.EXCHANGE &&
                    EXCHANGE_CONFIG_FIELDS[subType as keyof typeof EXCHANGE_CONFIG_FIELDS]?.map((field) => (
                      <Form.Item
                        key={field.key}
                        name={`dynamic_${field.key}`}
                        label={<span style={{ fontSize: 14, fontWeight: 500 }}>{field.label}</span>}
                        rules={[{ required: field.required, message: `请输入${field.label}` }]}
                      >
                        {field.type === 'password' ? (
                          <Input.Password
                            placeholder={`请输入${field.label}`}
                            style={{ fontFamily: 'monospace', fontSize: 14 }}
                            size="large"
                          />
                        ) : (
                          <Input
                            placeholder={field.defaultValue || `请输入${field.label}`}
                            style={{ fontFamily: 'monospace', fontSize: 14 }}
                            size="large"
                          />
                        )}
                      </Form.Item>
                    ))}

                  {configType === ConfigType.NOTIFICATION &&
                    NOTIFICATION_CONFIG_FIELDS[subType as keyof typeof NOTIFICATION_CONFIG_FIELDS]?.map((field) => (
                      <Form.Item
                        key={field.key}
                        name={`dynamic_${field.key}`}
                        label={<span style={{ fontSize: 14, fontWeight: 500 }}>{field.label}</span>}
                        rules={[{ required: field.required, message: `请输入${field.label}` }]}
                      >
                        {field.type === 'password' ? (
                          <Input.Password
                            placeholder={`请输入${field.label}`}
                            style={{ fontFamily: 'monospace', fontSize: 14 }}
                            size="large"
                          />
                        ) : (
                          <Input
                            placeholder={field.defaultValue || `请输入${field.label}`}
                            style={{ fontFamily: 'monospace', fontSize: 14 }}
                            size="large"
                          />
                        )}
                      </Form.Item>
                    ))}

                  <Form.Item
                    name="status"
                    label={<span style={{ fontSize: 14, fontWeight: 500 }}>状态</span>}
                    rules={[{ required: true }]}
                  >
                    <Select size="large" style={{ fontSize: 14 }}>
                      <Option value={ConfigStatus.ACTIVE}>已激活</Option>
                      <Option value={ConfigStatus.INACTIVE}>已停用</Option>
                    </Select>
                  </Form.Item>
                </>
              )}

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
              <ProCard
                title="配置信息"
                style={{
                  marginBottom: 16,
                  background: '#FFFFFF',
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                }}
              >
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
                style={{
                  background: '#FFFFFF',
                  borderRadius: 12,
                  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                }}
              >
                {!history || history.length === 0 ? (
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
