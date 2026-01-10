/**
 * Interactive scatter plot heatmap visualization.
 */

import { useMemo, useState, useEffect } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { EntityPoint } from '../api/types';

interface HeatmapProps {
  data: EntityPoint[];
  colorMode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE';
  onDotClick: (entityId: string) => void;
}

// Color scale helpers
function getColorForMomentum(value: number): string {
  // Momentum: negative = cool (blue), positive = hot (red), zero = neutral (gray)
  const normalized = Math.max(-1, Math.min(1, value / 50)); // Normalize to -1..1
  if (normalized > 0) {
    // Hot: red gradient
    const intensity = Math.floor(255 * (1 - normalized));
    return `rgb(255, ${intensity}, ${intensity})`;
  } else if (normalized < 0) {
    // Cool: blue gradient
    const intensity = Math.floor(255 * (1 + normalized));
    return `rgb(${intensity}, ${intensity}, 255)`;
  }
  return '#888'; // Neutral gray
}

function getColorForPolarization(value: number): string {
  // Polarization: 0 = gray (low), 100 = red (high)
  const intensity = Math.floor(255 * (value / 100));
  return `rgb(255, ${255 - intensity}, ${255 - intensity})`;
}

function getColorForConfidence(value: number): string {
  // Confidence: 0 = red (low), 100 = green (high)
  const intensity = Math.floor(255 * (value / 100));
  return `rgb(${255 - intensity}, 255, ${255 - intensity})`;
}

