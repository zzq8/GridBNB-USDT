/**
 * AI策略配置页面
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Select,
} from 'antd';
import {
  SaveOutlined,
  QuestionCircleOutlined,
  LeftOutlined,
  RobotOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const AIConfig: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);

  // 保存配置
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);

      console.log('AI策略配置:', values);

      // TODO: 调用API保存配置
      // await saveAIConfig(values);

      message.success('AI策略配置保存成功');
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

  // 提示词模板
  const promptTemplates = [
    {
      label: '稳健型',
      value: '你是一位经验丰富的加密货币交易专家。请基于当前市场数据，使用保守稳健的策略进行交易决策。重点关注风险控制，避免激进操作。',
    },
    {
      label: '激进型',
      value: '你是一位追求高收益的加密货币交易专家。请基于当前市场数据，积极捕捉交易机会。在风险可控的前提下，追求利润最大化。',
    },
    {
      label: '趋势跟随',
      value: '你是一位擅长趋势分析的交易专家。请识别市场主要趋势，顺势而为。在上升趋势中持有仓位，在下降趋势中保持观望。',
    },
    {
      label: '震荡策略',
      value: '你是一位擅长震荡市场的交易专家。在价格震荡区间内，通过高抛低吸获取收益。注意识别震荡区间的上下边界。',
    },
  ];

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
          🤖 AI策略配置
        </Title>
        <Text type="secondary" style={{ fontSize: 14 }}>
          配置AI智能交易策略，通过自然语言提示词定制您的交易逻辑
        </Text>
      </div>

      {/* 提示信息 */}
      <Alert
        message="AI策略说明"
        description="AI策略利用大语言模型分析市场数据，根据您设定的提示词做出交易决策。提示词越详细，AI的决策越准确。建议从模板开始，然后根据实际情况调整。"
        type="info"
        showIcon
        icon={<RobotOutlined />}
        closable
        style={{
          marginBottom: 24,
          background: '#F5F3FF',
          border: '1px solid #8B5CF6',
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
                enabled: true,
                symbol: 'BNBUSDT',
                investment_amount: 1000,
                ai_model: 'gpt-4',
                analysis_interval: 60,
                max_position_size: 50,
                stop_loss_enabled: true,
                stop_loss_rate: 5,
                prompt_template: '',
              }}
            >
              {/* 基础配置 */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #8B5CF6',
              }}>
                基础配置
              </div>

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

              <Form.Item
                name="symbol"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    交易对
                    <Tooltip title="选择要交易的币种对">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
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

              <Form.Item
                name="investment_amount"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    投资金额 (USDT)
                    <Tooltip title="分配给该策略的总投资金额">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
                rules={[{ required: true, message: '请输入投资金额' }]}
              >
                <InputNumber
                  placeholder="请输入投资金额"
                  min={10}
                  max={1000000}
                  step={100}
                  size="large"
                  style={{ width: '100%', fontSize: 14 }}
                  formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={(value) => value!.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* AI模型配置 */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #8B5CF6',
              }}>
                AI模型配置
              </div>

              <Form.Item
                name="ai_model"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    AI模型
                    <Tooltip title="选择用于分析的AI模型">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
                rules={[{ required: true, message: '请选择AI模型' }]}
              >
                <Select size="large" style={{ fontSize: 14 }}>
                  <Option value="gpt-4">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, fontSize: 14, color: '#111827', lineHeight: 1.5 }}>
                          GPT-4
                        </div>
                        <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5, marginTop: 2 }}>
                          最强大的模型，适合复杂市场分析
                        </div>
                      </div>
                    </div>
                  </Option>
                  <Option value="gpt-3.5-turbo">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, fontSize: 14, color: '#111827', lineHeight: 1.5 }}>
                          GPT-3.5 Turbo
                        </div>
                        <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5, marginTop: 2 }}>
                          速度快，成本低，适合频繁交易
                        </div>
                      </div>
                    </div>
                  </Option>
                  <Option value="claude-3">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 500, fontSize: 14, color: '#111827', lineHeight: 1.5 }}>
                          Claude 3
                        </div>
                        <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5, marginTop: 2 }}>
                          Anthropic模型，注重安全性和准确性
                        </div>
                      </div>
                    </div>
                  </Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="analysis_interval"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    分析间隔 (秒)
                    <Tooltip title="AI分析市场的时间间隔，间隔越短，反应越快">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
                rules={[{ required: true, message: '请输入分析间隔' }]}
              >
                <InputNumber
                  placeholder="建议 30-300 秒"
                  min={10}
                  max={3600}
                  step={10}
                  size="large"
                  style={{ width: '100%', fontSize: 14 }}
                  formatter={(value) => `${value}秒`}
                  parser={(value) => value!.replace('秒', '')}
                />
              </Form.Item>

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* 提示词配置 */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #8B5CF6',
              }}>
                提示词配置
              </div>

              <Form.Item
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    选择模板 (可选)
                    <Tooltip title="选择预设模板快速开始，或自定义提示词">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
              >
                <Select
                  placeholder="选择一个提示词模板"
                  size="large"
                  style={{ fontSize: 14 }}
                  onChange={(value) => {
                    const template = promptTemplates.find(t => t.value === value);
                    if (template) {
                      form.setFieldValue('prompt_template', template.value);
                    }
                  }}
                  allowClear
                >
                  {promptTemplates.map((template) => (
                    <Option key={template.label} value={template.value}>
                      <span style={{ fontSize: 14, color: '#111827' }}>{template.label}</span>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="prompt_template"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    AI提示词
                    <Tooltip title="详细描述您希望AI如何进行交易决策">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
                rules={[{ required: true, message: '请输入AI提示词' }]}
              >
                <TextArea
                  placeholder="请输入详细的提示词，描述您的交易策略、风险偏好、市场判断标准等..."
                  rows={8}
                  style={{ fontSize: 14, lineHeight: 1.6 }}
                  showCount
                  maxLength={2000}
                />
              </Form.Item>

              <Alert
                message="提示词编写建议"
                description={
                  <ul style={{ marginBottom: 0, paddingLeft: 20, fontSize: 13 }}>
                    <li>清晰描述交易目标和风险偏好</li>
                    <li>说明买入和卖出的判断标准</li>
                    <li>指定仓位管理规则</li>
                    <li>包含止损和止盈策略</li>
                    <li>考虑市场趋势和技术指标</li>
                  </ul>
                }
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Divider style={{ margin: '32px 0', borderColor: '#E5E7EB' }} />

              {/* 风险控制 */}
              <div style={{
                fontSize: 15,
                fontWeight: 600,
                color: '#111827',
                marginBottom: 20,
                paddingBottom: 12,
                borderBottom: '2px solid #EF4444',
              }}>
                风险控制
              </div>

              <Form.Item
                name="max_position_size"
                label={
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                    最大仓位比例 (%)
                    <Tooltip title="单次交易最多使用的资金比例">
                      <QuestionCircleOutlined style={{ marginLeft: 4, color: '#9CA3AF' }} />
                    </Tooltip>
                  </span>
                }
                rules={[{ required: true, message: '请输入最大仓位比例' }]}
              >
                <InputNumber
                  placeholder="建议不超过 50%"
                  min={1}
                  max={100}
                  step={5}
                  size="large"
                  style={{ width: '100%', fontSize: 14 }}
                  formatter={(value) => `${value}%`}
                  parser={(value) => value!.replace('%', '')}
                />
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
                    <Form.Item
                      name="stop_loss_rate"
                      label={
                        <span style={{ fontSize: 14, fontWeight: 500, color: '#111827' }}>
                          止损比例 (%)
                        </span>
                      }
                      rules={[{ required: true, message: '请输入止损比例' }]}
                    >
                      <InputNumber
                        placeholder="达到该亏损比例后停止策略"
                        min={1}
                        max={50}
                        step={1}
                        size="large"
                        style={{ width: '100%', fontSize: 14 }}
                        formatter={(value) => `${value}%`}
                        parser={(value) => value!.replace('%', '')}
                      />
                    </Form.Item>
                  ) : null
                }
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
                      background: '#8B5CF6',
                      borderColor: '#8B5CF6',
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

        {/* 右侧：配置说明 */}
        <Col span={8}>
          <Card
            title="AI策略指南"
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
                <Text strong style={{ fontSize: 14, color: '#111827' }}>模型选择建议</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#6B7280', marginBottom: 0 }}>
                  • GPT-4: 复杂策略，深度分析<br />
                  • GPT-3.5: 快速决策，高频交易<br />
                  • Claude 3: 风险控制，稳健策略
                </Paragraph>
              </div>

              <Divider style={{ margin: 0 }} />

              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>分析间隔设置</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#6B7280', marginBottom: 0 }}>
                  • 短期交易: 30-60秒<br />
                  • 中期持仓: 120-300秒<br />
                  • 长期投资: 300秒以上
                </Paragraph>
              </div>

              <Divider style={{ margin: 0 }} />

              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>提示词要点</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#6B7280', marginBottom: 0 }}>
                  1. 明确交易目标和风格<br />
                  2. 说明技术指标偏好<br />
                  3. 设定仓位管理规则<br />
                  4. 包含风险控制措施<br />
                  5. 考虑市场环境因素
                </Paragraph>
              </div>

              <Divider style={{ margin: 0 }} />

              <div>
                <Text strong style={{ fontSize: 14, color: '#111827' }}>风险提示</Text>
                <Paragraph style={{ marginTop: 8, fontSize: 13, color: '#EF4444', marginBottom: 0 }}>
                  ⚠️ AI决策存在不确定性<br />
                  ⚠️ 建议小额测试后再扩大规模<br />
                  ⚠️ 定期检查AI决策质量<br />
                  ⚠️ 必须设置止损保护
                </Paragraph>
              </div>
            </Space>
          </Card>

          <Card
            title="配置预览"
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
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>交易对:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>{values.symbol || '--'}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>投资金额:</Text>
                      <Text strong style={{ color: '#8B5CF6', fontSize: 13 }}>
                        ${values.investment_amount || 0}
                      </Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>AI模型:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>{values.ai_model || '--'}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6B7280', fontSize: 13 }}>分析间隔:</Text>
                      <Text strong style={{ color: '#111827', fontSize: 13 }}>{values.analysis_interval || 0}秒</Text>
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

export default AIConfig;
