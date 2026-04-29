import type { ReactNode } from "react";

type MetricProps = {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
};

export function Metric({ detail, label, value }: MetricProps) {
  return (
    <section className="metric">
      <p className="metricLabel">{label}</p>
      <p className="metricValue">{value}</p>
      {detail ? <p className="metricDetail">{detail}</p> : null}
    </section>
  );
}