function getColor(dataPoint: EntityPoint, colorMode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE'): string {
  switch (colorMode) {
    case 'MOMENTUM':
      return getColorForMomentum(dataPoint.momentum);
    case 'POLARIZATION':
      return getColorForPolarization(dataPoint.polarization);
    case 'CONFIDENCE':
      return getColorForConfidence(dataPoint.confidence);
    default:
      return '#888';
  }
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length > 0) {
    const data = payload[0].payload as EntityPoint;
    const isTrending = Math.abs(data.momentum) >= 10;
    const sources = data.sources_distinct || 0;

    return (
      <div style={{
        backgroundColor: 'var(--bg-primary)',
        border: '2px solid var(--primary)',
        padding: '12px',
        borderRadius: '8px',
        boxShadow: '0 4px 12px var(--shadow-strong)',
        minWidth: '220px',
        transition: 'background-color 0.3s ease, border-color 0.3s ease'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <p style={{ fontWeight: 'bold', margin: 0, fontSize: '15px', flex: 1 }}>{data.name}</p>
          {isTrending && <span style={{ fontSize: '18px' }}>🔥</span>}
        </div>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <span style={{
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary)',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '11px',
            fontWeight: 'bold'
          }}>
            {data.type}
          </span>
          {data.is_pinned && (
            <span style={{
              backgroundColor: 'var(--warning-light)',
              color: 'var(--warning)',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>
              📌 PINNED
            </span>
          )}
        </div>

        <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '8px', marginTop: '8px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Fame</div>
              <div style={{ fontWeight: 'bold', color: 'var(--primary)' }}>{data.x_fame.toFixed(1)}</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Love</div>
              <div style={{ fontWeight: 'bold', color: '#e91e63' }}>{data.y_love.toFixed(1)}</div>
            </div>
            <div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>Momentum</div>
              <div style={{
                fontWeight: 'bold',
                color: data.momentum > 0 ? 'var(--success)' : data.momentum < 0 ? 'var(--error)' : 'var(--text-secondary)'
              }}>
                {data.momentum > 0 ? '↑' : data.momentum < 0 ? '↓' : '→'} {Math.abs(data.momentum).toFixed(1)}
              </div>
            </div>
            <div>
              <div style={{ color: '#666', fontSize: '11px' }}>Polarization</div>
              <div style={{ fontWeight: 'bold' }}>{data.polarization.toFixed(1)}%</div>
            </div>
            <div>
              <div style={{ color: '#666', fontSize: '11px' }}>Confidence</div>
              <div style={{ fontWeight: 'bold' }}>{data.confidence.toFixed(1)}%</div>
            </div>
            <div>
              <div style={{ color: '#666', fontSize: '11px' }}>Mentions</div>
              <div style={{ fontWeight: 'bold' }}>{(data.mentions_explicit || 0) + (data.mentions_implicit || 0)}</div>
            </div>
          </div>
        </div>

        {sources > 0 && (
          <div style={{
            marginTop: '8px',
            paddingTop: '8px',
            borderTop: '1px solid var(--border-color)',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            📰 {sources} source{sources !== 1 ? 's' : ''}
          </div>
        )}

        {data.is_dormant && (
          <p style={{ margin: '8px 0 0 0', fontSize: '11px', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
            ⏸ Dormant
          </p>
        )}

        <p style={{ margin: '8px 0 0 0', fontSize: '10px', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
          Click to view details
        </p>
      </div>
    );
  }
  return null;
};

export default function Heatmap({ data, colorMode, onDotClick }: HeatmapProps) {
  // Prepare data for Recharts (needs x, y format)
  const scatterData = useMemo(() => {
    return data.map(point => ({
      ...point,
      x: point.x_fame,
      y: point.y_love,
    }));
  }, [data]);

  // Responsive height based on viewport
  const getHeight = () => {
    if (typeof window === 'undefined') return 600;
    const isMobile = window.innerWidth <= 768;
    const isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
    if (isMobile) return Math.min(window.innerHeight * 0.5, 400);
    if (isTablet) return 500;
    return 600;
  };

  const [height, setHeight] = useState(getHeight());

  useEffect(() => {
    const handleResize = () => {
      setHeight(getHeight());
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Quadrant lines (at 50, 50 for fame/love)
  const quadrantLines = [
    { x1: 50, y1: 0, x2: 50, y2: 100 }, // Vertical line at fame=50
    { x1: 0, y1: 50, x2: 100, y2: 50 }, // Horizontal line at love=50
  ];

  return (
    <div style={{ width: '100%', height: `${height}px`, position: 'relative', minHeight: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 40, left: 40 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
          
          {/* Quadrant background lines */}
          <XAxis
            type="number"
            dataKey="x"
            domain={[0, 100]}
            name="Fame"
            label={{ value: 'Fame', position: 'insideBottom', offset: -10 }}
            tick={{ fontSize: 12, fill: 'var(--chart-axis)' }}
          />
          <YAxis
            type="number"
            dataKey="y"
            domain={[0, 100]}
            name="Love"
            label={{ value: 'Love', angle: -90, position: 'insideLeft' }}
            tick={{ fontSize: 12, fill: 'var(--chart-axis)' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          {/* Scatter points */}
          <Scatter
            name="Entities"
            data={scatterData}
            fill="#888"
            onClick={(data: any) => {
              if (data?.payload?.entity_id) {
                onDotClick(data.payload.entity_id);
              }
            }}
            shape={(props: any) => {
              const { cx, cy, payload } = props;
              const point = payload as EntityPoint;
              const color = getColor(point, colorMode);
              const isTrending = Math.abs(point.momentum) >= 10;
              const size = isTrending ? 8 : 6;

              return (
                <g>
                  <circle
                    cx={cx}
                    cy={cy}
                    r={size}
                    fill={color}
                    stroke={point.is_pinned ? '#000' : 'none'}
                    strokeWidth={point.is_pinned ? 2 : 0}
                    style={{ cursor: 'pointer' }}
                  />
                  {isTrending && (
                    <text
                      x={cx + 10}
                      y={cy - 8}
                      style={{
                        fontSize: '14px',
                        pointerEvents: 'none',
                        userSelect: 'none'
                      }}
                    >
                      🔥
                    </text>
                  )}
                </g>
              );
            }}
          />
        </ScatterChart>
      </ResponsiveContainer>
      
      {/* Quadrant labels */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        fontSize: '11px',
        color: 'var(--text-secondary)',
        fontWeight: 'bold'
      }}>
        High Fame, High Love
      </div>
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        fontSize: '11px',
        color: '#666',
        fontWeight: 'bold'
      }}>
        High Fame, Low Love
      </div>
      <div style={{
        position: 'absolute',
        bottom: '30px',
        left: '10px',
        fontSize: '11px',
        color: '#666',
        fontWeight: 'bold'
      }}>
        Low Fame, High Love
      </div>
      <div style={{
        position: 'absolute',
        bottom: '30px',
        right: '10px',
        fontSize: '11px',
        color: '#666',
        fontWeight: 'bold'
      }}>
        Low Fame, Low Love
      </div>
    </div>
  );
}
