/**
 * Timeline scrubber for viewing historical snapshots.
 */

import { useState, useEffect } from 'react';
import { getLatestRun, listRuns } from '../api/client';

interface TimelineScrubberProps {
  currentWindow?: string;
  onWindowChange: (windowStart: string) => void;
}

export default function TimelineScrubber({ currentWindow, onWindowChange }: TimelineScrubberProps) {
  const [availableWindows, setAvailableWindows] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Load available windows from API
  useEffect(() => {
    loadAvailableWindows();
  }, []);

  const loadAvailableWindows = async () => {
    setLoading(true);
    try {
      const response = await listRuns(100, 'SUCCESS');
      const runs = response.runs || [];
      const windows = runs.map((run: any) => run.window_start).filter(Boolean);
      setAvailableWindows(windows);
      
      // If no current window set, use latest
      if (!currentWindow && windows.length > 0) {
        onWindowChange(windows[0]);
      }
    } catch (error) {
      console.error('Failed to load available windows:', error);
      // Fallback to current window if API fails
      if (currentWindow) {
        setAvailableWindows([currentWindow]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePrevious = () => {
    if (!currentWindow) return;
    const currentIndex = availableWindows.indexOf(currentWindow);
    if (currentIndex > 0) {
      onWindowChange(availableWindows[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    if (!currentWindow) return;
    const currentIndex = availableWindows.indexOf(currentWindow);
    if (currentIndex < availableWindows.length - 1) {
      onWindowChange(availableWindows[currentIndex + 1]);
    }
  };
  
  const currentIndex = currentWindow ? availableWindows.indexOf(currentWindow) : -1;
  const canGoPrevious = currentIndex > 0;
  const canGoNext = currentIndex >= 0 && currentIndex < availableWindows.length - 1;

  return (
    <div style={{
      backgroundColor: '#f5f5f5',
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      fontSize: '14px'
    }}>
      <span style={{ fontWeight: 'bold', color: '#666' }}>Timeline:</span>
      
      <button
        onClick={handlePrevious}
        disabled={!canGoPrevious || loading}
        style={{
          padding: '4px 12px',
          border: '1px solid #ccc',
          backgroundColor: (!canGoPrevious || loading) ? '#f0f0f0' : 'white',
          borderRadius: '4px',
          cursor: (!canGoPrevious || loading) ? 'not-allowed' : 'pointer',
          fontSize: '12px'
        }}
      >
        ← Previous
      </button>

      {loading ? (
        <span style={{ color: '#999', minWidth: '200px', textAlign: 'center' }}>Loading...</span>
      ) : currentWindow ? (
        <span style={{ color: '#333', minWidth: '200px', textAlign: 'center' }}>
          {new Date(currentWindow).toLocaleDateString()} {new Date(currentWindow).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          {availableWindows.length > 1 && (
            <span style={{ fontSize: '11px', color: '#999', marginLeft: '8px' }}>
              ({currentIndex + 1} of {availableWindows.length})
            </span>
          )}
        </span>
      ) : (
        <span style={{ color: '#999', minWidth: '200px', textAlign: 'center' }}>No data available</span>
      )}

      <button
        onClick={handleNext}
        disabled={!canGoNext || loading}
        style={{
          padding: '4px 12px',
          border: '1px solid #ccc',
          backgroundColor: (!canGoNext || loading) ? '#f0f0f0' : 'white',
          borderRadius: '4px',
          cursor: (!canGoNext || loading) ? 'not-allowed' : 'pointer',
          fontSize: '12px'
        }}
      >
        Next →
      </button>
    </div>
  );
}
