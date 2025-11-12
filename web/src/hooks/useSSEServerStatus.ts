import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { request } from '@/utils/request';

export type SSEServerStatus = 'online' | 'offline' | 'unknown';

interface SSEStatusResponse {
  active_connections?: number;
  success?: boolean;
}

export const useSSEServerStatus = (intervalMs = 15000) => {
  const [status, setStatus] = useState<SSEServerStatus>('unknown');
  const [activeConnections, setActiveConnections] = useState<number>(0);
  const [lastError, setLastError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchStatus = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const response = await request.get<SSEStatusResponse>('/api/sse/status');
      if (response && response.success !== false) {
        setStatus('online');
        setActiveConnections(response.active_connections ?? 0);
        setLastError(null);
      } else {
        setStatus('offline');
        setLastError('SSE 服务未响应');
      }
    } catch (error: any) {
      const errMsg = error?.message || '无法连接到 SSE 服务';
      setStatus('offline');
      setLastError(errMsg);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, intervalMs);
    return () => clearInterval(timer);
  }, [fetchStatus, intervalMs]);

  const refresh = useCallback(async () => {
    if (isRefreshing) return;
    await fetchStatus();
    if (status === 'offline') {
      message.warning('正在重新检查 SSE 服务状态...');
    }
  }, [fetchStatus, isRefreshing, status]);

  return {
    status,
    activeConnections,
    lastError,
    isRefreshing,
    refresh,
  };
};

export default useSSEServerStatus;
