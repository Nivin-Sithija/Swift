import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Eye,
  ImageOff,
  LoaderCircle,
} from "lucide-react";
import { Link } from "react-router-dom";
import type { FilterState, Ticket, TicketEvent } from "../../types";
import { cn, confidenceBand, formatDate } from "../../lib/utils";
import {
  SUPPORTED_LANGUAGES,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
} from "../../lib/constants";
import { SearchInput } from "../common/Controls";

export const humanize = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (x) => x.toUpperCase());
export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={cn("badge status", value)}>
      <span className="dot" />
      {humanize(value)}
    </span>
  );
}
export function PriorityBadge({ value }: { value: string }) {
  return (
    <span className={cn("badge priority", value)}>
      {value === "critical" && <AlertTriangle size={13} />} {humanize(value)}
    </span>
  );
}
export function SentimentBadge({ value }: { value: string }) {
  return (
    <span className={cn("badge sentiment", value)}>{humanize(value)}</span>
  );
}
export function LanguageBadge({ value }: { value: string }) {
  return <span className="badge language">{humanize(value)}</span>;
}
export function ConfidenceIndicator({ value }: { value: number }) {
  const band = confidenceBand(value);
  return (
    <div className={cn("confidence", band)}>
      <div className="confidence-row">
        <span>{value}%</span>
        <strong>{humanize(band)}</strong>
      </div>
      <div className="confidence-track">
        <span style={{ width: `${value}%` }} />
      </div>
      {band === "low" && (
        <small>
          <AlertTriangle size={12} /> Manual review required
        </small>
      )}
    </div>
  );
}
export function TicketTimeline({
  events,
  customerSafe = false,
}: {
  events: TicketEvent[];
  customerSafe?: boolean;
}) {
  const visible = customerSafe
    ? events.filter((event) => event.customerVisible)
    : events;
  return (
    <ol className="timeline">
      {visible.map((event, index) => (
        <li
          key={event.id}
          className={index === visible.length - 1 ? "current" : ""}
        >
          <span className="timeline-mark">
            {index < visible.length - 1 ? (
              <CheckCircle2 size={15} />
            ) : (
              <Clock3 size={15} />
            )}
          </span>
          <div>
            <strong>{event.label}</strong>
            <p>{event.detail}</p>
            <time>{formatDate(event.at)}</time>
          </div>
        </li>
      ))}
    </ol>
  );
}
export function TicketFilters({
  filters,
  onChange,
  onClear,
}: {
  filters: FilterState;
  onChange: (patch: Partial<FilterState>) => void;
  onClear: () => void;
}) {
  return (
    <div className="filters">
      <SearchInput
        value={filters.search}
        onChange={(search) => onChange({ search })}
      />
      <select
        aria-label="Status filter"
        value={filters.status}
        onChange={(e) => onChange({ status: e.target.value })}
      >
        <option value="all">All statuses</option>
        {TICKET_STATUSES.map((x) => (
          <option key={x} value={x}>
            {humanize(x)}
          </option>
        ))}
      </select>
      <select
        aria-label="Priority filter"
        value={filters.priority}
        onChange={(e) => onChange({ priority: e.target.value })}
      >
        <option value="all">All priorities</option>
        {TICKET_PRIORITIES.map((x) => (
          <option key={x} value={x}>
            {humanize(x)}
          </option>
        ))}
      </select>
      <select
        aria-label="Language filter"
        value={filters.language}
        onChange={(e) => onChange({ language: e.target.value })}
      >
        <option value="all">All languages</option>
        {SUPPORTED_LANGUAGES.map((x) => (
          <option key={x} value={x}>
            {humanize(x)}
          </option>
        ))}
      </select>
      <button className="btn ghost" onClick={onClear}>
        Clear filters
      </button>
    </div>
  );
}
export function TicketTable({
  tickets,
  agent = false,
  selected = [],
  onSelect,
}: {
  tickets: Ticket[];
  agent?: boolean;
  selected?: string[];
  onSelect?: (id: string) => void;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {agent && (
              <th>
                <span className="sr-only">Select</span>
              </th>
            )}
            <th>Ticket</th>
            {agent && <th>Customer</th>}
            <th>Subject</th>
            <th>Language</th>
            <th>Category</th>
            <th>Priority</th>
            {agent && <th>Sentiment</th>}
            {agent && <th>Confidence</th>}
            <th>Status</th>
            <th>{agent ? "Assigned agent" : "Updated"}</th>
            <th>
              <span className="sr-only">Action</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => (
            <tr
              key={ticket.id}
              className={
                ticket.priority.value === "critical" ? "critical-row" : ""
              }
            >
              {agent && (
                <td>
                  <input
                    type="checkbox"
                    aria-label={`Select ${ticket.id}`}
                    checked={selected.includes(ticket.id)}
                    onChange={() => onSelect?.(ticket.id)}
                  />
                </td>
              )}
              <td>
                <strong>{ticket.id}</strong>
                <small>{formatDate(ticket.createdAt)}</small>
              </td>
              {agent && (
                <td>
                  {ticket.customerName}
                  <small>{ticket.customerId}</small>
                </td>
              )}
              <td>
                <span className="subject">{ticket.subject}</span>
                {ticket.requiresManualReview && (
                  <small className="warning-text">
                    <AlertTriangle size={12} /> Manual review
                  </small>
                )}
              </td>
              <td>
                <LanguageBadge value={ticket.language} />
              </td>
              <td>
                <span className="category">
                  {humanize(ticket.category.value)}
                </span>
              </td>
              <td>
                <PriorityBadge value={ticket.priority.value} />
              </td>
              {agent && (
                <td>
                  <SentimentBadge value={ticket.sentiment.value} />
                </td>
              )}
              {agent && (
                <td>
                  <ConfidenceIndicator value={ticket.category.confidence} />
                </td>
              )}
              <td>
                <StatusBadge value={ticket.status} />
              </td>
              <td>
                {agent
                  ? ticket.assignedAgent || "Unassigned"
                  : formatDate(ticket.updatedAt)}
              </td>
              <td>
                <Link
                  className="icon-btn"
                  aria-label={`Open ${ticket.id}`}
                  to={`${agent ? "/agent" : "/customer"}/tickets/${ticket.id}`}
                >
                  <Eye size={17} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function TicketCards({
  tickets,
  agent = false,
}: {
  tickets: Ticket[];
  agent?: boolean;
}) {
  return (
    <div className="ticket-cards">
      {tickets.map((ticket) => (
        <article className="ticket-card" key={ticket.id}>
          <div className="row spread">
            <strong>{ticket.id}</strong>
            <StatusBadge value={ticket.status} />
          </div>
          <h3>{ticket.subject}</h3>
          <p>{ticket.message}</p>
          <div className="badge-row">
            <PriorityBadge value={ticket.priority.value} />
            <LanguageBadge value={ticket.language} />
          </div>
          <div className="row spread meta">
            <span>{formatDate(ticket.updatedAt)}</span>
            <Link
              className="btn small"
              to={`${agent ? "/agent" : "/customer"}/tickets/${ticket.id}`}
            >
              View
            </Link>
          </div>
        </article>
      ))}
    </div>
  );
}
export function Pagination({
  page,
  pages,
  onChange,
}: {
  page: number;
  pages: number;
  onChange: (page: number) => void;
}) {
  return (
    <nav className="pagination" aria-label="Pagination">
      <button
        className="icon-btn"
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
      >
        <ChevronLeft />
        <span className="sr-only">Previous</span>
      </button>
      <span>
        Page <strong>{page}</strong> of {pages}
      </span>
      <button
        className="icon-btn"
        disabled={page === pages}
        onClick={() => onChange(page + 1)}
      >
        <ChevronRight />
        <span className="sr-only">Next</span>
      </button>
    </nav>
  );
}
export function LoadingSkeleton() {
  return (
    <div className="skeletons" role="status" aria-label="Loading tickets">
      {[1, 2, 3, 4].map((x) => (
        <div className="skeleton" key={x} />
      ))}
    </div>
  );
}
export function EmptyState({
  title = "No tickets found",
  detail = "Try changing your filters or create a new support ticket.",
}: {
  title?: string;
  detail?: string;
}) {
  return (
    <div className="empty">
      <ImageOff />
      <h3>{title}</h3>
      <p>{detail}</p>
    </div>
  );
}
export function ErrorState({ retry }: { retry: () => void }) {
  return (
    <div className="empty error">
      <AlertTriangle />
      <h3>Service temporarily unavailable</h3>
      <p>The mock ticket service could not load this view.</p>
      <button className="btn" onClick={retry}>
        Try again
      </button>
    </div>
  );
}
export function ProcessingStepper({
  current,
  steps,
}: {
  current: number;
  steps: string[];
}) {
  return (
    <ol className="stepper">
      {steps.map((step, index) => (
        <li
          className={cn(
            index < current && "done",
            index === current && "active",
          )}
          key={step}
        >
          {index < current ? (
            <CheckCircle2 />
          ) : index === current ? (
            <LoaderCircle className="spin" />
          ) : (
            <span>{index + 1}</span>
          )}
          <div>
            <strong>{step}</strong>
            <small>
              {index < current
                ? "Complete"
                : index === current
                  ? "In progress"
                  : "Waiting"}
            </small>
          </div>
        </li>
      ))}
    </ol>
  );
}
