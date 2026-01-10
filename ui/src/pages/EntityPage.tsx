/**
 * Entity drilldown page.
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DrilldownPanel from '../components/DrilldownPanel';
import DriversList from '../components/DriversList';
import ThemesList from '../components/ThemesList';
import { getEntityDrilldown } from '../api/client';
import type { EntityDrilldownResponse } from '../api/types';

export default function EntityPage() {
  const { entityId } = useParams();
  const navigate = useNavigate();
  const [drilldown, setDrilldown] = useState<EntityDrilldownResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (entityId) {
      loadDrilldown();
    }
  }, [entityId]);

  const loadDrilldown = async () => {
    if (!entityId) return;
    
    try {
      setLoading(true);
      const data = await getEntityDrilldown(entityId);
      setDrilldown(data);
    } catch (err: any) {
      console.error('Failed to load drilldown:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!entityId) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>No entity ID provided</p>
        <button onClick={() => navigate('/')}>Back to Heatmap</button>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>Loading entity data...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={() => navigate('/')}
          style={{
            padding: '8px 16px',
            border: '1px solid #ccc',
            backgroundColor: 'white',
            borderRadius: '4px',
            cursor: 'pointer',
            marginBottom: '16px'
          }}
        >
          ← Back to Heatmap
        </button>
      </div>

      {drilldown && (
        <>
          <DrilldownPanel entityId={entityId} />
          <div style={{ marginTop: '24px' }}>
            <DriversList entityId={entityId} drilldown={drilldown} />
          </div>
          <div style={{ marginTop: '24px' }}>
            <ThemesList entityId={entityId} drilldown={drilldown} />
          </div>
        </>
      )}
    </div>
  );
}
