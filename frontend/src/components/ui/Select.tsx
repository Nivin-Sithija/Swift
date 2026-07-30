import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
}

const chevron =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%23717A8A' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E\")";

/** Native-backed dropdown styled to match Input — used for filter bars and forms. Forwards its ref for react-hook-form. */
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  function Select({ label, options, className, id, ...props }, ref) {
    const select = (
      <select
        ref={ref}
        id={id}
        className={cn(
          "h-[34px] cursor-pointer appearance-none rounded-md border border-border-default bg-surface-card py-0 pl-2.5 pr-7 text-sm text-text-primary outline-none",
          "focus:border-border-focus focus:shadow-[var(--focus-ring)]",
          className,
        )}
        style={{
          backgroundImage: chevron,
          backgroundRepeat: "no-repeat",
          backgroundPosition: "right 10px center",
        }}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    );
    if (!label) return select;
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={id} className="text-xs font-medium text-text-muted">
          {label}
        </label>
        {select}
      </div>
    );
  },
);
