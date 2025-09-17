import { useEffect, useState } from 'react';
import type { BusinessMetric } from '../lib/dashboardTypes';

const metricsEndpoint = '/api/bi/metrics';

const BusinessIntelligenceTab = () => {
  const [metrics, setMetrics] = useState<BusinessMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    const loadMetrics = async () => {
      try {
        setLoading(true);
        const response = await fetch(metricsEndpoint, {
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error(`Failed to load metrics: ${response.status}`);
        }

        const payload: BusinessMetric[] = await response.json();
        setMetrics(payload);
        setError(null);
      } catch (err) {
        if ((err as Error).name === 'AbortError') return;
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadMetrics();
    const interval = window.setInterval(loadMetrics, 60_000);

    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, []);

  if (loading) {
    return <section className="panel">Loading Pay Ready KPIs...</section>;
  }

  if (error) {
    return (
      <section className="panel error">
        <h2>Metrics Unavailable</h2>
        <p>{error}</p>
      </section>
    );
  }

  return (
    <section className="panel-grid">
      {metrics.map((metric) => {
        const trendClass = metric.trend ? `trend-${metric.trend}` : '';
        const target = metric.target ? `${metric.target}${metric.unit ?? ''}` : '—';

        return (
          <article key={metric.id} className={`metric-card ${trendClass}`}>
            <header>
              <h2>{metric.label}</h2>
            </header>
            <div className="metric-body">
              <span className="metric-value">
                {metric.value.toLocaleString(undefined, {
                  maximumFractionDigits: 2
                })}
                {metric.unit ?? ""}
              </span>
              <dl>
                <div>
                  <dt>Trend</dt>
                  <dd>{metric.trend ?? 'stable'}</dd>
                </div>
                <div>
                  <dt>Target</dt>
                  <dd>{target}</dd>
                </div>
              </dl>
            </div>
            {metric.tags && Object.keys(metric.tags).length > 0 && (
              <div className="metric-tags">
                {Object.entries(metric.tags).map(([key, value]) => (
                  <span key={`${metric.id}-${key}`} className="tag-pill">
                    {key}: {value}
                  </span>
                ))}
              </div>
            )}
          </article>
        );
      })}
    </section>
  );
};

export default BusinessIntelligenceTab;
