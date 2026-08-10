export type UserRole = "customer" | "agent";
export type SupportedLanguage =
  "english" | "sinhala" | "tamil" | "singlish" | "tanglish" | "mixed";
export type TicketPriority = "low" | "medium" | "high" | "critical";
export type TicketSentiment = "positive" | "neutral" | "negative";
export type TicketStatus =
  | "new"
  | "processing"
  | "in_review"
  | "assigned"
  | "escalated"
  | "response_draft"
  | "responded"
  | "resolved"
  | "closed"
  | "reopened";
export type ConfidenceBand = "high" | "medium" | "low";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}
export interface Customer extends User {
  role: "customer";
  customerId: string;
}
export interface Agent extends User {
  role: "agent";
  team: string;
}
export interface TicketPrediction {
  value: string;
  confidence: number;
  modelVersion: string;
  predictedAt: string;
}
export interface PredictionCorrection {
  field: "category" | "priority" | "sentiment";
  previousValue: string;
  correctedValue: string;
  reason: string;
  correctedBy: string;
  correctedAt: string;
}
export interface Attachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url?: string;
}
export interface ImageEvidence {
  status: "processed" | "failed" | "processing" | "none";
  ocrText?: string;
  confidence?: number;
}
export interface TicketEvent {
  id: string;
  label: string;
  detail: string;
  at: string;
  customerVisible: boolean;
}
export interface InternalNote {
  id: string;
  author: string;
  text: string;
  at: string;
}
export interface ResponseDraft {
  text: string;
  language: "english" | "sinhala" | "tamil";
  updatedAt: string;
  status: "draft" | "rejected" | "approved";
}
export interface ApprovedResponse {
  text: string;
  approvedBy: string;
  approvedAt: string;
}
export interface Ticket {
  id: string;
  customerId: string;
  customerName: string;
  subject: string;
  message: string;
  preferredResponseLanguage: "english" | "sinhala" | "tamil";
  language: SupportedLanguage;
  category: TicketPrediction;
  priority: TicketPrediction;
  sentiment: TicketPrediction;
  status: TicketStatus;
  assignedQueue: string;
  assignedAgent: string | null;
  createdAt: string;
  updatedAt: string;
  attachment?: Attachment;
  imageEvidence: ImageEvidence;
  events: TicketEvent[];
  notes: InternalNote[];
  draft: ResponseDraft;
  approvedResponse?: ApprovedResponse;
  requiresManualReview: boolean;
  escalationReason?: string;
}
export interface DashboardMetrics {
  newTickets: number;
  assignedToMe: number;
  highPriority: number;
  critical: number;
  escalated: number;
  resolvedToday: number;
  averageFirstResponse: string;
  lowConfidence: number;
}
export interface TicketSubmission {
  subject: string;
  message: string;
  preferredResponseLanguage: "english" | "sinhala" | "tamil";
  attachment?: File | null;
}
export interface FilterState {
  search: string;
  status: string;
  priority: string;
  language: string;
}
