import { useEffect, useRef, useState } from 'react';
import { Card, Input, Select, Button, List, Tag, Spin } from 'antd';
import { getLogs, getLogFiles } from '@/api/logs';

const { Search } = Input;

const COLORS: Record<string, string> = {
  DEBUG: 'default',
  INFO: 'blue',
  WARNING: 'gold',
  ERROR: 'red',
  CRITICAL: 'magenta',
};

export default function LogsPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any[]>([]);
  const [keyword, setKeyword] = useState('');
  const [level, setLevel] = useState<string | undefined>();
  const [logFile, setLogFile] = useState<string | undefined>();
  const [files, setFiles] = useState<any[]>([]);

  const boxRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    loadFiles();
    loadLogs();
  }, []);

  async function loadFiles() {
    const res = await getLogFiles();
    if (res.success) {
      setFiles(res.data.files);
    }
  }

  async function loadLogs() {
    setLoading(true);
    const res = await getLogs({
      keyword,
      level,
      log_file: logFile,
      page: 1,
      page_size: 200,
    });

    if (res.success) {
      setData(res.data.logs);
      scrollBottom();
    }
    setLoading(false);
  }

  function scrollBottom() {
    if (boxRef.current) {
      boxRef.current.scrollTop = boxRef.current.scrollHeight;
    }
  }

  return (
    <Card
      title="📜 日志查看"
      style={{ margin: 24 }}
      extra={
        <Button onClick={loadLogs} disabled={loading}>
          刷新
        </Button>
      }
    >
      {/* 搜索区域 */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Search
          placeholder="关键词搜索"
          onSearch={loadLogs}
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          style={{ width: 240 }}
        />

        <Select
          allowClear
          placeholder="日志级别"
          value={level}
          onChange={(v) => setLevel(v)}
          style={{ width: 160 }}
        >
          <Select.Option value="DEBUG">DEBUG</Select.Option>
          <Select.Option value="INFO">INFO</Select.Option>
          <Select.Option value="WARNING">WARNING</Select.Option>
          <Select.Option value="ERROR">ERROR</Select.Option>
          <Select.Option value="CRITICAL">CRITICAL</Select.Option>
        </Select>

        <Select
          allowClear
          placeholder="日志文件"
          value={logFile}
          onChange={(v) => setLogFile(v)}
          style={{ width: 200 }}
        >
          {files.map((f: any) => (
            <Select.Option key={f.name} value={f.name}>
              {f.name}
            </Select.Option>
          ))}
        </Select>

        <Button type="primary" onClick={loadLogs} disabled={loading}>
          查询
        </Button>
      </div>

      {/* 日志展示区域 */}
      <div
        ref={boxRef}
        style={{
          height: '70vh',
          overflow: 'auto',
          background: '#1e1e1e',
          color: '#ddd',
          borderRadius: 4,
          padding: 12,
          fontFamily: 'monospace',
          fontSize: 13,
        }}
      >
        {loading ? (
          <Spin />
        ) : (
          <List
            dataSource={data}
            renderItem={(log: any) => (
              <List.Item style={{ background: 'transparent' }}>
                <Tag color={COLORS[log.level]}>{log.level}</Tag>
                {log.timestamp} —
                <span style={{ marginLeft: 8 }}>{log.message}</span>
              </List.Item>
            )}
          />
        )}
      </div>
    </Card>
  );
}