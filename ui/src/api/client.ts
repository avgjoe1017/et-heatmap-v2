/**
 * API client for backend requests.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getSnapshot(windowStart?: string) {
  const response = await api.get('/snapshots', {
    params: { window_start: windowStart },
  });
  return response.data;
}

export async function getEntityDrilldown(entityId: string, windowStart?: string) {
  const response = await api.get(`/entities/${entityId}`, {
    params: { window_start: windowStart },
  });
  return response.data;
}

export async function getResolveQueue(windowStart?: string, limit = 100) {
  const response = await api.get('/resolve-queue', {
    params: { window_start: windowStart, limit },
  });
  return response.data;
}

export async function getLatestRun() {
  const response = await api.get('/runs/latest');
  return response.data;
}

export default api;
