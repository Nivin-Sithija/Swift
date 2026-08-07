import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  MessageSquareText,
  UserCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageHeader } from "../../components/layout/Layouts";
import { ConfirmationDialog } from "../../components/common/Controls";
import {
  ImageEvidencePanel,
  InternalNotes,
  PredictionCard,
  ResponseEditor,
} from "../../components/agent/AgentPanels";
import {
  EmptyState,
  LanguageBadge,
  LoadingSkeleton,
  PriorityBadge,
  SentimentBadge,
  StatusBadge,
  TicketTimeline,
  humanize,
} from "../../components/tickets/TicketComponents";
import { ticketService } from "../../services/serviceSelector";
import type { AdjacentTickets } from "../../services/ticketService";
import type { Ticket, TicketEvent, TicketStatus } from "../../types";
import { formatDate } from "../../lib/utils";
import {
  CURRENT_AGENT,
  TICKET_CATEGORIES,
  TICKET_PRIORITIES,
  TICKET_SENTIMENTS,
} from "../../lib/constants";
export function AgentTicketDetailPage() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [neighbours, setNeighbours] = useState<AdjacentTickets>({});
  const [loadError, setLoadError] = useState(false);
  const [dialog, setDialog] = useState<"escalate" | "resolve" | "close" | null>(
    null,
  );
  const [notice, setNotice] = useState("");
  useEffect(() => {
    let active = true;
    setTicket(null);
    setLoadError(false);
    Promise.all([
      ticketService.getTicket(ticketId || ""),
      ticketService.getAdjacentTicketIds(ticketId || ""),
    ])
      .then(([next, adjacent]) => {
        if (!active) return;
        setTicket(next);
        setNeighbours(adjacent);
      })
      .catch((error) => {
        console.error("[AgentTicketDetailPage/load]", error);
        if (active) setLoadError(true);
      });
    return () => {
      active = false;
    };
  }, [ticketId]);
  if (loadError)
    return (
      <EmptyState
        title="Ticket not found"
        detail="This ticket may have been removed, or the link is incorrect."
      />
    );
  if (!ticket) return <LoadingSkeleton />;
  const update = async (patch: Partial<Ticket>) =>
    setTicket(await ticketService.updateTicket(ticket.id, patch));
  const transition = async (status: TicketStatus) => {
    await update({ status });
    setDialog(null);
    setNotice(`Ticket marked ${humanize(status)}.`);
  };
  /** Corrections are the project's audit surface — record the agent's reason on the
      ticket's own event trail so it is visible, not silently dropped. */
  const recordCorrection = (field: string, value: string, reason: string) => {
    const event: TicketEvent = {
      id: crypto.randomUUID(),
      label: `${field} corrected`,
      detail: `${CURRENT_AGENT} changed ${field.toLowerCase()} to “${humanize(value)}” — ${reason}`,
      at: new Date().toISOString(),
      customerVisible: false,
    };
    return { events: [...ticket.events, event] };
  };
  return (
    <>
      <Link className="back-link" to="/agent/tickets">
        <ArrowLeft />
        Back to queue
      </Link>
      <PageHeader
        eyebrow={ticket.id}
        title={ticket.subject}
        description={`${ticket.customerName} · Created ${formatDate(ticket.createdAt)}`}
        actions={
          <div className="ticket-nav">
            <button
              className="icon-btn"
              disabled={!neighbours.previous}
              onClick={() => navigate(`/agent/tickets/${neighbours.previous}`)}
            >
              <ChevronLeft />
              <span className="sr-only">Previous ticket</span>
            </button>
            <button
              className="icon-btn"
              disabled={!neighbours.next}
              onClick={() => navigate(`/agent/tickets/${neighbours.next}`)}
            >
              <ChevronRight />
              <span className="sr-only">Next ticket</span>
            </button>
          </div>
        }
      />
      {notice && (
        <div className="success-alert">
          <CheckCircle2 />
          {notice}
        </div>
      )}
      <div className="ticket-command">
        <div className="badge-row">
          <StatusBadge value={ticket.status} />
          <PriorityBadge value={ticket.priority.value} />
          <span className="queue-label">{ticket.assignedQueue}</span>
        </div>
        <div className="command-actions">
          <button
            className="btn secondary small"
            onClick={() =>
              update({ assignedAgent: CURRENT_AGENT, status: "assigned" })
            }
          >
            <UserCheck />
            Assign to me
          </button>
          <button className="btn secondary small">Reassign</button>
          <button
            className="btn warning small"
            onClick={() => setDialog("escalate")}
          >
            <AlertTriangle />
            Escalate
          </button>
          <button
            className="btn success small"
            onClick={() => setDialog("resolve")}
          >
            Resolve
          </button>
          <button
            className="btn ghost small"
            onClick={() => setDialog("close")}
          >
            Close
          </button>
        </div>
      </div>
      <div className="agent-detail-grid">
        <main className="stack">
          <section className="card">
            <div className="section-title">
              <MessageSquareText />
              <div>
                <span className="eyebrow">Customer context</span>
                <h2>Original customer message</h2>
              </div>
            </div>
            <div className="customer-strip">
              <div className="avatar">
                {ticket.customerName
                  .split(" ")
                  .map((x) => x[0])
                  .join("")}
              </div>
              <div>
                <strong>{ticket.customerName}</strong>
                <span>
                  {ticket.customerId} · Preferred response:{" "}
                  {humanize(ticket.preferredResponseLanguage)}
                </span>
              </div>
            </div>
            <h3>{ticket.subject}</h3>
            <p className="original-message">{ticket.message}</p>
            <div className="meta-grid">
              <div>
                <span>Detected language</span>
                <LanguageBadge value={ticket.language} />
              </div>
              <div>
                <span>Submitted</span>
                <strong>{formatDate(ticket.createdAt)}</strong>
              </div>
              <div>
                <span>Assigned agent</span>
                <strong>{ticket.assignedAgent || "Unassigned"}</strong>
              </div>
              <div>
                <span>Queue</span>
                <strong>{ticket.assignedQueue}</strong>
              </div>
            </div>
          </section>
          <ImageEvidencePanel ticket={ticket} />
          <section className="card">
            <span className="eyebrow">Complete audit trail</span>
            <h2>Ticket activity</h2>
            <TicketTimeline events={ticket.events} />
          </section>
          <InternalNotes
            initial={ticket.notes}
            onAdd={(text) => ticketService.addInternalNote(ticket.id, text)}
          />
          <ResponseEditor
            ticket={ticket}
            onApproved={(text) => {
              update({
                approvedResponse: {
                  text,
                  approvedBy: CURRENT_AGENT,
                  approvedAt: new Date().toISOString(),
                },
                draft: { ...ticket.draft, text, status: "approved" },
              });
              setNotice("Response approved and made customer-visible.");
            }}
          />
        </main>
        <aside className="stack sticky-analysis">
          <div className="analysis-heading">
            <span className="eyebrow">Advisory analysis</span>
            <h2>AI review</h2>
            <p>Accept or correct each prediction.</p>
          </div>
          <PredictionCard
            title="Category"
            prediction={ticket.category}
            options={[...TICKET_CATEGORIES]}
            onSave={(value, reason) =>
              update({
                category: { ...ticket.category, value },
                ...recordCorrection("Category", value, reason),
              })
            }
          />
          <PredictionCard
            title="Priority"
            prediction={ticket.priority}
            options={TICKET_PRIORITIES}
            criticalReason={
              ticket.priority.value === "critical"
                ? "Security-sensitive category and explicit unauthorised transaction signal. Sentiment was not used alone."
                : undefined
            }
            onSave={(value, reason) =>
              update({
                priority: { ...ticket.priority, value },
                ...recordCorrection("Priority", value, reason),
              })
            }
          />
          <PredictionCard
            title="Sentiment"
            prediction={ticket.sentiment}
            options={TICKET_SENTIMENTS}
            onSave={(value, reason) =>
              update({
                sentiment: { ...ticket.sentiment, value },
                ...recordCorrection("Sentiment", value, reason),
              })
            }
          />
          <section className="card compact-card">
            <h3>Current classification</h3>
            <div className="classification-summary">
              <div>
                <span>Priority</span>
                <PriorityBadge value={ticket.priority.value} />
              </div>
              <div>
                <span>Sentiment</span>
                <SentimentBadge value={ticket.sentiment.value} />
              </div>
            </div>
          </section>
        </aside>
      </div>
      {(["escalate", "resolve", "close"] as const).map((type) => (
        <ConfirmationDialog
          key={type}
          open={dialog === type}
          title={`${humanize(type)} this ticket?`}
          description={
            type === "escalate"
              ? "An administrator and specialist queue will be notified in this mock workspace."
              : `This will change the customer-visible status to ${type}d.`
          }
          confirmLabel={humanize(type)}
          danger={type === "close"}
          onCancel={() => setDialog(null)}
          onConfirm={() =>
            transition(
              type === "escalate"
                ? "escalated"
                : type === "resolve"
                  ? "resolved"
                  : "closed",
            )
          }
        />
      ))}
    </>
  );
}
