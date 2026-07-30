import type { ReactNode } from "react";

export interface DialogProps {
  open: boolean;
  title: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
}

/** Centered modal with scrim, used for confirmation actions. */
export function Dialog({ open, title, children, footer, onClose }: DialogProps) {
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
        aria-labelledby="dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
        className="w-[420px] rounded-lg border border-border-subtle bg-surface-card shadow-md"
      >
        <div id="dialog-title" className="border-b border-border-subtle p-5 text-lg font-semibold leading-tight text-text-primary">
          {title}
        </div>
        <div className="p-5">{children}</div>
        {footer ? <div className="flex justify-end gap-3 border-t border-border-subtle p-4 px-5">{footer}</div> : null}
      </div>
    </div>
  );
}
