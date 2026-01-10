/**
 * URL state management utilities for shareable links.
 * Supports filters, color mode, selected entity, and window start.
 */

export interface URLState {
  colorMode?: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE';
  types?: string[];
  onlyMovers?: boolean;
  onlyPolarizing?: boolean;
  onlyHighConfidence?: boolean;
  pinnedOnly?: boolean;
  entityId?: string;
  windowStart?: string;
}

/**
 * Parse URL search params into state object.
 */
export function parseURLState(searchParams: URLSearchParams): URLState {
  const state: URLState = {};

  // Color mode
  const colorMode = searchParams.get('colorMode');
  if (colorMode && ['MOMENTUM', 'POLARIZATION', 'CONFIDENCE'].includes(colorMode)) {
    state.colorMode = colorMode as 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE';
  }

  // Types filter
  const types = searchParams.get('types');
  if (types) {
    state.types = types.split(',').filter(Boolean);
  }

  // Boolean filters
  state.onlyMovers = searchParams.get('onlyMovers') === 'true';
  state.onlyPolarizing = searchParams.get('onlyPolarizing') === 'true';
  state.onlyHighConfidence = searchParams.get('onlyHighConfidence') === 'true';
  state.pinnedOnly = searchParams.get('pinnedOnly') === 'true';

  // Entity ID
  const entityId = searchParams.get('entityId');
  if (entityId) {
    state.entityId = entityId;
  }

  // Window start
  const windowStart = searchParams.get('windowStart');
  if (windowStart) {
    state.windowStart = windowStart;
  }

  return state;
}

/**
 * Convert state object to URL search params.
 */
export function stateToURLParams(state: Partial<URLState>): URLSearchParams {
  const params = new URLSearchParams();

  if (state.colorMode) {
    params.set('colorMode', state.colorMode);
  }

  if (state.types && state.types.length > 0) {
    params.set('types', state.types.join(','));
  }

  if (state.onlyMovers) {
    params.set('onlyMovers', 'true');
  }

  if (state.onlyPolarizing) {
    params.set('onlyPolarizing', 'true');
  }

  if (state.onlyHighConfidence) {
    params.set('onlyHighConfidence', 'true');
  }

  if (state.pinnedOnly) {
    params.set('pinnedOnly', 'true');
  }

  if (state.entityId) {
    params.set('entityId', state.entityId);
  }

  if (state.windowStart) {
    params.set('windowStart', state.windowStart);
  }

  return params;
}

/**
 * Update URL without page reload.
 */
export function updateURL(state: Partial<URLState>, replace = false) {
  const params = stateToURLParams(state);
  const newURL = params.toString() 
    ? `${window.location.pathname}?${params.toString()}`
    : window.location.pathname;

  if (replace) {
    window.history.replaceState({}, '', newURL);
  } else {
    window.history.pushState({}, '', newURL);
  }
}

/**
 * Get shareable URL with current state.
 */
export function getShareableURL(state: Partial<URLState>): string {
  const params = stateToURLParams(state);
  const query = params.toString();
  return `${window.location.origin}${window.location.pathname}${query ? `?${query}` : ''}`;
}
