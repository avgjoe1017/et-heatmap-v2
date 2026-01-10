/**
 * Top Movers analytics panel - shows entities with highest momentum.
 */

import { useNavigate } from 'react-router-dom';
import type { EntityPoint } from '../api/types';

interface TopMoversProps {
  entities: EntityPoint[];
  limit?: number;
}

export default function TopMovers({ entities, limit = 10 }: TopMoversProps) {
  const navigate = useNavigate();

  // Calculate top movers (highest absolute momentum)
  const topMovers = [...entities]
    .filter(e => !e.is_dormant)
    .sort((a, b) => Math.abs(b.momentum) - Math.abs(a.momentum))
    .slice(0, limit);

  // Calculate most polarizing
  const mostPolarizing = [...entities]
    .filter(e => !e.is_dormant)
    .sort((a, b) => b.polarization - a.polarization)
    .slice(0, 5);

  // Calculate highest confidence
  const highestConfidence = [...entities]
    .filter(e => !e.is_dormant && e.confidence >= 70)
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 5);

  const getMomentumColor = (momentum: number) => {
    if (momentum > 0) return '#4caf50';
    if (momentum < 0) return '#f44336';
    return '#999';
  };

  const getMomentumIcon = (momentum: number) => {
    if (momentum > 0) return '📈';
    if (momentum < 0) return '📉';
    return '➡️';
  };

  const getTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      PERSON: '#1976d2',
      SHOW: '#e91e63',
      FILM: '#9c27b0',
      FRANCHISE: '#ff9800',
      STREAMER: '#4caf50',
      BRAND: '#f44336',
      CHARACTER: '#00bcd4',
      COUPLE: '#ff5722'
    };
    return colors[type] || '#999';
  };

  return (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid #e0e0e0',
      borderRadius: '12px',
      padding: '20px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h2 style={{ margin: '0 0 16px 0', fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        🔥 Top Movers
      </h2>

      {/* Top Movers List */}
      <div style={{ marginBottom: '24px' }}>
        {topMovers.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#999', fontSize: '14px' }}>
            No significant movement detected
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {topMovers.map((entity, index) => (
              <div
                key={entity.entity_id}
                onClick={() => navigate(`/entity/${entity.entity_id}`)}
                style={{
                  padding: '12px',
                  backgroundColor: index < 3 ? '#f9f9f9' : 'transparent',
                  border: index < 3 ? '2px solid #e0e0e0' : '1px solid #f0f0f0',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'grid',
                  gridTemplateColumns: '24px 1fr auto auto',
                  gap: '12px',
                  alignItems: 'center'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f0f0f0';
                  e.currentTarget.style.borderColor = '#1976d2';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = index < 3 ? '#f9f9f9' : 'transparent';
                  e.currentTarget.style.borderColor = index < 3 ? '#e0e0e0' : '#f0f0f0';
                }}
              >
                <div style={{
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: index < 3 ? '#1976d2' : '#999'
                }}>
                  #{index + 1}
                </div>

                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
                    {entity.name}
                  </div>
                  <div style={{
                    display: 'inline-block',
                    backgroundColor: getTypeColor(entity.type) + '20',
                    color: getTypeColor(entity.type),
                    padding: '2px 8px',
                    borderRadius: '10px',
                    fontSize: '11px',
                    fontWeight: 'bold'
                  }}>
                    {entity.type}
                  </div>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: 'bold',
                  fontSize: '16px',
                  color: getMomentumColor(entity.momentum)
                }}>
                  {getMomentumIcon(entity.momentum)}
                  {Math.abs(entity.momentum).toFixed(1)}
                </div>

                <div style={{ fontSize: '18px', color: '#ccc' }}>→</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '12px',
        paddingTop: '16px',
        borderTop: '1px solid #e0e0e0'
      }}>
        {/* Most Polarizing */}
        <div>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', fontWeight: 'bold' }}>
            ⚡ Most Polarizing
          </div>
          {mostPolarizing.slice(0, 3).map(entity => (
            <div
              key={entity.entity_id}
              onClick={() => navigate(`/entity/${entity.entity_id}`)}
              style={{
                fontSize: '12px',
                marginBottom: '4px',
                cursor: 'pointer',
                color: '#9c27b0',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
              onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
            >
              {entity.name} ({entity.polarization.toFixed(0)}%)
            </div>
          ))}
        </div>

        {/* Highest Confidence */}
        <div>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px', fontWeight: 'bold' }}>
            ✓ Highest Confidence
          </div>
          {highestConfidence.slice(0, 3).map(entity => (
            <div
              key={entity.entity_id}
              onClick={() => navigate(`/entity/${entity.entity_id}`)}
              style={{
                fontSize: '12px',
                marginBottom: '4px',
                cursor: 'pointer',
                color: '#4caf50',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
              onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
            >
              {entity.name} ({entity.confidence.toFixed(0)}%)
            </div>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid #e0e0e0',
        display: 'flex',
        justifyContent: 'space-around',
        fontSize: '12px',
        color: '#666'
      }}>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '20px', color: '#4caf50' }}>
            {entities.filter(e => e.momentum > 5).length}
          </div>
          <div>Rising</div>
        </div>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '20px', color: '#f44336' }}>
            {entities.filter(e => e.momentum < -5).length}
          </div>
          <div>Falling</div>
        </div>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '20px', color: '#ff9800' }}>
            {entities.filter(e => e.polarization > 50).length}
          </div>
          <div>Polarizing</div>
        </div>
      </div>
    </div>
  );
}
