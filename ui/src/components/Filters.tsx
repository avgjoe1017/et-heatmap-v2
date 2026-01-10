/**
 * Heatmap filters component.
 */

import { useState, useEffect } from 'react';

interface FiltersProps {
  onFiltersChange: (filters: {
    types?: string[];
    onlyMovers?: boolean;
    onlyPolarizing?: boolean;
    onlyHighConfidence?: boolean;
    pinnedOnly?: boolean;
  }) => void;
  colorMode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE';
  onColorModeChange: (mode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE') => void;
  initialFilters?: {
    types?: string[];
    onlyMovers?: boolean;
    onlyPolarizing?: boolean;
    onlyHighConfidence?: boolean;
    pinnedOnly?: boolean;
  };
}

const ENTITY_TYPES = ['PERSON', 'SHOW', 'FILM', 'FRANCHISE', 'STREAMER', 'BRAND', 'CHARACTER', 'COUPLE'];

export default function Filters({ onFiltersChange, colorMode, onColorModeChange, initialFilters }: FiltersProps) {
  const [selectedTypes, setSelectedTypes] = useState<string[]>(initialFilters?.types || []);
  const [onlyMovers, setOnlyMovers] = useState(initialFilters?.onlyMovers || false);
  const [onlyPolarizing, setOnlyPolarizing] = useState(initialFilters?.onlyPolarizing || false);
  const [onlyHighConfidence, setOnlyHighConfidence] = useState(initialFilters?.onlyHighConfidence || false);
  const [pinnedOnly, setPinnedOnly] = useState(initialFilters?.pinnedOnly || false);

  // Sync with initialFilters when they change (e.g., from URL)
  useEffect(() => {
    if (initialFilters) {
      setSelectedTypes(initialFilters.types || []);
      setOnlyMovers(initialFilters.onlyMovers || false);
      setOnlyPolarizing(initialFilters.onlyPolarizing || false);
      setOnlyHighConfidence(initialFilters.onlyHighConfidence || false);
      setPinnedOnly(initialFilters.pinnedOnly || false);
    }
  }, [initialFilters?.types?.join(','), initialFilters?.onlyMovers, initialFilters?.onlyPolarizing, initialFilters?.onlyHighConfidence, initialFilters?.pinnedOnly]);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Notify parent of filter changes
  useEffect(() => {
    onFiltersChange({
      types: selectedTypes.length > 0 ? selectedTypes : undefined,
      onlyMovers,
      onlyPolarizing,
      onlyHighConfidence,
      pinnedOnly: pinnedOnly || undefined,
    });
  }, [selectedTypes, onlyMovers, onlyPolarizing, onlyHighConfidence, pinnedOnly, onFiltersChange]);

  const handleTypeToggle = (type: string) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const handleResetFilters = () => {
    setSelectedTypes([]);
    setOnlyMovers(false);
    setOnlyPolarizing(false);
    setOnlyHighConfidence(false);
    setPinnedOnly(false);
  };

  const hasActiveFilters =
    selectedTypes.length > 0 ||
    onlyMovers ||
    onlyPolarizing ||
    onlyHighConfidence ||
    pinnedOnly;

  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--border-color)',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '20px',
      transition: 'background-color 0.3s ease, border-color 0.3s ease'
    }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', alignItems: 'flex-start' }}>
        {/* Color Mode Selector */}
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)' }}>
            Color Mode:
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            {(['MOMENTUM', 'POLARIZATION', 'CONFIDENCE'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => onColorModeChange(mode)}
                style={{
                  padding: '6px 12px',
                  border: `1px solid ${colorMode === mode ? 'var(--primary)' : 'var(--border-color)'}`,
                  backgroundColor: colorMode === mode ? 'var(--primary)' : 'var(--bg-primary)',
                  color: colorMode === mode ? 'white' : 'var(--text-primary)',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: colorMode === mode ? 'bold' : 'normal',
                  transition: 'all 0.3s ease'
                }}
              >
                {mode.charAt(0) + mode.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Entity Type Filters */}
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)' }}>
            Entity Types:
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {ENTITY_TYPES.map(type => (
              <button
                key={type}
                onClick={() => handleTypeToggle(type)}
                style={{
                  padding: '4px 10px',
                  border: `1px solid ${selectedTypes.includes(type) ? 'var(--primary)' : 'var(--border-color)'}`,
                  backgroundColor: selectedTypes.includes(type) ? 'var(--primary-light)' : 'var(--bg-primary)',
                  color: selectedTypes.includes(type) ? 'var(--primary)' : 'var(--text-primary)',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  transition: 'all 0.3s ease'
                }}
              >
                {type}
              </button>
            ))}
            {selectedTypes.length > 0 && (
              <button
                onClick={() => setSelectedTypes([])}
                style={{
                  padding: '4px 10px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'var(--bg-primary)',
                  color: 'var(--text-secondary)',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  transition: 'all 0.3s ease'
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Quick Filters */}
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)' }}>
              Quick Filters:
            </label>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setOnlyMovers(!onlyMovers)}
              style={{
                padding: '6px 12px',
                border: `2px solid ${onlyMovers ? 'var(--error)' : 'var(--border-color)'}`,
                backgroundColor: onlyMovers ? 'var(--error-light)' : 'var(--bg-primary)',
                color: onlyMovers ? 'var(--error)' : 'var(--text-primary)',
                borderRadius: '20px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: onlyMovers ? 'bold' : 'normal',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.3s ease'
              }}
            >
              {onlyMovers && '🔥'} Movers
            </button>
            <button
              onClick={() => setOnlyPolarizing(!onlyPolarizing)}
              style={{
                padding: '6px 12px',
                border: `2px solid ${onlyPolarizing ? '#9c27b0' : 'var(--border-color)'}`,
                backgroundColor: onlyPolarizing ? '#f3e5f5' : 'var(--bg-primary)',
                color: onlyPolarizing ? '#9c27b0' : 'var(--text-primary)',
                borderRadius: '20px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: onlyPolarizing ? 'bold' : 'normal',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.3s ease'
              }}
            >
              {onlyPolarizing && '⚡'} Polarizing
            </button>
            <button
              onClick={() => setOnlyHighConfidence(!onlyHighConfidence)}
              style={{
                padding: '6px 12px',
                border: `2px solid ${onlyHighConfidence ? 'var(--success)' : 'var(--border-color)'}`,
                backgroundColor: onlyHighConfidence ? 'var(--success-light)' : 'var(--bg-primary)',
                color: onlyHighConfidence ? 'var(--success)' : 'var(--text-primary)',
                borderRadius: '20px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: onlyHighConfidence ? 'bold' : 'normal',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.3s ease'
              }}
            >
              {onlyHighConfidence && '✓'} High Confidence
            </button>
            <button
              onClick={() => setPinnedOnly(!pinnedOnly)}
              style={{
                padding: '6px 12px',
                border: `2px solid ${pinnedOnly ? 'var(--primary)' : 'var(--border-color)'}`,
                backgroundColor: pinnedOnly ? 'var(--primary-light)' : 'var(--bg-primary)',
                color: pinnedOnly ? 'var(--primary)' : 'var(--text-primary)',
                borderRadius: '20px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: pinnedOnly ? 'bold' : 'normal',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.3s ease'
              }}
            >
              {pinnedOnly && '📌'} Pinned Only
            </button>
          </div>
        </div>

        {/* Reset Filters Button */}
        {hasActiveFilters && (
          <div style={{ marginLeft: 'auto' }}>
            <button
              onClick={handleResetFilters}
              style={{
                padding: '8px 16px',
                border: '2px solid var(--error)',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--error)',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
              title="Clear all filters"
            >
              ✕ Reset All Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
