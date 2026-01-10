/**
 * Top drivers list for entity drilldown.
 */

import type { EntityDrilldownResponse } from '../api/types';

interface DriversListProps {
  entityId: string;
  drilldown: EntityDrilldownResponse | null;
}

export default function DriversList({ entityId, drilldown }: DriversListProps) {
  if (!drilldown || !drilldown.drivers || drilldown.drivers.length === 0) {
    return (
      <div style={{
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>Top Drivers</h3>
        <p style={{ color: '#999', margin: '0' }}>No drivers available for this entity.</p>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: 'white',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '24px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: '18px' }}>Top Drivers</h3>
      <p style={{ fontSize: '14px', color: '#666', margin: '0 0 16px 0' }}>
        Sources that drove this entity's metrics:
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {drilldown.drivers.map((driver) => (
          <div
            key={driver.rank}
            style={{
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '16px',
              backgroundColor: '#fafafa'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{
                    display: 'inline-block',
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    backgroundColor: '#1976d2',
                    color: 'white',
                    textAlign: 'center',
                    lineHeight: '24px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {driver.rank}
                  </span>
                  <span style={{
                    fontSize: '12px',
                    color: '#666',
                    backgroundColor: '#e3f2fd',
                    padding: '2px 8px',
                    borderRadius: '12px'
                  }}>
                    {driver.source}
                  </span>
                  <span style={{ fontSize: '12px', color: '#999' }}>
                    Impact: {driver.impact_score.toFixed(1)}
                  </span>
                </div>
                <div style={{ fontWeight: 'bold', marginBottom: '4px', fontSize: '16px' }}>
                  {driver.title || '(No title)'}
                </div>
                {driver.reason && (
                  <div style={{ fontSize: '14px', color: '#666', fontStyle: 'italic', marginTop: '4px' }}>
                    {driver.reason}
                  </div>
                )}
              </div>
            </div>
            
            {driver.url && (
              <a
                href={driver.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontSize: '14px',
                  color: '#1976d2',
                  textDecoration: 'none',
                  display: 'inline-block',
                  marginTop: '8px'
                }}
              >
                View source →
              </a>
            )}
            
            {driver.published_at && (
              <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                {new Date(driver.published_at).toLocaleString()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
