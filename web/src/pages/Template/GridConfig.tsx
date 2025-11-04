/**
 * 网格策略配置页面 - 专业网格条件单
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  Space,
  message,
  Typography,
  Alert,
  Row,
  Col,
  Divider,
  Tooltip,
  Spin,
  Radio,
  Select,
  Slider,
} from 'antd';
import {
  SaveOutlined,
  QuestionCircleOutlined,
  LeftOutlined,
} from '@ant-design/icons';
import type { GridStrategy } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const GridConfig: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gridData, setGridData] = useState<GridStrategy | null>(null);

  const isNew = id === 'new';

  // 加载网格配置
  useEffect(() => {
    if (!isNew) {
      loadGridData();
    }
  }, [id]);

  const loadGridData = async () => {
    setLoading(true);
    try {
      // TODO: 替换为真实API
      // const data = await getGridStrategy(Number(id));
      // setGridData(data);
      // form.setFieldsValue(data);
      message.info('加载网格数据（模拟）');
    } catch (error) {
      message.error('加载网格配置失败');
      navigate('/templates');
    } finally {
      setLoading(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      console.log('网格策略配置:', values);

      // TODO: 调用API保存配置
      if (isNew) {
        // await createGridStrategy(values);
        message.success('网格策略创建成功');
      } else {
        // await updateGridStrategy(Number(id), values);
        message.success('网格策略更新成功');
      }

      navigate('/templates');
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单填写');
      } else {
        message.error('保存失败');
      }
    } finally {
      setSaving(false);
    }
  };

  // 加载中
  if (loading && !isNew) {
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
      <div style={{ marginBottom: 24 }}>
        <Button
          type="text"
          icon={<LeftOutlined />}
          onClick={() => navigate('/templates')}
          style={{ marginBottom: 12 }}
        >
          返回策略列表
        </Button>
        <Title level={3} style={{ marginBottom: 8, color: '#111827' }}>
          📊 {isNew ? '新增网格策略' : '编辑网格策略'}
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>
          专业网格交易策略配置，支持多种网格模式和高级风控功能
        </Text>
      </div>

      {/* 提示信息 */}
      <Alert
        message="网格策略说明"
        description="网格交易通过在价格区间内设置多个买卖网格，自动执行低买高卖操作。适合震荡行情，请根据市场情况合理设置参数。"
        type="info"
        showIcon
        closable
        style={{
          marginBottom: 24,
          background: '#EFF6FF',
          border: '1px solid #3B82F6',
        }}
      />

      <Row gutter={24}>
        {/* 左侧：配置表单 */}
        <Col span={16}>
          <Card
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
              border: 'none',
            }}
            styles={{ body: { padding: '32px' } }}
          >
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                name: '',
                enabled: true,
                symbol: 'BNBUSDT',
                investment_amount: 1000,
                grid_type: 'arithmetic',
                grid_count: 10,
                price_range_mode: 'auto',
                price_reference: 'current',
                price_range_percent: 20,
                min_profit_rate: 0.5,
                direction: 'both',
                first_order_mode: 'immediate',
                order_amount_mode: 'equal',
                min_order_amount: 10,
                max_order_amount: 100,
                grid_tracking: false,
                take_profit_enabled: false,
                take_profit_type: 'percent',
                take_profit_percent: 10,
                stop_loss_enabled: false,
                stop_loss_type: 'percent',
                stop_loss_percent: 5,
                trailing_stop: false,
                max_position_percent: 100,
                daily_trade_limit: 0,
                price_deviation_alert: 10,
                trigger_mode: 'immediate',
                trigger_price: null,
              }}
            >
              {/* ========== 基础配置 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #3B82F6',
              }}>
                基础配置
              </div>

              <Form.Item
                name="name"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    策略名称
                  </span>
                }
                rules={[{ required: true, message: '请输入策略名称' }]}
              >
                <Input
                  placeholder="例如: BNB网格-震荡区间"
                  size="large"
                  style={{ fontSize: 14 }}
                />
              </Form.Item>

              <Form.Item
                name="enabled"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    启用策略
                  </span>
                }
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="symbol"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        交易对
                      </span>
                    }
                    rules={[{ required: true, message: '请输入交易对' }]}
                  >
                    <Input
                      placeholder="例如: BNBUSDT"
                      size="large"
                      style={{ fontSize: 14 }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="investment_amount"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        投资金额 (USDT)
                      </span>
                    }
                    rules={[{ required: true, message: '请输入投资金额' }]}
                  >
                    <InputNumber
                      placeholder="投资金额"
                      min={10}
                      max={1000000}
                      step={100}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                      formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* ========== 网格参数 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #3B82F6',
              }}>
                网格参数
              </div>

              <Form.Item
                name="grid_type"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    网格类型
                    <Tooltip title="等差网格：每格价差相等；等比网格：每格涨跌幅相等">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
              >
                <Radio.Group size="large">
                  <Radio.Button value="arithmetic">等差网格</Radio.Button>
                  <Radio.Button value="geometric">等比网格</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="grid_count"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        网格数量
                      </span>
                    }
                    rules={[{ required: true, message: '请输入网格数量' }]}
                  >
                    <InputNumber
                      placeholder="建议 5-50"
                      min={2}
                      max={100}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="min_profit_rate"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        单格利润率 (%)
                      </span>
                    }
                    rules={[{ required: true, message: '请输入单格利润率' }]}
                  >
                    <InputNumber
                      placeholder="建议 0.5-2%"
                      min={0.1}
                      max={10}
                      step={0.1}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                      formatter={(value) => `${value}%`}
                      parser={(value) => value!.replace('%', '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name="price_range_mode"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    价格区间模式
                  </span>
                }
              >
                <Radio.Group size="large">
                  <Radio.Button value="auto">自动计算</Radio.Button>
                  <Radio.Button value="manual">手动设置</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.price_range_mode !== currentValues.price_range_mode
                }
              >
                {({ getFieldValue }) => {
                  const mode = getFieldValue('price_range_mode');
                  if (mode === 'auto') {
                    return (
                      <>
                        <Form.Item
                          name="price_reference"
                          label={
                            <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                              参考价格
                            </span>
                          }
                        >
                          <Select size="large" style={{ fontSize: 14 }}>
                            <Option value="current">当前市价</Option>
                            <Option value="avg_24h">24小时均价</Option>
                            <Option value="highest_bid">最高买价</Option>
                            <Option value="lowest_ask">最低卖价</Option>
                          </Select>
                        </Form.Item>
                        <Form.Item
                          name="price_range_percent"
                          label={
                            <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                              价格区间百分比 (%)
                              <Tooltip title="上下浮动的百分比，例如20%表示参考价±20%">
                                <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                              </Tooltip>
                            </span>
                          }
                        >
                          <Slider
                            min={5}
                            max={50}
                            step={5}
                            marks={{
                              5: '5%',
                              15: '15%',
                              25: '25%',
                              35: '35%',
                              50: '50%',
                            }}
                          />
                        </Form.Item>
                      </>
                    );
                  } else {
                    return (
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item
                            name="price_min"
                            label={
                              <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                                最低价格
                              </span>
                            }
                            rules={[{ required: true, message: '请输入最低价格' }]}
                          >
                            <InputNumber
                              placeholder="最低价格"
                              min={0.01}
                              step={0.01}
                              size="large"
                              style={{ width: '100%', fontSize: 14 }}
                              prefix="$"
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item
                            name="price_max"
                            label={
                              <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                                最高价格
                              </span>
                            }
                            rules={[{ required: true, message: '请输入最高价格' }]}
                          >
                            <InputNumber
                              placeholder="最高价格"
                              min={0.01}
                              step={0.01}
                              size="large"
                              style={{ width: '100%', fontSize: 14 }}
                              prefix="$"
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    );
                  }
                }}
              </Form.Item>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* ========== 交易设置 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #8B5CF6',
              }}>
                交易设置
              </div>

              <Form.Item
                name="direction"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    交易方向
                  </span>
                }
              >
                <Radio.Group size="large">
                  <Radio.Button value="both">双向交易</Radio.Button>
                  <Radio.Button value="long">只做多</Radio.Button>
                  <Radio.Button value="short">只做空</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                name="first_order_mode"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    首次建仓
                    <Tooltip title="立即建仓：启动后立刻下单；等待触发：等价格触及网格才下单">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
              >
                <Radio.Group size="large">
                  <Radio.Button value="immediate">立即建仓</Radio.Button>
                  <Radio.Button value="wait">等待触发</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                name="order_amount_mode"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    下单金额模式
                  </span>
                }
              >
                <Radio.Group size="large">
                  <Radio.Button value="equal">等额分配</Radio.Button>
                  <Radio.Button value="pyramid">金字塔加仓</Radio.Button>
                  <Radio.Button value="reverse_pyramid">倒金字塔</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="min_order_amount"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        最小单笔金额 (USDT)
                      </span>
                    }
                  >
                    <InputNumber
                      placeholder="最小金额"
                      min={1}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                      prefix="$"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="max_order_amount"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        最大单笔金额 (USDT)
                      </span>
                    }
                  >
                    <InputNumber
                      placeholder="最大金额"
                      min={1}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                      prefix="$"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* ========== 高级功能 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #F59E0B',
              }}>
                高级功能
              </div>

              <Form.Item
                name="grid_tracking"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    网格追踪
                    <Tooltip title="价格突破区间时，自动调整网格跟随价格移动">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* ========== 止盈止损 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #10B981',
              }}>
                止盈止损
              </div>

              <Form.Item
                name="take_profit_enabled"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    启用止盈
                  </span>
                }
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.take_profit_enabled !== currentValues.take_profit_enabled
                }
              >
                {({ getFieldValue }) =>
                  getFieldValue('take_profit_enabled') ? (
                    <>
                      <Form.Item
                        name="take_profit_type"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            止盈方式
                          </span>
                        }
                      >
                        <Radio.Group size="large">
                          <Radio.Button value="percent">盈利百分比</Radio.Button>
                          <Radio.Button value="price">目标价格</Radio.Button>
                          <Radio.Button value="amount">盈利金额</Radio.Button>
                        </Radio.Group>
                      </Form.Item>
                      <Form.Item
                        name="take_profit_percent"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            止盈目标
                          </span>
                        }
                        rules={[{ required: true, message: '请输入止盈目标' }]}
                      >
                        <InputNumber
                          placeholder="止盈目标"
                          min={1}
                          max={100}
                          step={1}
                          size="large"
                          style={{ width: '100%', fontSize: 14 }}
                          formatter={(value) => `${value}%`}
                          parser={(value) => value!.replace('%', '')}
                        />
                      </Form.Item>
                    </>
                  ) : null
                }
              </Form.Item>

              <Form.Item
                name="stop_loss_enabled"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    启用止损
                  </span>
                }
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.stop_loss_enabled !== currentValues.stop_loss_enabled
                }
              >
                {({ getFieldValue }) =>
                  getFieldValue('stop_loss_enabled') ? (
                    <>
                      <Form.Item
                        name="stop_loss_type"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            止损方式
                          </span>
                        }
                      >
                        <Radio.Group size="large">
                          <Radio.Button value="percent">亏损百分比</Radio.Button>
                          <Radio.Button value="price">止损价格</Radio.Button>
                          <Radio.Button value="amount">亏损金额</Radio.Button>
                        </Radio.Group>
                      </Form.Item>
                      <Form.Item
                        name="stop_loss_percent"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            止损阈值
                          </span>
                        }
                        rules={[{ required: true, message: '请输入止损阈值' }]}
                      >
                        <InputNumber
                          placeholder="止损阈值"
                          min={1}
                          max={50}
                          step={1}
                          size="large"
                          style={{ width: '100%', fontSize: 14 }}
                          formatter={(value) => `${value}%`}
                          parser={(value) => value!.replace('%', '')}
                        />
                      </Form.Item>
                      <Form.Item
                        name="trailing_stop"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            移动止损
                            <Tooltip title="随着盈利增加，自动上移止损价格">
                              <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                            </Tooltip>
                          </span>
                        }
                        valuePropName="checked"
                      >
                        <Switch />
                      </Form.Item>
                    </>
                  ) : null
                }
              </Form.Item>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* ========== 风控设置 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #EF4444',
              }}>
                风控设置
              </div>

              <Form.Item
                name="max_position_percent"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    最大持仓比例 (%)
                    <Tooltip title="投资金额中最多用于持仓的比例">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
              >
                <Slider
                  min={10}
                  max={100}
                  step={10}
                  marks={{
                    10: '10%',
                    50: '50%',
                    100: '100%',
                  }}
                />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="daily_trade_limit"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        单日交易次数限制
                        <Tooltip title="0表示不限制">
                          <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                        </Tooltip>
                      </span>
                    }
                  >
                    <InputNumber
                      placeholder="0=不限制"
                      min={0}
                      max={1000}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="price_deviation_alert"
                    label={
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                        价格偏离预警 (%)
                      </span>
                    }
                  >
                    <InputNumber
                      placeholder="偏离预警"
                      min={1}
                      max={50}
                      size="large"
                      style={{ width: '100%', fontSize: 14 }}
                      formatter={(value) => `${value}%`}
                      parser={(value) => value!.replace('%', '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* ========== 启动条件 ========== */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #06B6D4',
              }}>
                启动条件
              </div>

              <Form.Item
                name="trigger_mode"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    启动方式
                  </span>
                }
              >
                <Radio.Group size="large">
                  <Radio.Button value="immediate">立即启动</Radio.Button>
                  <Radio.Button value="price">价格触发</Radio.Button>
                  <Radio.Button value="time">定时启动</Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                noStyle
                shouldUpdate={(prevValues, currentValues) =>
                  prevValues.trigger_mode !== currentValues.trigger_mode
                }
              >
                {({ getFieldValue }) => {
                  const mode = getFieldValue('trigger_mode');
                  if (mode === 'price') {
                    return (
                      <Form.Item
                        name="trigger_price"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            触发价格
                          </span>
                        }
                        rules={[{ required: true, message: '请输入触发价格' }]}
                      >
                        <InputNumber
                          placeholder="达到此价格时启动"
                          min={0.01}
                          step={0.01}
                          size="large"
                          style={{ width: '100%', fontSize: 14 }}
                          prefix="$"
                        />
                      </Form.Item>
                    );
                  } else if (mode === 'time') {
                    return (
                      <Form.Item
                        name="trigger_time"
                        label={
                          <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                            定时启动时间
                          </span>
                        }
                        rules={[{ required: true, message: '请选择启动时间' }]}
                      >
                        <Input
                          type="datetime-local"
                          size="large"
                          style={{ fontSize: 14 }}
                        />
                      </Form.Item>
                    );
                  }
                  return null;
                }}
              </Form.Item>

              <Divider />

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={handleSave}
                    loading={saving}
                    size="large"
                    style={{
                      background: '#3B82F6',
                      borderColor: '#3B82F6',
                      fontSize: 14,
                      fontWeight: 500,
                    }}
                  >
                    保存配置
                  </Button>
                  <Button
                    onClick={() => navigate('/templates')}
                    size="large"
                    style={{ fontSize: 14 }}
                  >
                    取消
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* 右侧：配置指南 */}
        <Col span={8}>
          <Card
            title="配置指南"
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
              marginBottom: 16,
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size={16}>
              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>网格类型</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#6B7280', marginBottom: 0 }}>
                  • 等差网格：适合低波动币种<br />
                  • 等比网格：适合高波动币种
                </Paragraph>
              </div>

              <Divider style={{ margin: 0 }} />

              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>交易方向</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#6B7280', marginBottom: 0 }}>
                  • 双向交易：适合震荡行情<br />
                  • 只做多：适合牛市上涨<br />
                  • 只做空：适合熊市下跌
                </Paragraph>
              </div>

              <Divider style={{ margin: 0 }} />

              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>下单模式</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#6B7280', marginBottom: 0 }}>
                  • 等额分配：每格金额相同<br />
                  • 金字塔：价格越低买入越多<br />
                  • 倒金字塔：价格越高买入越多
                </Paragraph>
              </div>

              <Divider style={{ margin: 0 }} />

              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>风险提示</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#EF4444', marginBottom: 0 }}>
                  ⚠️ 网格策略在单边行情下可能产生亏损<br />
                  ⚠️ 建议设置止损保护<br />
                  ⚠️ 定期检查策略运行状态
                </Paragraph>
              </div>
            </Space>
          </Card>

          <Card
            title="参数预览"
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <Form.Item noStyle shouldUpdate>
              {() => {
                const values = form.getFieldsValue();
                return (
                  <Space direction="vertical" style={{ width: '100%' }} size={12}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>策略名称:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>{values.name || '--'}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>交易对:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>{values.symbol || '--'}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>投资金额:</Text>
                      <Text strong style={{ color: '#3B82F6', fontSize: 13 }}>
                        ${values.investment_amount || 0}
                      </Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>网格类型:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>
                        {values.grid_type === 'arithmetic' ? '等差网格' : '等比网格'}
                      </Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>网格数量:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>{values.grid_count || 0} 个</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>单格利润率:</Text>
                      <Text strong style={{ color: '#10B981', fontSize: 13 }}>
                        {values.min_profit_rate || 0}%
                      </Text>
                    </div>
                    <Divider style={{ margin: '8px 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>策略状态:</Text>
                      <Text strong style={{ color: values.enabled ? '#10B981' : '#9CA3AF', fontSize: 13 }}>
                        {values.enabled ? '已启用' : '已停用'}
                      </Text>
                    </div>
                  </Space>
                );
              }}
            </Form.Item>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default GridConfig;
