import { Suspense } from "react";
import { ProductionPage } from "../../components/production/ProductionPage";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <ProductionPage />
    </Suspense>
  );
}
