import { useState } from "react";
import { cn } from "../../lib/utils";

export interface TabItem {
  value: string;
  label: string;
}

export interface TabsProps {
  items: TabItem[];
  defaultValue?: string;
  onChange?: (value: string) => void;
}

/** Underline-style segmented navigation, e.g. ticket-detail sub-views. */
export function Tabs({ items, defaultValue, onChange }: TabsProps) {
  const [active, setActive] = useState(defaultValue ?? items[0]?.value);
  const select = (value: string) => {
    setActive(value);
    onChange?.(value);
  };
  return (
    <div className="flex gap-6 border-b border-border-subtle" role="tablist">
      {items.map((item) => {
        const isActive = item.value === active;
        return (
          <button
            key={item.value}
            role="tab"
            aria-selected={isActive}
            onClick={() => select(item.value)}
            className={cn(
              "-mb-px cursor-pointer border-b-2 bg-transparent px-0.5 py-2.5 text-base transition-colors duration-[var(--duration-fast)] ease-[var(--ease-standard)]",
              isActive
                ? "border-primary-solid font-semibold text-text-primary"
                : "border-transparent font-medium text-text-secondary",
            )}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
