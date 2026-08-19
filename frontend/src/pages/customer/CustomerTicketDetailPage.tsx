import {
  AlertTriangle,
  ArrowLeft,
  ExternalLink,
  Image as ImageIcon,
  LoaderCircle,
  MessageSquareText,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "../../components/layout/Layouts";
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
import type { RagAssistanceResult, Ticket } from "../../types";
import { formatDate } from "../../lib/utils";
export function CustomerTicketDetailPage() {
  const { ticketId } = useParams();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [assistance, setAssistance] = useState<RagAssistanceResult | null>(
    null,
  );
  const [assistanceLoading, setAssistanceLoading] = useState(false);
  const [assistanceError, setAssistanceError] = useState("");
  useEffect(() => {
    let active = true;
    setLoading(true);
    ticketService
      .getTicket(ticketId || "")
      .then((next) => {
        if (active) setTicket(next);
      })
      .catch((error) => {
        console.error("[CustomerTicketDetailPage/load]", error);
        if (active) setTicket(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [ticketId]);
  useEffect(() => {
    if (!ticket) return;
    let active = true;
    setAssistanceLoading(true);
    setAssistanceError("");
    setAssistance(null);
    ticketService
      .getCustomerTicketAssistance(ticket.id)
      .then((result) => {
        if (active) setAssistance(result);
      })
      .catch((error) => {
        if (active)
          setAssistanceError(
            error instanceof Error
              ? error.message
              : "Unable to generate assistance",
          );
      })
      .finally(() => {
        if (active) setAssistanceLoading(false);
      });
    return () => {
      active = false;
    };
  }, [ticket]);
  if (loading) return <LoadingSkeleton />;
  if (!ticket)
    return (
      <EmptyState
        title="Ticket not found"
        detail="This ticket may not exist or is not available to this customer."
      />
    );
  return (
    <>
      <Link className="back-link" to="/customer/submit">
        <ArrowLeft />
        Back to my tickets
      </Link>
      <PageHeader
        eyebrow={ticket.id}
        title={ticket.subject}
        description="Customer-safe ticket view"
        actions={
          <>
            <PriorityBadge value={ticket.priority.value} />
            <StatusBadge value={ticket.status} />
          </>
        }
      />
      <div className="detail-grid">
        <div className="stack">
          <section className="card">
            <div className="section-title">
              <MessageSquareText />
              <div>
                <span className="eyebrow">Original customer message</span>
                <h2>Your message</h2>
              </div>
            </div>
            <p className="original-message">{ticket.message}</p>
            <div className="meta-grid">
              <div>
                <span>Preferred response</span>
                <strong>{humanize(ticket.preferredResponseLanguage)}</strong>
              </div>
              <div>
                <span>Detected language form</span>
                <LanguageBadge value={ticket.language} />
              </div>
              <div>
                <span>Category</span>
                <strong>{humanize(ticket.category.value)}</strong>
              </div>
              <div>
                <span>Sentiment</span>
                <SentimentBadge value={ticket.sentiment.value} />
              </div>
              <div>
                <span>Assigned queue</span>
                <strong>{ticket.assignedQueue}</strong>
              </div>
              <div>
                <span>Created</span>
                <strong>{formatDate(ticket.createdAt)}</strong>
              </div>
            </div>
          </section>
          {ticket.attachment && (
            <section className="card">
              <div className="section-title">
                <ImageIcon />
                <div>
                  <span className="eyebrow">Supplementary evidence</span>
                  <h2>Uploaded image</h2>
                </div>
              </div>
              <img
                className="evidence-image"
                src={ticket.attachment.url}
                alt="Customer uploaded transaction evidence"
              />
              {ticket.imageEvidence.status === "failed" && (
                <div className="warning-box">
                  <AlertTriangle />
                  Image processing failed. Your ticket was still submitted
                  successfully.
                </div>
              )}
            </section>
          )}
          <section className="card rag-draft-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">Approved-source guidance</span>
                <h2>Response for your ticket</h2>
              </div>
              <span className="ai-label">
                <Sparkles /> Customer assistance
              </span>
            </div>
            {assistanceLoading && (
              <div className="inline-loading" role="status">
                <LoaderCircle className="spin" /> Preparing response from
                approved sources…
              </div>
            )}
            {assistanceError && (
              <div className="error-alert" role="alert">
                <AlertTriangle /> {assistanceError}
              </div>
            )}
            {assistance && (
              <div
                className={`rag-result ${assistance.route === "human_escalation" ? "escalated" : "grounded"}`}
              >
                <div className="rag-result-summary">
                  <strong>
                    {assistance.draft
                      ? "Response for your ticket"
                      : "A support agent needs to review this"}
                  </strong>
                  <span>
                    {Math.round(assistance.confidence * 100)}% evidence
                    confidence
                  </span>
                </div>
                {assistance.draft && <p>{assistance.draft}</p>}
                {assistance.escalationReason && (
                  <p>
                    We could not safely provide an automated response:{" "}
                    {humanize(assistance.escalationReason)}.
                  </p>
                )}
                {assistance.citations.length > 0 && (
                  <div className="rag-citations">
                    <h3>Sources</h3>
                    {assistance.citations.map((citation) => (
                      <a
                        key={`${citation.sourceId}-${citation.marker}`}
                        href={citation.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <span>
                          [{citation.marker}] {citation.title}
                        </span>
                        <small>
                          {citation.institution} · reviewed{" "}
                          {citation.reviewDate}
                        </small>
                        <ExternalLink />
                      </a>
                    ))}
                  </div>
                )}
                <small>General policy guidance from approved sources.</small>
              </div>
            )}
          </section>
          {ticket.approvedResponse ? (
            <section className="card approved-response">
              <span className="eyebrow">Approved response</span>
              <h2>Support team response</h2>
              <p>{ticket.approvedResponse.text}</p>
              <small>
                Approved by an authorised support agent ·{" "}
                {formatDate(ticket.approvedResponse.approvedAt)}
              </small>
            </section>
          ) : (
            <section className="card empty-response">
              <MessageSquareText />
              <h2>No approved response yet</h2>
              <p>
                Your support team is reviewing this ticket. Only a
                human-approved response will appear here.
              </p>
            </section>
          )}
        </div>
        <aside className="stack">
          <section className="card">
            <h2>Current status</h2>
            <TicketTimeline events={ticket.events} customerSafe />
          </section>
          <section className="card compact-card">
            <h3>Ticket details</h3>
            <dl>
              <div>
                <dt>Last updated</dt>
                <dd>{formatDate(ticket.updatedAt)}</dd>
              </div>
              <div>
                <dt>Response available</dt>
                <dd>{ticket.approvedResponse ? "Yes" : "Not yet"}</dd>
              </div>
              <div>
                <dt>Image status</dt>
                <dd>{humanize(ticket.imageEvidence.status)}</dd>
              </div>
            </dl>
          </section>
        </aside>
      </div>
    </>
  );
}
