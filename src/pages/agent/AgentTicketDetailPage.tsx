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
  LanguageBadge,
  LoadingSkeleton,
  PriorityBadge,
  SentimentBadge,
  StatusBadge,
  TicketTimeline,
  humanize,
} from "../../components/tickets/TicketComponents";
import { mockTicketService } from "../../services/ticketService";
import type { Ticket, TicketStatus } from "../../types";
import { formatDate } from "../../lib/utils";
export function AgentTicketDetailPage() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [dialog, setDialog] = useState<"escalate" | "resolve" | "close" | null>(
    null,
  );
  const [notice, setNotice] = useState("");
  useEffect(() => {
    mockTicketService.getTicket(ticketId || "").then(setTicket);
  }, [ticketId]);
  if (!ticket) return <LoadingSkeleton />;
  const update = async (patch: Partial<Ticket>) =>
    setTicket(await mockTicketService.updateTicket(ticket.id, patch));
  const transition = async (status: TicketStatus) => {
    await update({ status });
    setDialog(null);
    setNotice(`Ticket marked ${humanize(status)}.`);
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
              onClick={() => navigate("/agent/tickets/SW-2026-1041")}
            >
              <ChevronLeft />
              <span className="sr-only">Previous ticket</span>
            </button>
            <button
              className="icon-btn"
              onClick={() => navigate("/agent/tickets/SW-2026-1040")}
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
              update({ assignedAgent: "Anika Fernando", status: "assigned" })
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
            onAdd={async (text) => {
              await mockTicketService.addInternalNote(ticket.id, text);
            }}
          />
        <ResponseEditor
          ticket={ticket}
          onApproved={(text) => {
            update({
              approvedResponse: {
                text,
                approvedBy: "Anika Fernando",
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
            options={[
              "card_payment_wrong_exchange_rate",
              "cash_withdrawal",
              "cash_withdrawal_not_received",
              "pending_transfer",
              "cash_transfer",
              "cash_withdrawal",
            ]}
            onSave={(value) =>
              update({ category: { ...ticket.category, value } })
            }
          />
          <PredictionCard
            title="Priority"
            prediction={ticket.priority}
            options={["low", "medium", "high", "critical"]}
            criticalReason={
              ticket.priority.value === "critical"
                ? "Security-sensitive category and explicit unauthorised transaction signal. Sentiment was not used alone."
                : undefined
            }
            onSave={(value) =>
              update({ priority: { ...ticket.priority, value } })
            }
          />
          <PredictionCard
            title="Sentiment"
            prediction={ticket.sentiment}
            options={["positive", "neutral", "negative"]}
            onSave={(value) =>
              update({ sentiment: { ...ticket.sentiment, value } })
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
              ? "A supervisor and specialist queue will be notified in this mock workspace."
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
