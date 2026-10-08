import { AlertTriangle, CheckCircle2, UserRoundPlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PageHeader } from "../../components/layout/Layouts";
import {
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  Pagination,
  TicketCards,
  TicketFilters,
  TicketTable,
  TicketTableSkeleton,
} from "../../components/tickets/TicketComponents";
import { filterTickets, isTicketSort, sortTickets, type TicketSort } from "../../lib/utils";
import { ticketService } from "../../services/serviceSelector";
import type { Ticket } from "../../types";
import { EMPTY_FILTERS } from "../../lib/constants";
import { useLanguage } from "../../app/providers/LanguageProvider";
import { useAuth } from "../../app/providers/AuthProvider";
import { loadAgentPreferences } from "../../lib/agentPreferences";
import {
  canAssignTicket,
  canChangeTicketStatus,
} from "../../lib/ticketActions";
export function AgentQueuePage({
  mode = "all",
}: {
  mode?: "all" | "high" | "escalated" | "resolved";
}) {
  const { tr } = useLanguage();
  const { user } = useAuth();
  const [preferences] = useState(loadAgentPreferences);
  const pageSize = Number(preferences.pageSize);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [bulkSaving, setBulkSaving] = useState(false);
  const [bulkError, setBulkError] = useState("");
  const [notice, setNotice] = useState("");
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedSort = searchParams.get("sort");
  const sort: TicketSort = isTicketSort(requestedSort) ? requestedSort : "urgency";
  const setSort = (newSort: TicketSort) => {
    setPage(1);
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("sort", newSort);
        return next;
      },
      { replace: true },
    );
  };
  const load = () => {
    setLoading(true);
    setError(false);
    ticketService
      .getTickets()
      .then(setTickets)
      .catch((cause) => {
        console.error("[AgentQueuePage/load]", cause);
        setError(true);
      })
      .finally(() => setLoading(false));
  };
  useEffect(load, []);
  const scoped = useMemo(
    () =>
      tickets.filter((t) =>
        mode === "high"
          ? ["high", "critical"].includes(t.priority.value) ||
            t.category.value.includes("fraud")
          : mode === "escalated"
            ? t.status === "escalated"
            : mode === "resolved"
              ? ["resolved", "closed"].includes(t.status)
              : true,
      ),
    [tickets, mode],
  );
  const filtered = useMemo(
    () => sortTickets(filterTickets(scoped, filters), sort, now),
    [scoped, filters, sort, now],
  );
  const shown = filtered.slice((page - 1) * pageSize, page * pageSize);
  const eligible = (action: "assign" | "escalate") =>
    tickets.filter(
      (ticket) =>
        selected.includes(ticket.id) &&
        (action === "assign"
          ? canAssignTicket(ticket.status) &&
            ticket.assignedAgent !== user?.name
          : canChangeTicketStatus(ticket.status, "escalated")),
    );
  const applyBulk = async (action: "assign" | "escalate") => {
    if (bulkSaving) return;
    setBulkSaving(true);
    setNotice("");
    setBulkError("");
    const targets = eligible(action);
    const results = await Promise.allSettled(
      targets.map((ticket) =>
        ticketService.updateTicket(
          ticket.id,
          action === "assign"
            ? { assignedAgent: user?.name || "Current agent" }
            : { status: "escalated" },
        ),
      ),
    );
    const updated = results.flatMap((result) =>
      result.status === "fulfilled" ? [result.value] : [],
    );
    setTickets((current) =>
      current.map(
        (ticket) => updated.find((item) => item.id === ticket.id) || ticket,
      ),
    );
    setSelected((current) =>
      current.filter((id) => !updated.some((ticket) => ticket.id === id)),
    );
    if (updated.length)
      setNotice(
        `${updated.length} tickets ${action === "assign" ? "assigned to you" : "escalated"}.`,
      );
    if (updated.length < targets.length)
      setBulkError(
        "Some tickets could not be updated. They remain selected; please retry.",
      );
    setBulkSaving(false);
  };
  const title =
    mode === "high"
      ? "High-priority review"
      : mode === "escalated"
        ? "Escalated tickets"
        : mode === "resolved"
          ? "Resolved tickets"
          : "Ticket queue";
  return (
    <>
      <PageHeader
        eyebrow={tr("Support operations")}
        title={tr(title)}
        description={`${filtered.length} tickets · ${sort === "urgency" ? "Urgency combines severity, sentiment, intent and waiting time; updates every 30 seconds." : "Advisory predictions require agent judgement."}`}
        actions={
          <select
            aria-label="Sort tickets"
            value={sort}
            onChange={(e) => setSort(e.target.value as TicketSort)}
          >
            <option value="urgency">{tr("Dynamic urgency")}</option>
            <option value="priority">{tr("Priority first")}</option>
            <option value="newest">{tr("Newest")}</option>
            <option value="confidence">{tr("Lowest confidence")}</option>
            <option value="waiting">{tr("Longest waiting")}</option>
          </select>
        }
      />
      {bulkError && (
        <div role="alert" className="error-alert">
          {bulkError}
        </div>
      )}
      {notice && (
        <div className="success-alert">
          <CheckCircle2 />
          {notice}
          <button onClick={() => setNotice("")}>Dismiss</button>
        </div>
      )}
      <div
        className={`card list-card${preferences.compactQueue ? " compact-queue" : ""}`}
      >
        <TicketFilters
          filters={filters}
          onChange={(p) => { setPage(1); setFilters((v) => ({ ...v, ...p })); }}
          onClear={() => { setPage(1); setFilters(EMPTY_FILTERS); }}
        />
        {selected.length > 0 && (
          <div className="bulk-bar">
            <strong>{selected.length} selected</strong>
            <button
              className="btn small"
              disabled={bulkSaving || eligible("assign").length === 0}
              onClick={() => applyBulk("assign")}
            >
              <UserRoundPlus />
              {tr("Assign to me")}
            </button>
            <button
              className="btn secondary small"
              disabled={bulkSaving || eligible("escalate").length === 0}
              onClick={() => applyBulk("escalate")}
            >
              <AlertTriangle />
              {tr("Escalate")}
            </button>
            <button className="link-button" onClick={() => setSelected([])}>
              Clear selection
            </button>
          </div>
        )}
        {loading ? (
          <>
            <div className="desktop-only">
              <TicketTableSkeleton agent rows={8} />
            </div>
            <div className="mobile-list">
              <LoadingSkeleton />
            </div>
          </>
        ) : error ? (
          <ErrorState retry={load} />
        ) : shown.length === 0 ? (
          <EmptyState detail="No tickets match this queue and filter combination." />
        ) : (
          <>
            <div className="desktop-only">
              <TicketTable
                tickets={shown}
                urgencyNow={now}
                agent
                selected={selected}
                onSelect={(id) =>
                  setSelected((v) =>
                    v.includes(id) ? v.filter((x) => x !== id) : [...v, id],
                  )
                }
              />
            </div>
            <div className="mobile-list">
              <TicketCards tickets={shown} agent urgencyNow={now} />
            </div>
            <div className="table-footer">
              <span>
                Showing {shown.length} of {filtered.length} tickets
              </span>
              <Pagination
                page={page}
                pages={Math.max(1, Math.ceil(filtered.length / pageSize))}
                onChange={setPage}
              />
            </div>
          </>
        )}
      </div>
    </>
  );
}
