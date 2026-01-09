/**
 * TypeScript types for API responses.
 */

export interface EntityPoint {
  entity_id: string;
  entity_key: string;
  name: string;
  type: string;
  x_fame: number;
  y_love: number;
  momentum: number;
  polarization: number;
  confidence: number;
  is_pinned: boolean;
  is_dormant: boolean;
}

export interface HeatmapSnapshotResponse {
  window: {
    start: string;
    end: string;
    timezone: string;
  };
  defaults: {
    color_mode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE';
    trail_days: 7 | 30 | 90;
  };
  points: EntityPoint[];
}

export interface EntityDrilldownResponse {
  window: {
    start: string;
    end: string;
    timezone: string;
  };
  entity: {
    entity_id: string;
    entity_key: string;
    name: string;
    type: string;
    is_pinned: boolean;
  };
  metrics: {
    x_fame: number;
    y_love: number;
    momentum: number;
    polarization: number;
    confidence: number;
  };
  narrative: {
    moved_because: string;
    bullets: string[];
  };
  drivers: Array<{
    rank: number;
    source: string;
    title: string;
    url: string;
    impact_score: number;
  }>;
  themes: Array<{
    theme_id: string;
    label: string;
    keywords: string[];
    volume: number;
  }>;
  series: Array<{
    window_start: string;
    x_fame: number;
    y_love: number;
  }>;
}
