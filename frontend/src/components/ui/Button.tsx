import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md";

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-primary-solid text-text-inverse border-transparent hover:bg-primary-solid-hover active:bg-primary-solid-active",
  secondary: "bg-surface-card text-text-primary border-border-default hover:bg-surface-hover active:bg-gray-150",
  ghost: "bg-transparent text-text-secondary border-transparent hover:bg-surface-hover active:bg-gray-150",
  danger: "bg-error-subtle text-error-text border-error-border hover:bg-[#fbdede] active:bg-[#f6cccc]",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 gap-1.5 text-sm",
  md: "h-[38px] px-4 gap-[7px] text-base",
};

export interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: LucideIcon;
  iconOnly?: boolean;
  children?: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  icon: Icon,
  iconOnly,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled}
      className={cn(
        "inline-flex items-center justify-center rounded-md border font-medium transition-colors duration-[var(--duration-fast)] ease-[var(--ease-standard)] disabled:cursor-not-allowed disabled:opacity-50",
        iconOnly ? (size === "sm" ? "h-8 w-8 p-0" : "h-[38px] w-[38px] p-0") : sizeClasses[size],
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {Icon ? <Icon size={size === "sm" ? 14 : 16} /> : null}
      {!iconOnly ? children : null}
    </button>
  );
}

export function IconButton({
  icon,
  size = "md",
  variant = "ghost",
  active,
  className,
  ...props
}: Omit<ButtonProps, "iconOnly" | "children"> & { active?: boolean }) {
  return (
    <Button
      variant={active ? "secondary" : variant}
      size={size}
      icon={icon}
      iconOnly
      className={className}
      {...props}
    />
  );
}
