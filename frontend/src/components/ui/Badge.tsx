import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export type BadgeTone =
  "neutral" | "primary" | "success" | "info" | "warning" | "error" | "accent2";

const toneClasses: Record<BadgeTone, string> = {
  neutral:
    "bg-neutral-badge-subtle border-neutral-badge-border text-neutral-badge-text",
  primary: "bg-primary-subtle border-primary-subtle-border text-primary-text",
  success: "bg-success-subtle border-success-border text-success-text",
  info: "bg-info-subtle border-info-border text-info-text",
  warning: "bg-warning-subtle border-warning-border text-warning-text",
  error: "bg-error-subtle border-error-border text-error-text",
  accent2: "bg-accent2-subtle border-accent2-border text-accent2-text",
};

export interface BadgeProps {
  tone?: BadgeTone;
  icon?: LucideIcon;
  children: ReactNode;
  className?: string;
}

/** Pill-shaped status/label chip — the core vocabulary for category, priority, sentiment, language and channel tags. */
export function Badge({
  tone = "neutral",
  icon: Icon,
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-[5px] whitespace-nowrap rounded-pill border px-2.5 py-[3px] text-xs font-medium leading-none",
        toneClasses[tone],
        className,
      )}
    >
      {Icon ? <Icon size={12} /> : null}
      {children}
    </span>
  );
}
