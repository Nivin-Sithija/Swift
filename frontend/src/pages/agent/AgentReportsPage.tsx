import { Download, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "../../components/layout/Layouts";
import {
  EmptyState,
  ErrorState,
  LoadingSkeleton,
  PriorityBadge,
  StatusBadge,
  humanize,
} from "../../components/tickets/TicketComponents";
import { ticketService } from "../../services/serviceSelector";
import type { Ticket } from "../../types";

type Period = "7" | "30" | "all";

const csvCell = (value: string | number) =>
  `"${String(value).replaceAll('"', '""')}"`;

export function AgentReportsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [period, setPeriod] = useState<Period>("30");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [reportTime] = useState(() => Date.now());

  const load = () => {
    setLoading(true);
    setError(false);
    ticketService
      .getTickets()
      .then(setTickets)
      .catch((cause) => {
        console.error("[AgentReportsPage/load]", cause);
        setError(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const scoped = useMemo(() => {
    if (period === "all") return tickets;
    const cutoff = reportTime - Number(period) * 86_400_000;
    return tickets.filter((ticket) => new Date(ticket.createdAt).getTime() >= cutoff);
  }, [period, reportTime, tickets]);

  const summary = useMemo(() => {
    const resolved = scoped.filter((ticket) =>
      ["resolved", "closed"].includes(ticket.status),
    ).length;
    const escalated = scoped.filter((ticket) => ticket.status === "escalated").length;
    const manualReview = scoped.filter((ticket) => ticket.requiresManualReview).length;
    return {
      total: scoped.length,
      resolved,
      escalated,
      manualReview,
      resolutionRate: scoped.length ? Math.round((resolved / scoped.length) * 100) : 0,
    };
  }, [scoped]);

  const categories = useMemo(() => {
    const counts = new Map<string, number>();
    scoped.forEach((ticket) =>
      counts.set(ticket.category.value, (counts.get(ticket.category.value) ?? 0) + 1),
    );
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  }, [scoped]);

  const exportCsv = () => {
    const rows = [
      ["Ticket", "Subject", "Category", "Priority", "Status", "Language", "Created"],
      ...scoped.map((ticket) => [
        ticket.id,
        ticket.subject,
        ticket.category.value,
        ticket.priority.value,
        ticket.status,
        ticket.language,
        ticket.createdAt,
      ]),
    ];
    const blob = new Blob([rows.map((row) => row.map(csvCell).join(",")).join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `swift-support-report-${new Date().toISOString().slice(0, 10)}.csv`;
    anchor.click();
    URL.revokeObjectURL(href);
  };

  return (
    <>
      <PageHeader
        eyebrow="Support intelligence"
        title="Reports"
        description="Operational trends calculated from the tickets currently available to you."
        actions={
          <div className="row">
            <select
              aria-label="Report period"
              value={period}
              onChange={(event) => setPeriod(event.target.value as Period)}
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="all">All time</option>
            </select>
            <button className="btn secondary" onClick={load} disabled={loading}>
              <RefreshCw /> Refresh
            </button>
            <button className="btn" onClick={exportCsv} disabled={!scoped.length}>
              <Download /> Export CSV
            </button>
          </div>
        }
      />
      {loading ? (
        <LoadingSkeleton />
      ) : error ? (
        <ErrorState retry={load} />
      ) : (
        <>
          <div className="metric-grid">
            {[
              ["Tickets received", summary.total],
              ["Resolved", summary.resolved],
              ["Resolution rate", `${summary.resolutionRate}%`],
              ["Escalated", summary.escalated],
              ["Manual review", summary.manualReview],
            ].map(([label, value]) => (
              <article className="metric-card" key={label}>
                <div><span>{label}</span><strong>{value}</strong><small>Selected reporting period</small></div>
              </article>
            ))}
          </div>
          {scoped.length === 0 ? (
            <EmptyState detail="No tickets were created during this reporting period." />
          ) : (
            <div className="chart-grid">
              <section className="card">
                <span className="eyebrow">Demand profile</span>
                <h2>Top categories</h2>
                <div className="bar-chart">
                  {categories.map(([category, count]) => (
                    <div key={category}>
                      <span>{humanize(category)}</span>
                      <div><i style={{ width: `${(count / categories[0][1]) * 100}%` }} /></div>
                      <strong>{count}</strong>
                    </div>
                  ))}
                </div>
              </section>
              <section className="card list-card">
                <span className="eyebrow">Recent activity</span>
                <h2>Latest tickets</h2>
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Ticket</th><th>Priority</th><th>Status</th></tr></thead>
                    <tbody>
                      {scoped.slice(0, 6).map((ticket) => (
                        <tr key={ticket.id}>
                          <td><strong>{ticket.subject}</strong><small>{ticket.id}</small></td>
                          <td><PriorityBadge value={ticket.priority.value} /></td>
                          <td><StatusBadge value={ticket.status} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}
        </>
      )}
    </>
  );
}
