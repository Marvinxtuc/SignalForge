import type { HTMLAttributes, ReactNode } from "react";

type BadgeTone = "neutral" | "success" | "warning" | "danger";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode;
  tone?: BadgeTone;
};

const toneClass: Record<BadgeTone, string> = {
  neutral: "badgeNeutral",
  success: "badgeSuccess",
  warning: "badgeWarning",
  danger: "badgeDanger"
};

export function Badge({ children, className = "", tone = "neutral", ...props }: BadgeProps) {
  return (
    <span className={`badge ${toneClass[tone]}${className ? ` ${className}` : ""}`} {...props}>
      {children}
    </span>
  );
}
