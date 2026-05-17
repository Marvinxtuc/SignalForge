type LoadingStateProps = {
  label?: string;
};

export function LoadingState({ label = "加载中" }: LoadingStateProps) {
  return (
    <div className="loadingRow" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
