/**
 * Resolve queue page for managing unresolved mentions.
 */

import { useState, useEffect } from 'react';
import { getResolveQueue, resolveMention } from '../api/client';

interface ResolveQueueItem {
  surface: string;
  count: number;
  impact: number;
  examples: Array<{
    source: string;
    context: string;
    candidates: Array<{ entity_id?: string; score?: number }>;
  }>;
}

export default function ResolveQueuePage() {
  const [queue, setQueue] = useState<{ items: ResolveQueueItem[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolving, setResolving] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getResolveQueue();
      setQueue(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load resolve queue');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (surface: string, entityId: string, alias?: string) => {
    if (!queue) return;

    setResolving(prev => new Set(prev).add(surface));
    try {
      // Find the unresolved_id from the queue items
      // Note: This is simplified - in production, you'd want to track unresolved_id properly
      await resolveMention(surface, entityId, alias);
      
      // Reload queue after successful resolution
      await loadQueue();
    } catch (err: any) {
      alert(`Failed to resolve: ${err.message || 'Unknown error'}`);
    } finally {
      setResolving(prev => {
        const next = new Set(prev);
        next.delete(surface);
        return next;
      });
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        <h1>Resolve Queue</h1>
        <p>Loading unresolved mentions...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <h1>Resolve Queue</h1>
        <div style={{ color: 'red', padding: '10px', backgroundColor: '#fee', borderRadius: '4px' }}>
          Error: {error}
        </div>
        <button onClick={loadQueue} style={{ marginTop: '10px', padding: '8px 16px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (!queue || queue.items.length === 0) {
    return (
      <div style={{ padding: '20px' }}>
        <h1>Resolve Queue</h1>
        <p>No unresolved mentions found. Great job! 🎉</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>Resolve Queue</h1>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Found {queue.items.length} unresolved mention{queue.items.length !== 1 ? 's' : ''}. 
        Resolve them to improve entity recognition accuracy.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {queue.items.map((item, idx) => (
          <div
            key={idx}
            style={{
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '16px',
              backgroundColor: 'white'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px' }}>"{item.surface}"</h3>
                <div style={{ fontSize: '14px', color: '#666', marginTop: '4px' }}>
                  Appeared {item.count} time{item.count !== 1 ? 's' : ''} • Impact: {item.impact.toFixed(1)}
                </div>
              </div>
            </div>

            {item.examples.length > 0 && (
              <div style={{ marginBottom: '12px', fontSize: '14px' }}>
                <strong>Context:</strong>
                <div style={{
                  marginTop: '8px',
                  padding: '12px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '4px',
                  fontStyle: 'italic',
                  color: '#555'
                }}>
                  {item.examples[0].context}
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#999' }}>
                  Source: {item.examples[0].source}
                </div>
              </div>
            )}

            {item.examples[0]?.candidates && item.examples[0].candidates.length > 0 && (
              <div>
                <strong style={{ fontSize: '14px' }}>Suggested entities:</strong>
                <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {item.examples[0].candidates.map((candidate, cIdx) => (
                    <button
                      key={cIdx}
                      onClick={() => candidate.entity_id && handleResolve(item.surface, candidate.entity_id)}
                      disabled={resolving.has(item.surface)}
                      style={{
                        padding: '6px 12px',
                        border: '1px solid #007bff',
                        backgroundColor: resolving.has(item.surface) ? '#f0f0f0' : 'white',
                        color: '#007bff',
                        borderRadius: '4px',
                        cursor: resolving.has(item.surface) ? 'not-allowed' : 'pointer',
                        fontSize: '13px'
                      }}
                    >
                      {candidate.entity_id || 'Unknown'} {candidate.score && `(${(candidate.score * 100).toFixed(0)}%)`}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {(!item.examples[0]?.candidates || item.examples[0].candidates.length === 0) && (
              <div style={{ fontSize: '14px', color: '#999', fontStyle: 'italic' }}>
                No candidate entities found. Manual review needed.
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
