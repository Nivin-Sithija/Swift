import { cn } from "../../lib/utils";

export interface AvatarProps {
  name: string;
  src?: string;
  size?: number;
  className?: string;
}

/** Initials or image circle, e.g. the agent/customer identity chip in nav and profile menus. */
export function Avatar({ name, src, size = 32, className }: AvatarProps) {
  const initials = name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold leading-none",
        src ? "bg-transparent" : "bg-blue-100 text-blue-700",
        className,
      )}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {src ? <img src={src} alt={name} className="h-full w-full object-cover" /> : initials}
    </span>
  );
}
