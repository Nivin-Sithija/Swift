import type { TicketStatus } from "../types";

// Keep aligned with backend/app/domain/policies.py.
const transitions: Record<TicketStatus, TicketStatus[]> = {
  new: ["processing", "assigned", "escalated"],
  processing: ["in_review", "escalated"],
  in_review: ["assigned", "escalated", "response_draft"],
  assigned: ["escalated", "response_draft", "resolved"],
  escalated: ["assigned", "response_draft", "resolved"],
  response_draft: ["responded", "assigned"],
  responded: ["resolved", "reopened"],
  resolved: ["closed", "reopened"],
  closed: ["reopened"],
  reopened: ["assigned", "escalated"],
};

export const canChangeTicketStatus = (from: TicketStatus, to: TicketStatus) =>
  transitions[from].includes(to);

export const canAssignTicket = (status: TicketStatus) =>
  status === "assigned" || canChangeTicketStatus(status, "assigned");
