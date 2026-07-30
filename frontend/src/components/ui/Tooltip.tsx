import { useState, type ReactNode } from "react";

export interface TooltipProps {
  label: string;
  children: ReactNode;
}

/** Small dark popover on hover, for truncated text or icon-only affordances. */
export function Tooltip({ label, children }: TooltipProps) {
  const [show, setShow] = useState(false);
  return (
    <span
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
      onFocus={() => setShow(true)}
      onBlur={() => setShow(false)}
    >
      {children}
      {show ? (
        <span
          role="tooltip"
          className="absolute bottom-[125%] left-1/2 z-50 -translate-x-1/2 whitespace-nowrap rounded-sm bg-gray-900 px-[9px] py-[5px] text-xs font-medium leading-[1.3] text-text-inverse shadow-sm"
        >
          {label}
        </span>
      ) : null}
    </span>
  );
}
