import { Suspense } from "react";
import { LogsPage } from "../../components/logs/LogsPage";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <LogsPage />
    </Suspense>
  );
}
