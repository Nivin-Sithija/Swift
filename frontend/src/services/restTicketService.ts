import { getApiBaseUrl } from "../lib/config";
import type { DashboardMetrics, InternalNote, Ticket, TicketSubmission, User, UserRole } from "../types";
import type { AdjacentTickets, TicketService } from "./ticketService";

type ApiPrediction = { id: string; value: string; confidence: number; model_version: string; predicted_at: string };
type ApiResponse = { text: string; status: string; updated_at: string; approved_by?: string; approved_at?: string };
type ApiTicket = Record<string, unknown> & {
  id: string; customer_id: string; customer_name: string; subject: string; message: string;
  preferred_response_language: "english" | "sinhala" | "tamil"; language: string;
  category: ApiPrediction; priority: ApiPrediction; sentiment: ApiPrediction; status: Ticket["status"];
  assigned_queue: string; assigned_agent: string | null; created_at: string; updated_at: string;
  attachments: Array<{ id: string; name: string; size: number; type: string; download_url: string }>;
  events: Array<{ id: string; label: string; detail: string; at: string; customer_visible: boolean }>;
  notes: Array<{ id: string; author: string; text: string; at: string }>;
  responses: ApiResponse[]; requires_manual_review: boolean; escalation_reason?: string;
};

let accessToken: string | null = null;
const url = (path: string) => `${getApiBaseUrl()}${path}`;
async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(url(path), { ...init, headers, credentials: "include" });
  if (response.status === 401 && retry) {
    const refreshed = await fetch(url("/auth/refresh"), { method: "POST", credentials: "include" });
    if (refreshed.ok) {
      accessToken = ((await refreshed.json()) as { access_token: string }).access_token;
      return request<T>(path, init, false);
    }
  }
  if (!response.ok) throw new Error(((await response.json().catch(() => null)) as { message?: string } | null)?.message || `Request failed (${response.status})`);
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}
const prediction = (p: ApiPrediction) => ({ value: p.value, confidence: Math.round(p.confidence * 100), modelVersion: p.model_version, predictedAt: p.predicted_at });
function mapTicket(t: ApiTicket): Ticket {
  const approved = [...t.responses].reverse().find((r) => ["approved", "sent"].includes(r.status));
  const draft = [...t.responses].reverse().find((r) => !["rejected", "sent"].includes(r.status)) || t.responses[0];
  const attachment = t.attachments[0];
  return {
    id: t.id, customerId: t.customer_id, customerName: t.customer_name, subject: t.subject, message: t.message,
    preferredResponseLanguage: t.preferred_response_language,
    language: (t.language === "code_mixed" ? "mixed" : t.language) as Ticket["language"],
    category: prediction(t.category), priority: prediction(t.priority), sentiment: prediction(t.sentiment), status: t.status,
    assignedQueue: t.assigned_queue, assignedAgent: t.assigned_agent, createdAt: t.created_at, updatedAt: t.updated_at,
    attachment: attachment ? { id: attachment.id, name: attachment.name, size: attachment.size, type: attachment.type, url: url(`/attachments/${attachment.id}/download`) } : undefined,
    imageEvidence: attachment ? { status: "processing" } : { status: "none" },
    events: t.events.map((e) => ({ id: e.id, label: e.label, detail: e.detail, at: e.at, customerVisible: e.customer_visible })),
    notes: t.notes, draft: { text: draft?.text || "", language: t.preferred_response_language, updatedAt: draft?.updated_at || t.updated_at, status: draft?.status === "approved" ? "approved" : draft?.status === "rejected" ? "rejected" : "draft" },
    approvedResponse: approved ? { text: approved.text, approvedBy: approved.approved_by || "Authorised agent", approvedAt: approved.approved_at || approved.updated_at } : undefined,
    requiresManualReview: t.requires_manual_review, escalationReason: t.escalation_reason,
  };
}
export const restTicketService: TicketService = {
  async login(email: string, password: string, _role: UserRole): Promise<User> {
    const result = await request<{ access_token: string; user: { id: string; full_name: string; email: string; role: UserRole } }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }, false);
    accessToken = result.access_token;
    return { id: result.user.id, name: result.user.full_name, email: result.user.email, role: result.user.role === "customer" ? "customer" : "agent" };
  },
  async register(input) {
    const result = await request<{ access_token: string; user: { id: string; full_name: string; email: string; role: UserRole } }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: input.name,
        email: input.email,
        password: input.password,
        role: input.role,
        preferred_language: input.preferredLanguage,
        agent_registration_code: input.agentCode || null,
      }),
    }, false);
    accessToken = result.access_token;
    return { id: result.user.id, name: result.user.full_name, email: result.user.email, role: result.user.role === "customer" ? "customer" : "agent" };
  },
  async logout() { await request<void>("/auth/logout", { method: "POST" }); accessToken = null; },
  async createTicket(submission: TicketSubmission) {
    const created = await request<ApiTicket>("/tickets", { method: "POST", body: JSON.stringify({ subject: submission.subject, message: submission.message, preferred_response_language: submission.preferredResponseLanguage }) });
    if (submission.attachment) { const body = new FormData(); body.append("file", submission.attachment); await request(`/tickets/${created.id}/attachments`, { method: "POST", body }); return this.getTicket(created.id); }
    return mapTicket(created);
  },
  async getTickets() { const data = await request<{ items: ApiTicket[] }>("/tickets?page_size=100"); return data.items.map(mapTicket); },
  async getTicket(id) { return mapTicket(await request<ApiTicket>(`/tickets/${id}`)); },
  async getAdjacentTicketIds(id): Promise<AdjacentTickets> { const tickets = await this.getTickets(); const index = tickets.findIndex((t) => t.id === id); return { previous: tickets[index - 1]?.id, next: tickets[index + 1]?.id }; },
  async updateTicket(id, patch) {
    if (patch.status) return mapTicket(await request<ApiTicket>(`/tickets/${id}/status`, { method: "PUT", body: JSON.stringify({ status: patch.status }) }));
    if (patch.assignedAgent) return mapTicket(await request<ApiTicket>(`/tickets/${id}/assignment`, { method: "PUT", body: "{}" }));
    return this.getTicket(id);
  },
  async addInternalNote(id, text): Promise<InternalNote> { const n = await request<{ id: string; author: string; text: string; at: string }>(`/tickets/${id}/notes`, { method: "POST", body: JSON.stringify({ text }) }); return n; },
  async getDashboardMetrics() { const m = await request<Record<string, number | string>>("/dashboard/metrics"); return { newTickets: Number(m.new_tickets), assignedToMe: Number(m.assigned_to_me), highPriority: Number(m.high_priority), critical: Number(m.critical), escalated: Number(m.escalated), resolvedToday: Number(m.resolved_today), averageFirstResponse: String(m.average_first_response), lowConfidence: Number(m.low_confidence) } satisfies DashboardMetrics; },
};
