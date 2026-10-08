import type { ConfidenceBand, Ticket, TicketPriority } from "../types";

export const cn = (...classes: Array<string | false | undefined>) =>
  classes.filter(Boolean).join(" ");

export const confidenceBand = (value: number): ConfidenceBand =>
  value >= 80 ? "high" : value >= 60 ? "medium" : "low";

export const formatDate = (value: string) =>
  new Intl.DateTimeFormat("en-LK", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));

const priorityRank: Record<TicketPriority, number> = {
  critical: 4,
  high: 3,
  medium: 2,
  low: 1,
};

export function filterTickets(
  tickets: Ticket[],
  filters: Partial<{
    search: string;
    status: string;
    priority: string;
    language: string;
  }>,
) {
  const query = filters.search?.trim().toLowerCase();
  return tickets.filter(
    (ticket) =>
      (!query ||
        ticket.id.toLowerCase().includes(query) ||
        ticket.subject.toLowerCase().includes(query) ||
        ticket.customerName.toLowerCase().includes(query)) &&
      (!filters.status ||
        filters.status === "all" ||
        ticket.status === filters.status) &&
      (!filters.priority ||
        filters.priority === "all" ||
        ticket.priority.value === filters.priority) &&
      (!filters.language ||
        filters.language === "all" ||
        ticket.language === filters.language),
  );
}

export type TicketSort = "urgency" | "priority" | "newest" | "confidence" | "waiting";

export function urgencyScore(ticket: Ticket, now = Date.now()): number {
  const urgency = ticket.urgency;
  if (!urgency || !urgency.active) return 0;
  const elapsed = Math.max(0, (now - Date.parse(urgency.evaluatedAt)) / 60_000);
  return urgency.intrinsicSeverity *
    (1 + urgency.agingAlpha * (urgency.waitingMinutes + elapsed) / urgency.slaMinutes);
}

export const isTicketSort = (value: string | null): value is TicketSort =>
  ["urgency", "priority", "newest", "confidence", "waiting"].includes(value || "");

const comparators: Record<Exclude<TicketSort, "urgency">, (a: Ticket, b: Ticket) => number> = {
  priority: (a, b) =>
    priorityRank[b.priority.value as TicketPriority] -
      priorityRank[a.priority.value as TicketPriority] ||
    +new Date(b.createdAt) - +new Date(a.createdAt),
  newest: (a, b) => +new Date(b.createdAt) - +new Date(a.createdAt),
  confidence: (a, b) => a.category.confidence - b.category.confidence,
  waiting: (a, b) => +new Date(a.createdAt) - +new Date(b.createdAt),
};

export const sortTickets = (tickets: Ticket[], sort: TicketSort = "urgency", now = Date.now()) =>
  [...tickets].sort(sort === "urgency" ? (a, b) =>
    Number(Boolean(b.urgency?.active)) - Number(Boolean(a.urgency?.active)) ||
    urgencyScore(b, now) - urgencyScore(a, now) ||
    +new Date(a.createdAt) - +new Date(b.createdAt) || a.id.localeCompare(b.id)
    : comparators[sort]);

export const delay = (ms = 350) =>
  new Promise((resolve) => setTimeout(resolve, ms));
