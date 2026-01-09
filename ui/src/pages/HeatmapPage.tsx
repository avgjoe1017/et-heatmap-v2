/**
 * Main heatmap page with scatter plot visualization.
 */

import { useState, useEffect } from 'react';
import Heatmap from '../components/Heatmap';
import Filters from '../components/Filters';
import TimelineScrubber from '../components/TimelineScrubber';

export default function HeatmapPage() {
  // TODO: Implement
  // - Load snapshot data from API
  // - Handle filters (type, genre, etc.)
  // - Handle color mode toggle (momentum/polarization/confidence)
  // - Handle timeline scrubbing
  // - Handle dot clicks -> navigate to EntityPage
  return (
    <div>
      <h1>Entertainment Feelings Heatmap</h1>
      <Filters />
      <TimelineScrubber />
      <Heatmap />
    </div>
  );
}
