/**
 * Interactive scatter plot heatmap visualization.
 */

interface HeatmapProps {
  data: any[]; // EntityPoint[]
  colorMode: 'MOMENTUM' | 'POLARIZATION' | 'CONFIDENCE';
  onDotClick: (entityId: string) => void;
}

export default function Heatmap({ data, colorMode, onDotClick }: HeatmapProps) {
  // TODO: Implement
  // - Use Recharts or similar for scatter plot
  // - Map x_fame, y_love to axes
  // - Color dots by colorMode
  // - Handle dot clicks -> onDotClick
  // - Display quadrants
  return (
    <div>
      {/* TODO: Implement scatter plot */}
    </div>
  );
}
