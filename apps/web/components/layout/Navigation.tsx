"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { NAV_ITEMS } from "../../lib/constants";

export function Navigation({ selectedProjectId }: { selectedProjectId: string | null }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId") ?? selectedProjectId;

  return (
    <nav aria-label="Primary">
      <p className="sectionLabel">Navigation</p>
      <div className="navList">
        {NAV_ITEMS.map((item) => {
          const href = projectId
            ? `${item.href}?projectId=${encodeURIComponent(projectId)}`
            : item.href;
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              aria-current={isActive ? "page" : undefined}
              className={`navItem${isActive ? " navItemActive" : ""}`}
              href={href}
              key={item.href}
            >
              <span>{item.label}</span>
              <span className="navHint">{item.hint}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
