import { Activity, KeyRound, ListTree, ScrollText, ShieldCheck, Ticket, UserCog, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../../components/layout/Layouts";
import { ErrorState, LoadingSkeleton, TableLoadingRows } from "../../components/tickets/TicketComponents";
import { Badge } from "../../components/ui/Badge";
import { ticketService } from "../../services/serviceSelector";
import type { AdminDashboardMetrics } from "../../types";
import { delay, formatDate } from "../../lib/utils";

const DASHBOARD_LOADING_FLOOR_MS = 650;

export function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<AdminDashboardMetrics | null>(null);
  const [error, setError] = useState(false);
  const load = () => {
    setError(false);
    Promise.all([
      ticketService.getAdminDashboard(),
      delay(DASHBOARD_LOADING_FLOOR_MS),
    ]).then(([next]) => setMetrics(next)).catch((cause) => {
      console.error("[AdminDashboardPage/load]", cause);
      setError(true);
    });
  };
  useEffect(load, []);
  if (error) return <ErrorState retry={load} />;
  if (!metrics) return <><PageHeader eyebrow="System governance" title="Administrator overview" description="Loading current system totals…"/><LoadingSkeleton/><section className="card list-card"><div className="table-wrap"><table><thead><tr><th>User</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th></tr></thead><TableLoadingRows columns={5}/></table></div></section></>;
  const cards = [
    ["Customers", metrics.customers, Users, "primary"],
    ["Support agents", metrics.agents, UserCog, "success"],
    ["Administrators", metrics.administrators, ShieldCheck, "warning"],
    ["Active sessions", metrics.activeSessions, KeyRound, "neutral"],
    ["Open tickets", metrics.openTickets, Ticket, "primary"],
    ["Support queues", metrics.supportQueues, ListTree, "neutral"],
    ["Audit events", metrics.auditEvents, ScrollText, "neutral"],
  ] as const;
  return (
    <>
      <PageHeader
        eyebrow="System governance"
        title="Administrator overview"
        description="Manage access, monitor system activity, and govern the support operation."
        actions={<Link className="btn" to="/admin/users"><UserCog /> Manage users</Link>}
      />
      <div className="metric-grid">
        {cards.map(([label, value, Icon, tone]) => (
          <article className="metric-card" key={label}>
            <span className={`metric-icon tone-${tone}`}><Icon /></span>
            <div><span>{label}</span><strong>{value}</strong><small>Current system total</small></div>
          </article>
        ))}
      </div>
      <div className="chart-grid">
        <section className="card" style={{ gridColumn: "span 2" }}>
          <div className="card-heading">
            <div><span className="eyebrow">Access governance</span><h2>Recently created accounts</h2></div>
            <Link className="link-button" to="/admin/users">View all users</Link>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>User</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>{metrics.recentUsers.map((user) => (
                <tr key={user.id}>
                  <td><strong>{user.name}</strong></td><td>{user.email}</td>
                  <td><Badge tone={user.role === "administrator" ? "warning" : user.role === "agent" ? "info" : "neutral"}>{user.role}</Badge></td>
                  <td><Badge tone={user.isActive ? "success" : "error"}>{user.isActive ? "Active" : "Disabled"}</Badge></td>
                  <td>{formatDate(user.createdAt)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </section>
        <section className="card">
          <span className="eyebrow">Security posture</span><h2>Administrative controls</h2>
          <div className="stack">
            <Link className="btn secondary" to="/admin/audit"><Activity /> Review audit activity</Link>
            <Link className="btn secondary" to="/admin/queues"><ListTree /> Configure queues</Link>
            <Link className="btn secondary" to="/admin/settings"><ShieldCheck /> Security settings</Link>
          </div>
        </section>
      </div>
    </>
  );
}
