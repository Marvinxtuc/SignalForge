import { Suspense } from "react";
import { OpportunitiesPage } from "../../components/opportunities/OpportunitiesPage";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <OpportunitiesPage />
    </Suspense>
  );
}
