const statusItems = [
  "Phase 0 Infrastructure",
  "API status placeholder",
  "No business functionality in this phase",
  "No Signal Inbox, connectors, pipeline, or product dashboards yet"
];

export default function Home() {
  return (
    <main className="shell">
      <section className="panel" aria-labelledby="title">
        <p className="eyebrow">SignalForge</p>
        <h1 id="title">Phase 0 Infrastructure</h1>
        <p className="summary">
          This shell verifies that the Web service can start. Product workflows
          begin in later phases after the infrastructure gate passes.
        </p>
        <ul className="statusList">
          {statusItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
