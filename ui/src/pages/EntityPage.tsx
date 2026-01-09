/**
 * Entity drilldown page.
 */

import { useParams } from 'react-router-dom';
import DrilldownPanel from '../components/DrilldownPanel';
import DriversList from '../components/DriversList';
import ThemesList from '../components/ThemesList';

export default function EntityPage() {
  const { entityId } = useParams();
  
  // TODO: Implement
  // - Load entity drilldown data from API
  // - Display metrics, narrative, drivers, themes
  // - Display historical series (trail)
  return (
    <div>
      <h1>Entity Drilldown</h1>
      <DrilldownPanel entityId={entityId} />
      <DriversList entityId={entityId} />
      <ThemesList entityId={entityId} />
    </div>
  );
}
