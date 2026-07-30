import { Badge, type BadgeTone } from "./Badge";

export type QueuePriority = "High" | "Medium" | "Low";

const priorityTone: Record<QueuePriority, BadgeTone> = {
  High: "error",
  Medium: "warning",
  Low: "success",
};

const dotClass: Record<QueuePriority, string> = {
  High: "bg-red-500",
  Medium: "bg-amber-500",
  Low: "bg-green-500",
};

export interface PriorityQueueRowProps {
  customer: string;
  snippet: string;
  priority: QueuePriority;
  category: string;
  minutesAgo: string;
}

/** Single row in the dashboard's live priority queue list. */
export function PriorityQueueRow({
  customer,
  snippet,
  priority,
  category,
  minutesAgo,
}: PriorityQueueRowProps) {
  return (
    <div className="flex items-center gap-4 border-b border-border-subtle py-3 last:border-b-0">
      <span className={`h-2 w-2 shrink-0 rounded-full ${dotClass[priority]}`} />
      <div className="min-w-0 flex-1">
        <div className="font-medium text-text-primary">{customer}</div>
        <div className="truncate text-sm text-text-muted">{snippet}</div>
      </div>
      <span className="shrink-0 text-sm text-text-muted">{category}</span>
      <Badge tone={priorityTone[priority]}>{priority}</Badge>
      <span className="w-14 shrink-0 text-right text-sm text-text-muted">
        {minutesAgo}
      </span>
    </div>
  );
}
