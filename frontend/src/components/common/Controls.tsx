import { Check, Languages, Moon, Sun, Monitor, X, Search } from "lucide-react";
import { useEffect, useId } from "react";
import { useLanguage } from "../../app/providers/LanguageProvider";
import { useTheme, type Theme } from "../../app/providers/ThemeProvider";
import { cn } from "../../lib/utils";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="logo">
      <img src="/logo.png" alt="Swift" />
      {!compact && <strong>Swift</strong>}
    </div>
  );
}
export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  const options: Array<[Theme, typeof Moon]> = [
    ["dark", Moon],
    ["light", Sun],
    ["system", Monitor],
  ];
  return (
    <div className="segmented" aria-label="Theme">
      {options.map(([value, Icon]) => (
        <button
          key={value}
          className={cn(theme === value && "active")}
          onClick={() => setTheme(value)}
          aria-label={`${value} theme`}
          title={`${value} theme`}
        >
          <Icon size={16} />
        </button>
      ))}
    </div>
  );
}
export function LanguageSelector() {
  const { language, setLanguage } = useLanguage();
  return (
    <label className="select-compact">
      <Languages size={16} />
      <span className="sr-only">Interface language</span>
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as "en" | "si" | "ta")}
      >
        <option value="en">English</option>
        <option value="si">සිංහල</option>
        <option value="ta">தமிழ்</option>
      </select>
    </label>
  );
}
export function SearchInput({
  value,
  onChange,
  placeholder = "Search tickets…",
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="search">
      <Search size={17} />
      <span className="sr-only">Search</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      {value && (
        <button onClick={() => onChange("")} aria-label="Clear search">
          <X size={15} />
        </button>
      )}
    </label>
  );
}
export function ConfirmationDialog({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  onConfirm,
  onCancel,
  danger = false,
}: {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  danger?: boolean;
}) {
  const titleId = useId();
  // Escape must dismiss a modal; without it the scrim is the only way out.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) =>
      event.key === "Escape" && onCancel();
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onCancel]);
  if (!open) return null;
  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={(e) => e.target === e.currentTarget && onCancel()}
    >
      <div
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <div className="dialog-icon">
          <Check />
        </div>
        <h2 id={titleId}>{title}</h2>
        <p>{description}</p>
        <div className="dialog-actions">
          <button className="btn secondary" onClick={onCancel}>
            Cancel
          </button>
          <button
            autoFocus
            className={cn("btn", danger && "danger")}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
