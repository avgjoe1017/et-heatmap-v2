/**
 * Pipeline runs page - shows run status and history.
 */

import { useState, useEffect } from 'react';
import { getLatestRun, listRuns } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';

interface Run {
  run_id: string;
  status: 'running' | 'success' | 'failed' | 'partial';
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  metrics?: {
    total_sources?: number;
    total_entities?: number;
    total_mentions?: number;
    sources_ingested?: {
      reddit?: number;
      youtube?: number;
      gdelt?: number;
    };
  };
}

export default function RunsPage() {
  const [latestRun, setLatestRun] = useState<Run | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRuns();
    // Poll for updates every 30 seconds
    const interval = setInterval(loadRuns, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadRuns = async () => {
    try {
      setError(null);
      const [latest, history] = await Promise.all([
        getLatestRun().catch(() => null),
        listRuns(20).catch(() => ({ runs: [] }))
      ]);

      setLatestRun(latest);
      setRuns(history.runs || history || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load runs');
      console.error('Failed to load runs:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#2196f3';
      case 'success': return '#4caf50';
      case 'failed': return '#f44336';
      case 'partial': return '#ff9800';
      default: return '#999';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '⏳';
      case 'success': return '✅';
      case 'failed': return '❌';
      case 'partial': return '⚠️';
      default: return '❓';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  if (loading && !latestRun) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <LoadingSpinner size="large" text="Loading pipeline runs..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: '0 0 8px 0' }}>Pipeline Runs</h1>
        <p style={{ color: '#666', fontSize: '14px', margin: 0 }}>
          Monitor pipeline execution status and history
        </p>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#ffebee',
          border: '1px solid #f44336',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '20px',
          color: '#c62828'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Latest Run Status Card */}
      {latestRun && (
        <div style={{
          backgroundColor: 'white',
          border: '2px solid #e0e0e0',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '32px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
            <div>
              <h2 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>Latest Run</h2>
              <p style={{ margin: 0, color: '#666', fontSize: '13px' }}>
                {latestRun.completed_at ? (
                  <>Completed {getTimeAgo(latestRun.completed_at)}</>
                ) : (
                  <>Started {getTimeAgo(latestRun.started_at)}</>
                )}
              </p>
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: getStatusColor(latestRun.status) + '20',
              border: `2px solid ${getStatusColor(latestRun.status)}`,
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '14px',
              fontWeight: 'bold',
              color: getStatusColor(latestRun.status)
            }}>
              {getStatusIcon(latestRun.status)} {latestRun.status.toUpperCase()}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{
              backgroundColor: '#f5f5f5',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Duration</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {formatDuration(latestRun.duration_seconds)}
              </div>
            </div>

            {latestRun.metrics?.total_entities !== undefined && (
              <div style={{
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Entities</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1976d2' }}>
                  {latestRun.metrics.total_entities.toLocaleString()}
                </div>
              </div>
            )}

            {latestRun.metrics?.total_mentions !== undefined && (
              <div style={{
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Mentions</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e91e63' }}>
                  {latestRun.metrics.total_mentions.toLocaleString()}
                </div>
              </div>
            )}

            {latestRun.metrics?.total_sources !== undefined && (
              <div style={{
                backgroundColor: '#f5f5f5',
                padding: '16px',
                borderRadius: '8px',
                border: '1px solid #e0e0e0'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>Sources</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#4caf50' }}>
                  {latestRun.metrics.total_sources.toLocaleString()}
                </div>
              </div>
            )}
          </div>

          {latestRun.metrics?.sources_ingested && (
            <div style={{
              backgroundColor: '#f9f9f9',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid #e0e0e0'
            }}>
              <div style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '12px', color: '#666' }}>
                Sources Ingested:
              </div>
              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                {latestRun.metrics.sources_ingested.reddit !== undefined && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      backgroundColor: '#ff4500',
                      color: 'white',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}>
                      Reddit
                    </span>
                    <span style={{ fontWeight: 'bold' }}>
                      {latestRun.metrics.sources_ingested.reddit.toLocaleString()}
                    </span>
                  </div>
                )}
                {latestRun.metrics.sources_ingested.youtube !== undefined && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      backgroundColor: '#ff0000',
                      color: 'white',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}>
                      YouTube
                    </span>
                    <span style={{ fontWeight: 'bold' }}>
                      {latestRun.metrics.sources_ingested.youtube.toLocaleString()}
                    </span>
                  </div>
                )}
                {latestRun.metrics.sources_ingested.gdelt !== undefined && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      backgroundColor: '#1976d2',
                      color: 'white',
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 'bold'
                    }}>
                      GDELT
                    </span>
                    <span style={{ fontWeight: 'bold' }}>
                      {latestRun.metrics.sources_ingested.gdelt.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {latestRun.error_message && (
            <div style={{
              backgroundColor: '#ffebee',
              border: '1px solid #f44336',
              borderRadius: '8px',
              padding: '12px',
              marginTop: '16px',
              fontSize: '13px',
              color: '#c62828'
            }}>
              <strong>Error:</strong> {latestRun.error_message}
            </div>
          )}

          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e0e0e0', fontSize: '12px', color: '#999' }}>
            <div><strong>Run ID:</strong> {latestRun.run_id}</div>
            <div><strong>Started:</strong> {formatDate(latestRun.started_at)}</div>
            {latestRun.completed_at && (
              <div><strong>Completed:</strong> {formatDate(latestRun.completed_at)}</div>
            )}
          </div>
        </div>
      )}

      {/* Run History */}
      <div>
        <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Run History</h2>

        {runs.length === 0 ? (
          <div style={{
            backgroundColor: 'white',
            border: '1px solid #e0e0e0',
            borderRadius: '8px',
            padding: '40px',
            textAlign: 'center',
            color: '#999'
          }}>
            <p style={{ margin: 0 }}>No pipeline runs found. Run the pipeline to see history here.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {runs.map((run) => (
              <div
                key={run.run_id}
                style={{
                  backgroundColor: 'white',
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  padding: '16px',
                  display: 'grid',
                  gridTemplateColumns: '120px 1fr auto auto',
                  gap: '16px',
                  alignItems: 'center'
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13px',
                  fontWeight: 'bold',
                  color: getStatusColor(run.status)
                }}>
                  {getStatusIcon(run.status)} {run.status.toUpperCase()}
                </div>

                <div style={{ fontSize: '13px' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                    {formatDate(run.started_at)}
                  </div>
                  <div style={{ color: '#666', fontSize: '12px' }}>
                    {run.metrics?.total_entities !== undefined && (
                      <span>{run.metrics.total_entities.toLocaleString()} entities • </span>
                    )}
                    {run.metrics?.total_mentions !== undefined && (
                      <span>{run.metrics.total_mentions.toLocaleString()} mentions</span>
                    )}
                  </div>
                </div>

                <div style={{ fontSize: '13px', color: '#666' }}>
                  {formatDuration(run.duration_seconds)}
                </div>

                <div style={{ fontSize: '12px', color: '#999' }}>
                  {getTimeAgo(run.started_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Auto-refresh indicator */}
      <div style={{
        marginTop: '24px',
        textAlign: 'center',
        fontSize: '12px',
        color: '#999'
      }}>
        ⟳ Auto-refreshing every 30 seconds
      </div>
    </div>
  );
}
