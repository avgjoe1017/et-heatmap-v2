/**
 * Main heatmap page with scatter plot visualization.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Heatmap from '../components/Heatmap';
import Filters from '../components/Filters';
import TimelineScrubber from '../components/TimelineScrubber';
import LoadingSpinner from '../components/LoadingSpinner';
import SearchBar from '../components/SearchBar';
import TopMovers from '../components/TopMovers';
import ShareButton from '../components/ShareButton';
import { getSnapshot, getLatestRun } from '../api/client';
import { exportToCSV, exportToJSON, generateFilename } from '../utils/export';
import { useURLState } from '../hooks/useURLState';
import { useMediaQuery, breakpoints } from '../hooks/useMediaQuery';
import type { HeatmapSnapshotResponse, EntityPoint } from '../api/types';

export default function HeatmapPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { state: urlState, updateState, clearFilters } = useURLState();
  const isMobile = useMediaQuery(breakpoints.mobile);
  const isTablet = useMediaQuery(breakpoints.tablet);

  const [snapshot, setSnapshot] = useState<HeatmapSnapshotResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [colorMode, setColorMode] = useState<'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE'>(
    urlState.colorMode || 'MOMENTUM'
  );
  const [filters, setFilters] = useState<{
    types?: string[];
    onlyMovers?: boolean;
    onlyPolarizing?: boolean;
    onlyHighConfidence?: boolean;
    pinnedOnly?: boolean;
  }>({
    types: urlState.types,
    onlyMovers: urlState.onlyMovers,
    onlyPolarizing: urlState.onlyPolarizing,
    onlyHighConfidence: urlState.onlyHighConfidence,
    pinnedOnly: urlState.pinnedOnly,
  });

  // Load snapshot data from URL or default
  useEffect(() => {
    loadSnapshot(urlState.windowStart);
  }, []);

  // Sync URL state with component state on mount
  useEffect(() => {
    if (urlState.colorMode && urlState.colorMode !== colorMode) {
      setColorMode(urlState.colorMode);
    }
  }, []);

  // Navigate to entity if URL has entityId
  useEffect(() => {
    if (urlState.entityId && snapshot) {
      const entityExists = snapshot.points.some(p => p.entity_id === urlState.entityId);
      if (entityExists) {
        navigate(`/entity/${urlState.entityId}`, { replace: true });
      }
    }
  }, [urlState.entityId, snapshot, navigate]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') {
        return;
      }

      // ESC to reload data
      if (e.key === 'Escape') {
        loadSnapshot();
      }
      // R to reset filters
      if (e.key === 'r' || e.key === 'R') {
        handleResetFilters();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  const loadSnapshot = async (windowStart?: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSnapshot(windowStart);
      setSnapshot(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load heatmap data');
      console.error('Failed to load snapshot:', err);
    } finally {
      setLoading(false);
    }
  };

  // Apply filters to points
  const filteredPoints = snapshot?.points.filter((point: EntityPoint) => {
    if (filters.types && filters.types.length > 0) {
      if (!filters.types.includes(point.type)) {
        return false;
      }
    }

    if (filters.pinnedOnly && !point.is_pinned) {
      return false;
    }

    if (filters.onlyMovers && Math.abs(point.momentum || 0) < 5) {
      return false;
    }

    if (filters.onlyPolarizing && (point.polarization || 0) < 30) {
      return false;
    }

    if (filters.onlyHighConfidence && (point.confidence || 0) < 70) {
      return false;
    }

    return true;
  }) || [];

  const handleDotClick = (entityId: string) => {
    navigate(`/entity/${entityId}`);
  };

  const handleColorModeChange = (mode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE') => {
    setColorMode(mode);
    updateState({ colorMode: mode });
  };

  const handleWindowChange = (windowStart: string) => {
    loadSnapshot(windowStart);
    updateState({ windowStart });
  };

  const handleFiltersChange = (newFilters: {
    types?: string[];
    onlyMovers?: boolean;
    onlyPolarizing?: boolean;
    onlyHighConfidence?: boolean;
    pinnedOnly?: boolean;
  }) => {
    setFilters(newFilters);
    updateState({
      types: newFilters.types,
      onlyMovers: newFilters.onlyMovers,
      onlyPolarizing: newFilters.onlyPolarizing,
      onlyHighConfidence: newFilters.onlyHighConfidence,
      pinnedOnly: newFilters.pinnedOnly,
    });
  };

  const handleResetFilters = () => {
    setFilters({});
    clearFilters();
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <LoadingSpinner size="large" text="Loading heatmap data..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--error)' }}>
        <p>Error: {error}</p>
        <button 
          onClick={() => loadSnapshot()}
          style={{
            padding: '8px 16px',
            border: '2px solid var(--error)',
            backgroundColor: 'var(--bg-primary)',
            color: 'var(--error)',
            borderRadius: '8px',
            cursor: 'pointer',
            marginTop: '12px'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        <p>No data available. Run the pipeline to generate heatmap data.</p>
      </div>
    );
  }

  // Calculate time ago for timestamp
  const getTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  };

  return (
    <div style={{ 
      padding: '20px', 
      maxWidth: '1400px', 
      margin: '0 auto',
      backgroundColor: 'var(--bg-primary)',
      color: 'var(--text-primary)',
      minHeight: '100vh'
    }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '10px',
          flexWrap: 'wrap',
          gap: '12px'
        }}>
          <h1 style={{ margin: 0, fontSize: isMobile ? '24px' : '32px' }}>Entertainment Feelings Heatmap</h1>
          <div style={{
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            flexWrap: 'wrap'
          }}>
            {snapshot.window && (
              <div style={{
                backgroundColor: 'var(--success-light)',
                padding: '6px 12px',
                borderRadius: '20px',
                fontSize: isMobile ? '11px' : '13px',
                color: 'var(--success)',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                🕒 Updated {getTimeAgo(snapshot.window.end)}
              </div>
            )}
            <ShareButton
              state={{
                colorMode,
                types: filters.types,
                onlyMovers: filters.onlyMovers,
                onlyPolarizing: filters.onlyPolarizing,
                onlyHighConfidence: filters.onlyHighConfidence,
                pinnedOnly: filters.pinnedOnly,
                windowStart: snapshot.window?.start,
              }}
            />
          </div>
        </div>
        {snapshot.window && (
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: '0' }}>
            Window: {new Date(snapshot.window.start).toLocaleString()} - {new Date(snapshot.window.end).toLocaleString()}
          </p>
        )}
        <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', margin: '4px 0 0 0' }}>
          Press <kbd style={{ padding: '2px 6px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '11px', color: 'var(--text-primary)' }}>ESC</kbd> to refresh •
          Press <kbd style={{ padding: '2px 6px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '11px', color: 'var(--text-primary)' }}>R</kbd> to reset filters •
          Press <kbd style={{ padding: '2px 6px', backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', fontSize: '11px', color: 'var(--text-primary)' }}>/</kbd> to search
        </p>
      </div>

      {/* Search Bar */}
      <div style={{ marginBottom: '20px', width: '100%' }}>
        <SearchBar
          entities={snapshot?.points.map(p => ({
            entity_id: p.entity_id,
            name: p.name,
            type: p.type
          }))}
          placeholder="Search entities... (press / to focus)"
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <Filters
          onFiltersChange={handleFiltersChange}
          colorMode={colorMode}
          onColorModeChange={handleColorModeChange}
          initialFilters={{
            types: filters.types,
            onlyMovers: filters.onlyMovers,
            onlyPolarizing: filters.onlyPolarizing,
            onlyHighConfidence: filters.onlyHighConfidence,
            pinnedOnly: filters.pinnedOnly,
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <TimelineScrubber
          currentWindow={snapshot.window?.start}
          onWindowChange={handleWindowChange}
        />
      </div>

      {/* Responsive layout: Heatmap + Analytics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : isTablet ? '1fr 280px' : '1fr 320px',
        gap: isMobile ? '16px' : '20px',
        alignItems: 'start'
      }}>
        {/* Main Heatmap */}
        <div style={{
          backgroundColor: 'var(--bg-primary)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: isMobile ? '12px' : '20px',
          boxShadow: '0 2px 4px var(--shadow)',
          overflow: 'auto', // Allow scrolling on mobile
          transition: 'background-color 0.3s ease, border-color 0.3s ease'
        }}>
        {filteredPoints.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <p>No entities match the current filters.</p>
          </div>
        ) : (
          <>
            <div style={{
              display: 'flex',
              flexDirection: isMobile ? 'column' : 'row',
              justifyContent: 'space-between',
              alignItems: isMobile ? 'flex-start' : 'center',
              gap: isMobile ? '12px' : '0',
              marginBottom: '10px'
            }}>
              <div style={{ fontSize: isMobile ? '12px' : '14px', color: 'var(--text-secondary)' }}>
                Showing {filteredPoints.length} of {snapshot.points.length} entities
              </div>
              <div style={{
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap',
                width: isMobile ? '100%' : 'auto'
              }}>
                <button
                  onClick={() => exportToCSV(
                    filteredPoints,
                    generateFilename('heatmap', 'csv', snapshot.window?.start)
                  )}
                  style={{
                    padding: isMobile ? '8px 12px' : '6px 14px',
                    border: '2px solid var(--success)',
                    backgroundColor: 'var(--bg-primary)',
                    color: 'var(--success)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: isMobile ? '12px' : '13px',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    flex: isMobile ? '1' : 'auto',
                    transition: 'all 0.3s ease'
                  }}
                  title="Export visible entities to CSV"
                >
                  📄 {isMobile ? 'CSV' : 'Export CSV'}
                </button>
                <button
                  onClick={() => exportToJSON(
                    filteredPoints,
                    generateFilename('heatmap', 'json', snapshot.window?.start)
                  )}
                  style={{
                    padding: isMobile ? '8px 12px' : '6px 14px',
                    border: '2px solid var(--info)',
                    backgroundColor: 'var(--bg-primary)',
                    color: 'var(--info)',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: isMobile ? '12px' : '13px',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    flex: isMobile ? '1' : 'auto',
                    transition: 'all 0.3s ease'
                  }}
                  title="Export visible entities to JSON"
                >
                  💾 {isMobile ? 'JSON' : 'Export JSON'}
                </button>
              </div>
            </div>
            <Heatmap
              data={filteredPoints}
              colorMode={colorMode}
              onDotClick={handleDotClick}
            />
          </>
        )}
        </div>

        {/* Analytics Sidebar */}
        <div style={{ order: isMobile ? 2 : 1 }}>
          <TopMovers entities={filteredPoints.length > 0 ? filteredPoints : (snapshot?.points || [])} limit={10} />
        </div>
      </div>
    </div>
  );
}
