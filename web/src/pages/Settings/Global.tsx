/**
 * 全局设置（趋势风控）
 * 仅展示关键的趋势检测相关参数，便于快速调整。
 */

import React, { useEffect, useState } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Switch,
  Button,
  Row,
  Col,
  Typography,
  message,
  Tag,
  Empty,
} from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { getConfigs, batchUpdateConfigs, reloadConfigs } from '@/api/config';
import type { Configuration } from '@/types';

const { Title } = Typography;

const TREND_KEYS = [
  'TREND_DETECTION_INTERVAL',
  'TREND_STRONG_THRESHOLD',
  'TREND_ADX_PERIOD',
  'TREND_EMA_LONG',
  'TREND_EMA_SHORT',
  'ENABLE_TREND_DETECTION',
];

const KEY_ORDER = [
  'TREND_DETECTION_INTERVAL',
  'TREND_STRONG_THRESHOLD',
  'TREND_ADX_PERIOD',
  'TREND_EMA_LONG',
  'TREND_EMA_SHORT',
  'ENABLE_TREND_DETECTION',
];

const GlobalSettings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [items, setItems] = useState<Configuration[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const resp = await getConfigs({ page: 1, page_size: 1000 });
      const all: Configuration[] = resp.items || [];

      const selected = all.filter((c) => TREND_KEYS.includes(c.config_key));

      const values: Record<number, any> = {};
      selected.forEach((item) => {
        if (item.data_type === 'boolean') {
          values[item.id] = String(item.config_value).toLowerCase() === 'true';
        } else if (item.data_type === 'number') {
          const num = Number(item.config_value);
          values[item.id] = Number.isNaN(num) ? undefined : num;
        } else {
          values[item.id] = item.config_value;
        }
      });
      form.setFieldsValue(values);

      setItems(
        selected.sort(
          (a, b) => KEY_ORDER.indexOf(a.config_key) - KEY_ORDER.indexOf(b.config_key)
        )
      );
    } catch (error) {
      message.error('参数加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onSave = async () => {
    try {
      const values = await form.validateFields();
      const updates = items.map((item) => {
        const value = values[item.id];
        if (typeof value === 'boolean') {
          return { id: item.id, config_value: value ? 'true' : 'false' };
        }
        return { id: item.id, config_value: value?.toString() ?? '' };
      });
      setSaving(true);
      const res = await batchUpdateConfigs({ updates });
      message.success(`已更新 ${res.updated} 项`);
      await load();
    } catch (error: any) {
      if (error?.errorFields) {
        message.error('请完善必要参数');
      } else {
        message.error('保存失败');
      }
    } finally {
      setSaving(false);
    }
  };

  const onReload = async () => {
    try {
      await reloadConfigs();
      message.success('后端配置已重载');
    } catch {
      message.error('重载失败');
    }
  };

  const renderControl = (item: Configuration) => {
    if (item.data_type === 'boolean') {
      return <Switch />;
    }
    return <InputNumber style={{ width: '100%' }} />;
  };

  return (
    <div>
      <div
        style={{
          marginBottom: 16,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          趋势风控参数
        </Title>
        <div style={{ display: 'flex', gap: 12 }}>
          <Button icon={<ReloadOutlined />} onClick={onReload} disabled={loading}>
            重载
          </Button>
          <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={onSave}>
            保存
          </Button>
        </div>
      </div>

      <Form form={form} layout="vertical" disabled={loading}>
        {items.length === 0 ? (
          <Empty description="暂无配置" />
        ) : (
          <Row gutter={[16, 16]}>
            {items.map((item) => (
              <Col span={12} key={item.id}>
                <Card hoverable bodyStyle={{ padding: 20 }} style={{ height: '100%' }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 15, fontWeight: 600 }}>{item.display_name}</div>
                      {item.description && (
                        <div style={{ color: '#6B7280', fontSize: 12, marginTop: 4 }}>
                          {item.description}
                        </div>
                      )}
                    </div>
                    <Tag color="orange">risk</Tag>
                  </div>
                  <div style={{ marginTop: 16 }}>
                    <Form.Item name={item.id} style={{ marginBottom: 0 }}>
                      {renderControl(item)}
                    </Form.Item>
                  </div>
                  <div
                    style={{
                      marginTop: 16,
                      display: 'flex',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Tag color={item.is_required ? 'red' : 'default'}>
                      {item.is_required ? '必填' : '可选'}
                    </Tag>
                    <Tag color={item.requires_restart ? 'volcano' : 'green'}>
                      {item.requires_restart ? '需重启生效' : '即时生效'}
                    </Tag>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Form>
    </div>
  );
};

export default GlobalSettings;
