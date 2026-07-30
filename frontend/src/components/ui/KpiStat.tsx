import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export interface KpiStatProps {
  label: string;
  value: ReactNode;
  delta?: string;
  deltaTone?: "success" | "error";
  sublabel?: string;
  className?: string;
}

/** Single stat block used in the dashboard's KPI row. */
export function KpiStat({ label, value, delta, deltaTone = "success", sublabel, className }: KpiStatProps) {
  return (
    <div className={cn("rounded-lg border border-border-subtle bg-surface-card p-5 shadow-xs", className)}>
      <div className="mb-3 text-sm font-medium text-text-secondary">{label}</div>
      <div className="mb-3 text-[30px] font-bold leading-tight text-text-primary">{value}</div>
      {delta ? (
        <div className="flex items-center gap-1.5 border-t border-border-subtle pt-3">
          <span className={cn("text-xs font-semibold", deltaTone === "success" ? "text-success-text" : "text-error-text")}>
            {delta}
          </span>
          {sublabel ? <span className="text-sm text-text-muted">{sublabel}</span> : null}
        </div>
      ) : null}
    </div>
  );
}
