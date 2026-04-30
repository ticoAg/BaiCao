import type { ReactNode } from "react";
import { cx } from "./radix";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

type AppBadgeProps = {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
};

export const AppBadge = ({ children, tone = "neutral", className }: AppBadgeProps) => (
  <span className={cx("bc-badge", `bc-badge--${tone}`, className)}>{children}</span>
);

export const Spinner = ({ label = "加载中" }: { label?: string }) => (
  <span className="bc-spinner" role="status" aria-label={label} />
);

export const EmptyState = ({ description }: { description: string }) => (
  <div className="bc-empty-state">
    <div className="bc-empty-mark" aria-hidden="true" />
    <span>{description}</span>
  </div>
);
