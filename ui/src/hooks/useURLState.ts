/**
 * React hook for managing URL state.
 */

import { useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { parseURLState, stateToURLParams, type URLState } from '../utils/urlState';

export function useURLState() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Get current state from URL
  const state = parseURLState(searchParams);

  // Update URL state
  const updateState = useCallback((newState: Partial<URLState>, replace = false) => {
    const currentState = parseURLState(searchParams);
    const mergedState = { ...currentState, ...newState };
    
    // Remove falsy values (except for entityId which can be explicitly cleared)
    Object.keys(mergedState).forEach(key => {
      const value = (mergedState as any)[key];
      if (value === false || value === undefined || (Array.isArray(value) && value.length === 0)) {
        if (key !== 'entityId') {
          delete (mergedState as any)[key];
        }
      }
    });

    const params = stateToURLParams(mergedState);
    if (replace) {
      setSearchParams(params, { replace: true });
    } else {
      setSearchParams(params);
    }
  }, [searchParams, setSearchParams]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    const params = new URLSearchParams();
    // Keep entityId and windowStart if present
    if (searchParams.get('entityId')) {
      params.set('entityId', searchParams.get('entityId')!);
    }
    if (searchParams.get('windowStart')) {
      params.set('windowStart', searchParams.get('windowStart')!);
    }
    setSearchParams(params, { replace: true });
  }, [searchParams, setSearchParams]);

  return {
    state,
    updateState,
    clearFilters,
  };
}
