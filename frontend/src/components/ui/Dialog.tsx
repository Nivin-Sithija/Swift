import { useEffect, useId, type ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  title: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
}

/** Centered modal with scrim, used for confirmation actions. */
export function Dialog({
  open,
  title,
  children,
  footer,
  onClose,
}: DialogProps) {
  const titleId = useId();
  // Escape must dismiss a modal; without it the scrim is the only way out.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) =>
      event.key === "Escape" && onClose();
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-surface-overlay"
      role="presentation"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(event) => event.stopPropagation()}
        className="w-[420px] rounded-lg border border-border-subtle bg-surface-card shadow-md"
      >
        <div
          id={titleId}
          className="border-b border-border-subtle p-5 text-lg font-semibold leading-tight text-text-primary"
        >
          {title}
        </div>
        <div className="p-5">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-3 border-t border-border-subtle p-4 px-5">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}
