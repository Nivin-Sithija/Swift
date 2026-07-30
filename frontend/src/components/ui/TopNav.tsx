import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";

export interface TopNavItem {
  to: string;
  label: string;
}

export interface TopNavProps {
  logo: ReactNode;
  items: TopNavItem[];
  right?: ReactNode;
}

/** Fixed-height full-width navbar. Swift has no sidebar — this is the only chrome above page content. */
export function TopNav({ logo, items, right }: TopNavProps) {
  return (
    <div className="flex h-[var(--navbar-height)] items-center gap-8 border-b border-border-subtle bg-surface-nav px-[var(--container-padding)]">
      {logo}
      <nav className="flex flex-1 gap-6">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn("py-2 text-base", isActive ? "font-semibold text-primary-text" : "font-medium text-text-secondary")
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="flex items-center gap-4">{right}</div>
    </div>
  );
}
