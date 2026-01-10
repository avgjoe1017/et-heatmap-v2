/**
 * Export utility functions for CSV and JSON downloads.
 */

import type { EntityPoint } from '../api/types';

export function exportToCSV(data: EntityPoint[], filename: string = 'heatmap-data.csv') {
  // Create CSV header
  const headers = [
    'Entity ID',
    'Name',
    'Type',
    'Fame',
    'Love',
    'Momentum',
    'Polarization',
    'Confidence',
    'Attention',
    'Baseline Fame',
    'Mentions Explicit',
    'Mentions Implicit',
    'Sources Distinct',
    'Is Pinned',
    'Is Dormant'
  ];

  // Create CSV rows
  const rows = data.map(entity => [
    entity.entity_id,
    `"${entity.name}"`, // Quote name in case it contains commas
    entity.type,
    entity.x_fame.toFixed(2),
    entity.y_love.toFixed(2),
    entity.momentum.toFixed(2),
    entity.polarization.toFixed(2),
    entity.confidence.toFixed(2),
    (entity.attention || 0).toFixed(2),
    (entity.baseline_fame || 0).toFixed(2),
    entity.mentions_explicit || 0,
    entity.mentions_implicit || 0,
    entity.sources_distinct || 0,
    entity.is_pinned ? 'Yes' : 'No',
    entity.is_dormant ? 'Yes' : 'No'
  ]);

  // Combine headers and rows
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');

  // Create download
  downloadFile(csvContent, filename, 'text/csv');
}

export function exportToJSON(data: EntityPoint[], filename: string = 'heatmap-data.json', pretty: boolean = true) {
  const jsonContent = pretty
    ? JSON.stringify(data, null, 2)
    : JSON.stringify(data);

  downloadFile(jsonContent, filename, 'application/json');
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function generateFilename(prefix: string, format: 'csv' | 'json', windowStart?: string): string {
  const date = windowStart ? new Date(windowStart) : new Date();
  const dateStr = date.toISOString().split('T')[0]; // YYYY-MM-DD
  return `${prefix}-${dateStr}.${format}`;
}
