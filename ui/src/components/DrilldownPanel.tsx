/**
 * Entity drilldown panel with metrics and narrative.
 */

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { getEntityDrilldown } from '../api/client';
import LoadingSpinner from './LoadingSpinner';
import type { EntityDrilldownResponse } from '../api/types';

interface DrilldownPanelProps {
  entityId: string | undefined;
  windowStart?: string;
}

export default function DrilldownPanel({ entityId, windowStart }: DrilldownPanelProps) {
  const [drilldown, setDrilldown] = useState<EntityDrilldownResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!entityId) {
      setLoading(false);
      return;
    }
    loadDrilldown();
  }, [entityId, windowStart]);

  const loadDrilldown = async () => {
    if (!entityId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await getEntityDrilldown(entityId, windowStart);
      setDrilldown(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load entity data');
      console.error('Failed to load drilldown:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyMetrics = () => {
    if (!drilldown) return;

    const { entity, metrics } = drilldown;
    const text = `${entity.name} (${entity.type})
Fame: ${metrics.x_fame.toFixed(1)}
Love: ${metrics.y_love.toFixed(1)}
Momentum: ${metrics.momentum.toFixed(1)}
Polarization: ${metrics.polarization.toFixed(1)}%
Confidence: ${metrics.confidence.toFixed(1)}%
Mentions: ${metrics.mentions_explicit + (metrics.mentions_implicit || 0)}`;

    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  if (!entityId) {
    return <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>No entity selected</div>;
  }

  if (loading) {
    return (
      <div style={{ padding: '40px' }}>
        <LoadingSpinner text="Loading entity data..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#d32f2f' }}>
        Error: {error}
      </div>
    );
  }

  if (!drilldown) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>No data available</div>;
  }

  const { entity, metrics, narrative, series } = drilldown;

  // Prepare sparkline data
  const sparklineData = series.slice(-7).map((point: any) => ({
    date: new Date(point.window_start).toLocaleDateString(),
    fame: point.x_fame,
    love: point.y_love,
    attention: point.momentum || 0,
  }));

  return (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '24px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      {/* Entity Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '24px' }}>{entity.name}</h2>
          <button
            onClick={handleCopyMetrics}
            style={{
              padding: '8px 16px',
              border: copied ? '2px solid #4caf50' : '2px solid #1976d2',
              backgroundColor: copied ? '#e8f5e9' : 'white',
              color: copied ? '#4caf50' : '#1976d2',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.3s ease'
            }}
            title="Copy metrics to clipboard"
          >
            {copied ? '✓ Copied!' : '📋 Copy Metrics'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: '12px', fontSize: '14px', color: '#666' }}>
          <span style={{
            backgroundColor: '#e3f2fd',
            color: '#1976d2',
            padding: '4px 10px',
            borderRadius: '12px',
            fontSize: '13px',
            fontWeight: 'bold'
          }}>
            {entity.type}
          </span>
          {entity.is_pinned && (
            <span style={{
              backgroundColor: '#fff3e0',
              color: '#f57c00',
              padding: '4px 10px',
              borderRadius: '12px',
              fontSize: '13px',
              fontWeight: 'bold'
            }}>
              📌 PINNED
            </span>
          )}
        </div>
      </div>

      {/* Current Coordinates */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>Current Position</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          <div style={{
            backgroundColor: '#f5f5f5',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #e0e0e0'
          }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Fame</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#1976d2' }}>
              {metrics.x_fame.toFixed(1)}
            </div>
            {metrics.delta_1d?.x_fame && (
              <div style={{ fontSize: '12px', color: metrics.delta_1d.x_fame >= 0 ? '#4caf50' : '#f44336' }}>
                {metrics.delta_1d.x_fame >= 0 ? '↑' : '↓'} {Math.abs(metrics.delta_1d.x_fame).toFixed(1)} (1d)
              </div>
            )}
          </div>
          <div style={{
            backgroundColor: '#f5f5f5',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #e0e0e0'
          }}>
            <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Love</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#e91e63' }}>
              {metrics.y_love.toFixed(1)}
            </div>
            {metrics.delta_1d?.y_love && (
              <div style={{ fontSize: '12px', color: metrics.delta_1d.y_love >= 0 ? '#4caf50' : '#f44336' }}>
                {metrics.delta_1d.y_love >= 0 ? '↑' : '↓'} {Math.abs(metrics.delta_1d.y_love).toFixed(1)} (1d)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Additional Metrics */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>Metrics</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '14px' }}>
          <div>
            <div style={{ color: '#666', marginBottom: '4px' }}>Momentum</div>
            <div style={{ fontWeight: 'bold' }}>{metrics.momentum.toFixed(1)}</div>
          </div>
          <div>
            <div style={{ color: '#666', marginBottom: '4px' }}>Polarization</div>
            <div style={{ fontWeight: 'bold' }}>{metrics.polarization.toFixed(1)}%</div>
          </div>
          <div>
            <div style={{ color: '#666', marginBottom: '4px' }}>Confidence</div>
            <div style={{ fontWeight: 'bold' }}>{metrics.confidence.toFixed(1)}%</div>
          </div>
          <div>
            <div style={{ color: '#666', marginBottom: '4px' }}>Mentions</div>
            <div style={{ fontWeight: 'bold' }}>{metrics.mentions_explicit + (metrics.mentions_implicit || 0)}</div>
          </div>
        </div>
      </div>

      {/* 7-Day Sparklines */}
      {sparklineData.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>7-Day Trends</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={sparklineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="fame" stroke="#1976d2" strokeWidth={2} name="Fame" />
              <Line type="monotone" dataKey="love" stroke="#e91e63" strokeWidth={2} name="Love" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Narrative */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>Why It Moved</h3>
        <div style={{
          backgroundColor: '#f9f9f9',
          padding: '16px',
          borderRadius: '8px',
          border: '1px solid #e0e0e0'
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 'bold' }}>{narrative.moved_because}</p>
          {narrative.bullets && narrative.bullets.length > 0 && (
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
              {narrative.bullets.map((bullet, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{bullet}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
