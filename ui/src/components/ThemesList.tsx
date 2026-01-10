/**
 * Themes list for entity drilldown.
 */

import type { EntityDrilldownResponse } from '../api/types';

interface ThemesListProps {
  entityId: string;
  drilldown: EntityDrilldownResponse | null;
}

export default function ThemesList({ entityId, drilldown }: ThemesListProps) {
  if (!drilldown || !drilldown.themes || drilldown.themes.length === 0) {
    return (
      <div style={{
        backgroundColor: 'white',
        border: '1px solid #ddd',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px' }}>Themes</h3>
        <p style={{ color: '#999', margin: '0' }}>No themes identified for this entity.</p>
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
      <h3 style={{ margin: '0 0 16px 0', fontSize: '18px' }}>Conversation Themes</h3>
      <p style={{ fontSize: '14px', color: '#666', margin: '0 0 16px 0' }}>
        Topic clusters identified in mentions:
      </p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {drilldown.themes.map((theme) => {
          const sentimentMix = theme.sentiment_mix || { pos: 0, neg: 0, neu: 1 };
          const dominantSentiment = sentimentMix.pos > sentimentMix.neg ? 'positive' : 
                                   sentimentMix.neg > sentimentMix.pos ? 'negative' : 'neutral';
          
          return (
            <div
              key={theme.theme_id}
              style={{
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                padding: '16px',
                backgroundColor: '#fafafa'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                <h4 style={{ margin: '0', fontSize: '16px', fontWeight: 'bold' }}>
                  {theme.label}
                </h4>
                <span style={{
                  fontSize: '12px',
                  color: '#666',
                  backgroundColor: '#f0f0f0',
                  padding: '2px 8px',
                  borderRadius: '12px'
                }}>
                  {theme.volume} mentions
                </span>
              </div>
              
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '6px' }}>Keywords:</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {theme.keywords.slice(0, 5).map((keyword, idx) => (
                    <span
                      key={idx}
                      style={{
                        fontSize: '12px',
                        backgroundColor: '#e3f2fd',
                        color: '#1976d2',
                        padding: '4px 8px',
                        borderRadius: '12px'
                      }}
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
              
              {sentimentMix && (
                <div>
                  <div style={{ fontSize: '12px', color: '#666', marginBottom: '6px' }}>Sentiment:</div>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                    <span style={{ color: '#4caf50' }}>
                      ↑ {(sentimentMix.pos * 100).toFixed(0)}% pos
                    </span>
                    <span style={{ color: '#666' }}>
                      • {(sentimentMix.neu * 100).toFixed(0)}% neu
                    </span>
                    <span style={{ color: '#f44336' }}>
                      ↓ {(sentimentMix.neg * 100).toFixed(0)}% neg
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
