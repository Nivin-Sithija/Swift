import type {
  FilterState,
  SupportedLanguage,
  TicketPriority,
  TicketSentiment,
  TicketStatus,
} from "../types";

/** The demo agent the mock service signs in as. Every "who did this" string
    resolves here so there is one place to change when real auth lands. */
export const CURRENT_AGENT = "Anika Fernando";

export const TICKET_STATUSES: TicketStatus[] = [
  "new",
  "processing",
  "in_review",
  "assigned",
  "escalated",
  "resolved",
  "closed",
  "reopened",
];

export const TICKET_PRIORITIES: TicketPriority[] = [
  "low",
  "medium",
  "high",
  "critical",
];

export const TICKET_SENTIMENTS: TicketSentiment[] = [
  "positive",
  "neutral",
  "negative",
];

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  "english",
  "sinhala",
  "tamil",
  "singlish",
  "tanglish",
  "mixed",
];

/** The BANKING77 intents the mock data draws from. The production list is the
    full 77-way taxonomy served by the classifier, not this preview subset. */
export const TICKET_CATEGORIES = [
  "card_payment_wrong_exchange_rate",
  "cash_withdrawal",
  "cash_withdrawal_not_received",
  "pending_transfer",
  "beneficiary_not_allowed",
  "cash_transfer",
] as const;

export const EMPTY_FILTERS: FilterState = {
  search: "",
  status: "all",
  priority: "all",
  language: "all",
};
