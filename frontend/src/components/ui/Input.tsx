import { forwardRef, type InputHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  icon?: LucideIcon;
  size?: "sm" | "md";
}

/** Text input with an optional leading icon — forwards its ref so it works with react-hook-form's `register()`. */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { icon: Icon, size = "md", className, ...props },
  ref,
) {
  return (
    <div className="relative flex items-center">
      {Icon ? <Icon size={15} className="pointer-events-none absolute left-2.5 text-text-muted" /> : null}
      <input
        ref={ref}
        className={cn(
          "w-full rounded-md border border-border-default bg-surface-card text-base text-text-primary outline-none",
          "focus:border-border-focus focus:shadow-[var(--focus-ring)]",
          size === "sm" ? "h-8" : "h-[38px]",
          Icon ? "pl-8 pr-3" : "px-3",
          className,
        )}
        {...props}
      />
    </div>
  );
});
