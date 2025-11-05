/**
 * 网格策略配置页面 - 专业网格条件单
 * 参考专业交易平台的网格交易条件单设计
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
  Collapse,
  Badge,
  Statistic,
  Tag,
  DatePicker,
  TimePicker,
} from 'antd';
import {
  SaveOutlined,
  QuestionCircleOutlined,
  LeftOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseOutlined,
  CheckOutlined,
  UpOutlined,
  DownOutlined,
} from '@ant-design/icons';
import type { GridStrategy } from '@/types';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

const GridConfig: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gridData, setGridData] = useState<GridStrategy | null>(null);

  // 实时行情数据（模拟）
  const [marketData, setMarketData] = useState({
    currentPrice: 628.50,
    priceChange: 2.35,
    priceChangePercent: 0.375,
    highPrice: 635.20,
    lowPrice: 618.80,
    volume24h: '125,847',
    costPrice: 620.00,
  });

  const isNew = id === 'new';

  // 加载网格配置
  useEffect(() => {
    if (!isNew) {
      loadGridData();
    }
    // 模拟实时价格更新
    const interval = setInterval(() => {
      setMarketData(prev => ({
        ...prev,
        currentPrice: prev.currentPrice + (Math.random() - 0.5) * 2,
        priceChangePercent: prev.priceChangePercent + (Math.random() - 0.5) * 0.1,
      }));
    }, 3000);
    return () => clearInterval(interval);
  }, [id]);

  const loadGridData = async () => {
    setLoading(true);
    try {
      // TODO: 替换为真实API
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

      // 组合交易对
      const symbol = `${values.base_currency}${values.quote_currency}`;
      const submitData = {
        ...values,
        symbol, // 添加组合后的交易对
      };

      console.log('网格策略配置:', submitData);

      // TODO: 调用API保存配置
      if (isNew) {
        message.success('网格策略创建成功');
      } else {
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
    <div style={{ background: 'transparent', minHeight: '100vh' }}>
      {/* 顶部导航栏 */}
      <div style={{
        background: 'linear-gradient(135deg, #F43F5E 0%, #E11D48 100%)',
        padding: '16px 24px',
        borderRadius: '12px 12px 0 0',
        marginBottom: 0,
        boxShadow: '0 2px 8px rgba(244, 63, 94, 0.2)',
      }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Button
              type="text"
              icon={<CloseOutlined />}
              onClick={() => navigate('/templates')}
              style={{
                color: '#FFFFFF',
                fontSize: 16,
                fontWeight: 500,
              }}
            >
              取消
            </Button>
          </Col>
          <Col>
            <div style={{ textAlign: 'center' }}>
              <Title level={4} style={{ margin: 0, color: '#FFFFFF' }}>
                新建网格交易条件单
              </Title>
              <Tag color="#FCA5A5" style={{ marginTop: 4, border: 'none' }}>
                网格交易
              </Tag>
            </div>
          </Col>
          <Col>
            <Tooltip title="查看帮助文档">
              <Button
                type="text"
                icon={<QuestionCircleOutlined />}
                style={{
                  color: '#FFFFFF',
                  fontSize: 18,
                }}
              />
            </Tooltip>
          </Col>
        </Row>
      </div>

      {/* 风险提示 */}
      <Alert
        message={
          <Space>
            <WarningOutlined />
            <Text strong>风险提示</Text>
          </Space>
        }
        description="网格交易适合震荡行情，单边行情可能导致亏损。请合理设置参数并做好风险控制。"
        type="warning"
        showIcon={false}
        closable
        style={{
          marginBottom: 16,
          background: '#FEF3C7',
          border: '1px solid #F59E0B',
          borderRadius: 0,
        }}
      />

      <Card
        style={{
          background: '#FFFFFF',
          borderRadius: '0 0 12px 12px',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
          border: 'none',
        }}
        styles={{ body: { padding: '24px' } }}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            base_currency: 'BNB',
            quote_currency: 'USDT',
            grid_type: 'percent',
            trigger_base_price_type: 'current',
            trigger_base_price: null,
            price_min: null,
            price_max: null,
            rise_sell_percent: 1.0,
            fall_buy_percent: 1.0,
            enable_pullback_sell: false,
            pullback_sell_percent: 0.5,
            enable_rebound_buy: false,
            rebound_buy_percent: 0.5,
            order_type: 'limit',
            buy_price_mode: 'bid1',
            sell_price_mode: 'ask1',
            amount_mode: 'quantity',
            grid_symmetric: true,
            order_quantity: null,
            max_position: 100,
            min_position: null,
            enable_multiplier: false,
            expiry_days: -1,
            expiry_date: null,
            enable_monitor_period: false,
            enable_deviation_control: false,
            enable_price_optimization: false,
            enable_delay_confirm: false,
            enable_floor_price: false,
            enable_auto_close: false,
          }}
        >
          {/* ========== 标的选择区 ========== */}
          <div style={{
            background: '#F9FAFB',
            padding: '20px',
            borderRadius: 8,
            marginBottom: 24,
            border: '1px dashed #D1D5DB',
          }}>
            <Text type="secondary" style={{ fontSize: 13, marginBottom: 12, display: 'block' }}>
              请选择/输入交易对
            </Text>

            <Row gutter={8} style={{ marginBottom: 16 }}>
              <Col span={11}>
                <Form.Item
                  name="base_currency"
                  rules={[
                    { required: true, message: '请输入基础货币' },
                    { pattern: /^[A-Z0-9]+$/, message: '请输入大写字母或数字' }
                  ]}
                  style={{ marginBottom: 0 }}
                >
                  <Input
                    size="large"
                    placeholder="如：BNB"
                    style={{ fontSize: 14, textAlign: 'center' }}
                    maxLength={10}
                  />
                </Form.Item>
              </Col>
              <Col span={2} style={{ textAlign: 'center', paddingTop: 8 }}>
                <Text style={{ fontSize: 16, color: '#9CA3AF', fontWeight: 600 }}>/</Text>
              </Col>
              <Col span={11}>
                <Form.Item
                  name="quote_currency"
                  rules={[
                    { required: true, message: '请输入报价货币' },
                    { pattern: /^[A-Z0-9]+$/, message: '请输入大写字母或数字' }
                  ]}
                  style={{ marginBottom: 0 }}
                >
                  <Input
                    size="large"
                    placeholder="如：USDT"
                    style={{ fontSize: 14, textAlign: 'center' }}
                    maxLength={10}
                  />
                </Form.Item>
              </Col>
            </Row>
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                常用稳定币：USDT、BUSD、USDC、DAI
              </Text>
            </div>

            {/* 实时行情信息 */}
            <div style={{
              background: '#FFFFFF',
              padding: '12px',
              borderRadius: 6,
              border: '1px solid #E5E7EB',
            }}>
              <Row gutter={[12, 12]}>
                <Col span={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>当前价</Text>
                    <div style={{ fontSize: 16, fontWeight: 600, color: '#111827', marginTop: 4 }}>
                      ${marketData.currentPrice.toFixed(2)}
                    </div>
                  </div>
                </Col>
                <Col span={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>涨跌幅</Text>
                    <div style={{
                      fontSize: 16,
                      fontWeight: 600,
                      color: marketData.priceChangePercent >= 0 ? '#10B981' : '#EF4444',
                      marginTop: 4,
                    }}>
                      {marketData.priceChangePercent >= 0 ? '+' : ''}{marketData.priceChangePercent.toFixed(2)}%
                    </div>
                  </div>
                </Col>
                <Col span={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>成本价</Text>
                    <div style={{ fontSize: 16, fontWeight: 600, color: '#111827', marginTop: 4 }}>
                      ${marketData.costPrice.toFixed(2)}
                    </div>
                  </div>
                </Col>
              </Row>
              <Divider style={{ margin: '12px 0' }} />
              <Row gutter={[12, 12]}>
                <Col span={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>24H最高</Text>
                    <div style={{ fontSize: 14, fontWeight: 500, color: '#111827', marginTop: 4 }}>
                      ${marketData.highPrice.toFixed(2)}
                    </div>
                  </div>
                </Col>
                <Col span={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>24H最低</Text>
                    <div style={{ fontSize: 14, fontWeight: 500, color: '#111827', marginTop: 4 }}>
                      ${marketData.lowPrice.toFixed(2)}
                    </div>
                  </div>
                </Col>
                <Col span={8}>
                  <div style={{ textAlign: 'center' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>盈亏率</Text>
                    <div style={{
                      fontSize: 14,
                      fontWeight: 500,
                      color: '#10B981',
                      marginTop: 4,
                    }}>
                      +1.37%
                    </div>
                  </div>
                </Col>
              </Row>
            </div>
          </div>

          <Divider style={{ margin: '24px 0' }} />

          {/* ========== 触发条件 ========== */}
          <div style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#111827',
            marginBottom: 20,
          }}>
            触发条件
          </div>

          {/* 价格区间 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Text strong style={{ fontSize: 14, color: '#111827' }}>价格区间</Text>
            <Row gutter={16} style={{ marginTop: 12 }}>
              <Col span={11}>
                <Form.Item
                  name="price_min"
                  label={<Text style={{ fontSize: 13, color: '#6B7280' }}>最低价(元)</Text>}
                  rules={[{ required: true, message: '请输入最低价' }]}
                >
                  <InputNumber
                    placeholder="最低价"
                    min={0.01}
                    step={0.01}
                    size="large"
                    style={{ width: '100%' }}
                    prefix="$"
                  />
                </Form.Item>
              </Col>
              <Col span={2} style={{ textAlign: 'center', paddingTop: 30 }}>
                <Text style={{ fontSize: 16, color: '#9CA3AF' }}>~</Text>
              </Col>
              <Col span={11}>
                <Form.Item
                  name="price_max"
                  label={<Text style={{ fontSize: 13, color: '#6B7280' }}>最高价(元)</Text>}
                  rules={[{ required: true, message: '请输入最高价' }]}
                >
                  <InputNumber
                    placeholder="最高价"
                    min={0.01}
                    step={0.01}
                    size="large"
                    style={{ width: '100%' }}
                    prefix="$"
                  />
                </Form.Item>
              </Col>
            </Row>
            <Button
              type="link"
              size="small"
              style={{ padding: 0, fontSize: 13, color: '#3B82F6' }}
            >
              超出价格设置
            </Button>
          </div>

          {/* 触发基准价 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Text strong style={{ fontSize: 14, color: '#111827' }}>触发基准价</Text>
            <Row gutter={16} style={{ marginTop: 12 }}>
              <Col span={16}>
                <Form.Item name="trigger_base_price" style={{ marginBottom: 0 }}>
                  <InputNumber
                    placeholder="价格(元)"
                    min={0.01}
                    step={0.01}
                    size="large"
                    style={{ width: '100%' }}
                    prefix="$"
                  />
                </Form.Item>
              </Col>
              <Col span={4}>
                <Button size="large" style={{ width: '100%' }}>-</Button>
              </Col>
              <Col span={4}>
                <Button size="large" style={{ width: '100%' }}>+</Button>
              </Col>
            </Row>
            <Form.Item name="trigger_base_price_type" style={{ marginTop: 12, marginBottom: 0 }}>
              <Select size="large">
                <Option value="current">当前价</Option>
                <Option value="cost">成本价</Option>
                <Option value="avg_24h">24小时均价</Option>
                <Option value="manual">手动输入</Option>
              </Select>
            </Form.Item>
          </div>

          {/* 涨跌类型 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Text strong style={{ fontSize: 14, color: '#111827', marginRight: 24 }}>涨跌类型</Text>
            <Form.Item name="grid_type" style={{ marginBottom: 0, display: 'inline-block' }}>
              <Radio.Group size="large">
                <Radio.Button value="percent">按百分比</Radio.Button>
                <Radio.Button value="price">≈ 差价</Radio.Button>
              </Radio.Group>
            </Form.Item>
          </div>

          {/* 网格策略设置 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Row gutter={16}>
              <Col span={20}>
                <Form.Item
                  name="rise_sell_percent"
                  label={
                    <Text style={{ fontSize: 14, color: '#111827' }}>
                      上涨<Text style={{ color: '#EF4444' }}>...卖出</Text>
                    </Text>
                  }
                  rules={[{ required: true, message: '请输入上涨卖出百分比' }]}
                >
                  <Row gutter={8}>
                    <Col span={4}>
                      <Button size="large" style={{ width: '100%' }}>-</Button>
                    </Col>
                    <Col span={16}>
                      <InputNumber
                        placeholder="百分比(%)"
                        min={0.1}
                        max={100}
                        step={0.1}
                        size="large"
                        style={{ width: '100%' }}
                        formatter={(value) => `${value}%`}
                        parser={(value) => value!.replace('%', '')}
                      />
                    </Col>
                    <Col span={4}>
                      <Button size="large" style={{ width: '100%' }}>+</Button>
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
              <Col span={4} style={{ paddingTop: 30 }}>
                <div style={{ textAlign: 'right' }}>
                  <Form.Item name="enable_pullback_sell" valuePropName="checked" style={{ marginBottom: 0 }}>
                    <Switch />
                  </Form.Item>
                  <Text style={{ fontSize: 12, color: '#6B7280', display: 'block', marginTop: 4 }}>
                    回落卖出
                  </Text>
                </div>
              </Col>
            </Row>

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.enable_pullback_sell !== currentValues.enable_pullback_sell
              }
            >
              {({ getFieldValue }) =>
                getFieldValue('enable_pullback_sell') ? (
                  <Form.Item
                    name="pullback_sell_percent"
                    label={
                      <Text style={{ fontSize: 14, color: '#111827' }}>
                        回落<Text style={{ color: '#EF4444' }}>...卖出</Text>
                      </Text>
                    }
                    rules={[{ required: true, message: '请输入回落卖出百分比' }]}
                  >
                    <Row gutter={8}>
                      <Col span={4}>
                        <Button size="large" style={{ width: '100%' }}>-</Button>
                      </Col>
                      <Col span={16}>
                        <InputNumber
                          placeholder="百分比(%)"
                          min={0.1}
                          max={100}
                          step={0.1}
                          size="large"
                          style={{ width: '100%' }}
                          formatter={(value) => `${value}%`}
                          parser={(value) => value!.replace('%', '')}
                        />
                      </Col>
                      <Col span={4}>
                        <Button size="large" style={{ width: '100%' }}>+</Button>
                      </Col>
                    </Row>
                  </Form.Item>
                ) : null
              }
            </Form.Item>

            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={20}>
                <Form.Item
                  name="fall_buy_percent"
                  label={
                    <Text style={{ fontSize: 14, color: '#111827' }}>
                      下跌<Text style={{ color: '#10B981' }}>...买入</Text>
                    </Text>
                  }
                  rules={[{ required: true, message: '请输入下跌买入百分比' }]}
                >
                  <Row gutter={8}>
                    <Col span={4}>
                      <Button size="large" style={{ width: '100%' }}>-</Button>
                    </Col>
                    <Col span={16}>
                      <InputNumber
                        placeholder="百分比(%)"
                        min={0.1}
                        max={100}
                        step={0.1}
                        size="large"
                        style={{ width: '100%' }}
                        formatter={(value) => `${value}%`}
                        parser={(value) => value!.replace('%', '')}
                      />
                    </Col>
                    <Col span={4}>
                      <Button size="large" style={{ width: '100%' }}>+</Button>
                    </Col>
                  </Row>
                </Form.Item>
              </Col>
              <Col span={4} style={{ paddingTop: 30 }}>
                <div style={{ textAlign: 'right' }}>
                  <Form.Item name="enable_rebound_buy" valuePropName="checked" style={{ marginBottom: 0 }}>
                    <Switch />
                  </Form.Item>
                  <Text style={{ fontSize: 12, color: '#6B7280', display: 'block', marginTop: 4 }}>
                    拐点买入
                  </Text>
                </div>
              </Col>
            </Row>

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.enable_rebound_buy !== currentValues.enable_rebound_buy
              }
            >
              {({ getFieldValue }) =>
                getFieldValue('enable_rebound_buy') ? (
                  <Form.Item
                    name="rebound_buy_percent"
                    label={
                      <Text style={{ fontSize: 14, color: '#111827' }}>
                        反弹<Text style={{ color: '#10B981' }}>...买入</Text>
                      </Text>
                    }
                    rules={[{ required: true, message: '请输入反弹买入百分比' }]}
                  >
                    <Row gutter={8}>
                      <Col span={4}>
                        <Button size="large" style={{ width: '100%' }}>-</Button>
                      </Col>
                      <Col span={16}>
                        <InputNumber
                          placeholder="百分比(%)"
                          min={0.1}
                          max={100}
                          step={0.1}
                          size="large"
                          style={{ width: '100%' }}
                          formatter={(value) => `${value}%`}
                          parser={(value) => value!.replace('%', '')}
                        />
                      </Col>
                      <Col span={4}>
                        <Button size="large" style={{ width: '100%' }}>+</Button>
                      </Col>
                    </Row>
                  </Form.Item>
                ) : null
              }
            </Form.Item>
          </div>

          <Divider style={{ margin: '24px 0' }} />

          {/* ========== 委托设置 ========== */}
          <div style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#111827',
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
          }}>
            委托设置
            <Tooltip title="行情数据刷新频率: 3秒/次">
              <WarningOutlined style={{ marginLeft: 8, fontSize: 14, color: '#F59E0B' }} />
            </Tooltip>
          </div>

          {/* 委托类型 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Form.Item name="order_type" style={{ marginBottom: 0 }}>
              <Radio.Group size="large" style={{ width: '100%' }}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Radio.Button value="limit" style={{ width: '100%', textAlign: 'center' }}>
                      <DownOutlined style={{ marginRight: 4, color: '#EF4444' }} />
                      限价委托
                    </Radio.Button>
                  </Col>
                  <Col span={12}>
                    <Radio.Button value="market" style={{ width: '100%', textAlign: 'center' }}>
                      <UpOutlined style={{ marginRight: 4, color: '#10B981' }} />
                      市价委托
                    </Radio.Button>
                  </Col>
                </Row>
              </Radio.Group>
            </Form.Item>
          </div>

          {/* 价格设置 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="buy_price_mode"
                  label={<Text style={{ fontSize: 14, color: '#10B981' }}>买入价格</Text>}
                >
                  <Select size="large">
                    <Option value="immediate">即时买一价</Option>
                    <Option value="bid1">买一价</Option>
                    <Option value="bid2">买二价</Option>
                    <Option value="market">市价</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="sell_price_mode"
                  label={<Text style={{ fontSize: 14, color: '#EF4444' }}>卖出价格</Text>}
                >
                  <Select size="large">
                    <Option value="immediate">即时卖一价</Option>
                    <Option value="ask1">卖一价</Option>
                    <Option value="ask2">卖二价</Option>
                    <Option value="market">市价</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Text type="secondary" style={{ fontSize: 12 }}>
              当无法取得对应报价时，将以即时现价报单
            </Text>
          </div>

          {/* 数量/金额设置 */}
          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Form.Item name="amount_mode" style={{ marginBottom: 16 }}>
              <Radio.Group size="large">
                <Radio.Button value="quantity" style={{ marginRight: 24 }}>
                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                  委托股数
                </Radio.Button>
                <Radio.Button value="amount">
                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                  委托金额
                </Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item name="grid_symmetric" style={{ marginBottom: 16 }}>
              <Radio.Group size="large">
                <Radio.Button value={true} style={{ marginRight: 24 }}>
                  <CheckOutlined style={{ marginRight: 4 }} />
                  对称网格
                </Radio.Button>
                <Radio.Button value={false}>
                  不对称网格
                </Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              name="order_quantity"
              label={<Text style={{ fontSize: 14, color: '#111827' }}>每笔委托</Text>}
              rules={[{ required: true, message: '请输入每笔委托数量' }]}
            >
              <Row gutter={8}>
                <Col span={4}>
                  <Button size="large" style={{ width: '100%' }}>-</Button>
                </Col>
                <Col span={16}>
                  <InputNumber
                    placeholder="股数(股)"
                    min={1}
                    step={1}
                    size="large"
                    style={{ width: '100%' }}
                  />
                </Col>
                <Col span={4}>
                  <Button size="large" style={{ width: '100%' }}>+</Button>
                </Col>
              </Row>
            </Form.Item>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="max_position"
                  label={<Text style={{ fontSize: 14, color: '#111827' }}>最大持仓</Text>}
                  rules={[{ required: true, message: '请输入最大持仓' }]}
                  initialValue={100}
                >
                  <InputNumber
                    placeholder="最大持仓"
                    min={1}
                    size="large"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="min_position"
                  label={<Text style={{ fontSize: 14, color: '#111827' }}>最小底仓</Text>}
                >
                  <InputNumber
                    placeholder="选填"
                    min={0}
                    size="large"
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            </Row>

            <div style={{
              background: '#FEF3C7',
              padding: '8px 12px',
              borderRadius: 4,
              marginBottom: 12,
            }}>
              <Text style={{ fontSize: 12, color: '#92400E' }}>
                可买数量: -- &nbsp;&nbsp;|&nbsp;&nbsp; 当前持仓: --
              </Text>
            </div>

            <Row align="middle" justify="space-between">
              <Col>
                <Text style={{ fontSize: 14, color: '#111827' }}>倍数委托</Text>
              </Col>
              <Col>
                <Form.Item name="enable_multiplier" valuePropName="checked" style={{ marginBottom: 0 }}>
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </div>

          <Divider style={{ margin: '24px 0' }} />

          {/* ========== 截止日期 ========== */}
          <div style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#111827',
            marginBottom: 20,
          }}>
            截止日期
          </div>

          <div style={{
            background: '#F9FAFB',
            padding: '16px',
            borderRadius: 8,
            marginBottom: 16,
          }}>
            <Form.Item name="expiry_days" style={{ marginBottom: 16 }}>
              <Radio.Group size="large" style={{ width: '100%' }}>
                <Row gutter={[8, 8]}>
                  <Col span={4}>
                    <Radio.Button value={1} style={{ width: '100%', textAlign: 'center' }}>1日</Radio.Button>
                  </Col>
                  <Col span={4}>
                    <Radio.Button value={5} style={{ width: '100%', textAlign: 'center' }}>5日</Radio.Button>
                  </Col>
                  <Col span={4}>
                    <Radio.Button value={10} style={{ width: '100%', textAlign: 'center' }}>10日</Radio.Button>
                  </Col>
                  <Col span={4}>
                    <Radio.Button value={20} style={{ width: '100%', textAlign: 'center' }}>20日</Radio.Button>
                  </Col>
                  <Col span={4}>
                    <Radio.Button value={60} style={{ width: '100%', textAlign: 'center' }}>60日</Radio.Button>
                  </Col>
                  <Col span={4}>
                    <Radio.Button value={-1} style={{ width: '100%', textAlign: 'center' }}>永久</Radio.Button>
                  </Col>
                </Row>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) =>
                prevValues.expiry_days !== currentValues.expiry_days
              }
            >
              {({ getFieldValue }) => {
                const days = getFieldValue('expiry_days');

                // 永久有效
                if (days === -1) {
                  return (
                    <div style={{
                      background: '#FFFFFF',
                      padding: '12px',
                      borderRadius: 6,
                      textAlign: 'center',
                      border: '1px solid #E5E7EB',
                    }}>
                      <Text style={{ fontSize: 14, color: '#10B981', fontWeight: 600 }}>
                        永久有效，策略不会自动过期
                      </Text>
                    </div>
                  );
                }

                // 有期限
                const expiryDays = days || 20;
                const expiryDate = dayjs().add(expiryDays, 'day');
                return (
                  <div style={{
                    background: '#FFFFFF',
                    padding: '12px',
                    borderRadius: 6,
                    textAlign: 'center',
                    border: '1px solid #E5E7EB',
                  }}>
                    <Text style={{ fontSize: 14, color: '#111827' }}>
                      {expiryDate.format('YYYY年MM月DD日')}({expiryDays}个交易日) 收盘前
                    </Text>
                  </div>
                );
              }}
            </Form.Item>
          </div>

          <Divider style={{ margin: '24px 0' }} />

          {/* ========== 高级设置 ========== */}
          <Collapse
            ghost
            expandIconPosition="end"
            style={{
              background: '#F9FAFB',
              borderRadius: 8,
              marginBottom: 24,
            }}
          >
            <Panel
              header={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Text strong style={{ fontSize: 15, color: '#111827' }}>高级设置</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>保底价触发、延迟确认等</Text>
                </div>
              }
              key="advanced"
            >
              <Space direction="vertical" style={{ width: '100%' }} size={16}>
                <Row align="middle" justify="space-between">
                  <Col>
                    <Text style={{ fontSize: 14, color: '#111827' }}>监控时段</Text>
                  </Col>
                  <Col>
                    <Form.Item name="enable_monitor_period" valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Row align="middle" justify="space-between">
                  <Col>
                    <Text style={{ fontSize: 14, color: '#111827' }}>偏差控制</Text>
                  </Col>
                  <Col>
                    <Form.Item name="enable_deviation_control" valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Row align="middle" justify="space-between">
                  <Col>
                    <Text style={{ fontSize: 14, color: '#111827' }}>报价优化</Text>
                  </Col>
                  <Col>
                    <Form.Item name="enable_price_optimization" valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Row align="middle" justify="space-between">
                  <Col>
                    <Text style={{ fontSize: 14, color: '#111827' }}>延迟确认</Text>
                  </Col>
                  <Col>
                    <Form.Item name="enable_delay_confirm" valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Row align="middle" justify="space-between">
                  <Col>
                    <Text style={{ fontSize: 14, color: '#111827' }}>保底价触发</Text>
                  </Col>
                  <Col>
                    <Form.Item name="enable_floor_price" valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Row align="middle" justify="space-between">
                  <Col>
                    <Text style={{ fontSize: 14, color: '#111827' }}>清仓设置</Text>
                  </Col>
                  <Col>
                    <Form.Item name="enable_auto_close" valuePropName="checked" style={{ marginBottom: 0 }}>
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>
              </Space>

              <div style={{
                background: '#FEF3C7',
                padding: '8px 12px',
                borderRadius: 4,
                marginTop: 16,
              }}>
                <Text style={{ fontSize: 12, color: '#92400E' }}>
                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                  条件单采用交易所提供的Level-1行情，刷新频率: 3秒/次
                </Text>
              </div>
            </Panel>
          </Collapse>

          {/* ========== 底部操作按钮 ========== */}
          <Button
            type="primary"
            size="large"
            block
            onClick={handleSave}
            loading={saving}
            style={{
              background: 'linear-gradient(135deg, #F43F5E 0%, #E11D48 100%)',
              borderColor: 'transparent',
              height: 50,
              fontSize: 16,
              fontWeight: 600,
              borderRadius: 8,
              boxShadow: '0 4px 12px rgba(244, 63, 94, 0.3)',
            }}
          >
            提交创建
          </Button>
        </Form>
      </Card>
    </div>
  );
};

export default GridConfig;
