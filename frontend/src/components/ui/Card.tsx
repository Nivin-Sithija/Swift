import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export interface CardProps {
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** The single neutral container used for every content section. Color lives only inside, never on the card itself. */
export function Card({ title, action, children, className }: CardProps) {
  return (
    <div className={cn("rounded-lg border border-border-subtle bg-surface-card shadow-xs", className)}>
      {title ? (
        <div className="flex items-center justify-between px-5 pt-5">
          <h3 className="m-0 text-lg font-semibold leading-tight text-text-primary">{title}</h3>
          {action}
        </div>
      ) : null}
      <div className={cn("p-5", Boolean(title) && "pt-3")}>{children}</div>
    </div>
  );
}
