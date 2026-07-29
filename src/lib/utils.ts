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
    category: string;
  }>,
) {
  const query = filters.search?.trim().toLowerCase();
  return tickets.filter(
    (ticket) =>
      (!query ||
        ticket.id.toLowerCase().includes(query) ||
        ticket.subject.toLowerCase().includes(query) ||
        ticket.customerName.toLowerCase().includes(query)) &&
      (!filters.status || filters.status === "all" || ticket.status === filters.status) &&
      (!filters.priority ||
        filters.priority === "all" ||
        ticket.priority.value === filters.priority) &&
      (!filters.language ||
        filters.language === "all" ||
        ticket.language === filters.language) &&
      (!filters.category ||
        filters.category === "all" ||
        ticket.category.value === filters.category),
  );
}

export const sortByPriority = (tickets: Ticket[]) =>
  [...tickets].sort(
    (a, b) =>
      priorityRank[b.priority.value as TicketPriority] -
        priorityRank[a.priority.value as TicketPriority] ||
      +new Date(b.createdAt) - +new Date(a.createdAt),
  );

export const delay = (ms = 350) => new Promise((resolve) => setTimeout(resolve, ms));
