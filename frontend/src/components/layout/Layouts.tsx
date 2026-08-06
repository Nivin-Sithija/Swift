import {
  Bell,
  ChevronDown,
  CircleCheckBig,
  Gauge,
  LifeBuoy,
  LogOut,
  Menu,
  Search,
  Settings,
  ShieldAlert,
  Ticket,
  X,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/providers/AuthProvider";
import { useLanguage } from "../../app/providers/LanguageProvider";
import { LanguageSelector, Logo, ThemeSwitcher } from "../common/Controls";
import { TopNav } from "../ui/TopNav";
import { Avatar } from "../ui/Avatar";
import { Input } from "../ui/Input";
import { IconButton } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { cn } from "../../lib/utils";
import { ticketService } from "../../services/serviceSelector";
import type { DashboardMetrics } from "../../types";

function ProfileMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const container = useRef<HTMLDivElement>(null);
  // A dropdown that only closes via its own trigger traps the user behind it.
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!container.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);
  return (
    <div className="relative" ref={container}>
      <button
        className="flex items-center gap-2 rounded-md py-1 pl-1 pr-1.5 hover:bg-surface-hover"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <Avatar name={user?.name ?? ""} size={30} />
        <span className="hidden text-left leading-tight sm:inline-block">
          <span className="block text-sm font-semibold text-text-primary">
            {user?.name}
          </span>
          <span className="block text-xs text-text-muted">
            {user?.role === "agent" ? "Support agent" : "Customer"}
          </span>
        </span>
        <ChevronDown size={14} className="shrink-0 text-text-muted" />
      </button>
      {open ? (
        <div className="absolute right-0 top-full z-30 mt-2 min-w-[170px] rounded-md border border-border-subtle bg-surface-card p-1 shadow-sm">
          <button
            className="flex w-full items-center gap-2 rounded-sm px-2.5 py-2 text-sm text-text-primary hover:bg-surface-hover"
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
          >
            <LogOut size={16} /> Log out
          </button>
        </div>
      ) : null}
    </div>
  );
}
export function CustomerLayout() {
  const { t } = useLanguage();
  return (
    <div className="flex min-h-screen flex-col">
      <TopNav
        className="sticky top-0 z-20"
        logo={
          <Link to="/customer/submit">
            <Logo />
          </Link>
        }
        items={[
          { to: "/customer/submit", label: t.submit },
          { to: "/customer/tickets", label: t.tickets },
        ]}
        right={
          <>
            <LanguageSelector />
            <ThemeSwitcher />
            <ProfileMenu />
          </>
        }
      />
      <main className="page">
        <Outlet />
      </main>
      <footer className="footer">
        <span>Swift Support prototype</span>
        <span>Never share passwords or PINs in a ticket.</span>
      </footer>
    </div>
  );
}
const workspaceLinks: Array<{
  to: string;
  label: string;
  icon: LucideIcon;
  count?: keyof DashboardMetrics;
}> = [
  { to: "/agent/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/agent/tickets", label: "Ticket Queue", icon: Ticket },
  {
    to: "/agent/high-priority",
    label: "High Priority",
    icon: ShieldAlert,
    count: "highPriority",
  },
  {
    to: "/agent/escalated",
    label: "Escalated",
    icon: LifeBuoy,
    count: "escalated",
  },
  { to: "/agent/resolved", label: "Resolved", icon: CircleCheckBig },
  { to: "/agent/reports", label: "Reports", icon: Gauge },
];
function SidebarLink({
  to,
  label,
  icon: Icon,
  badge,
  onClick,
}: {
  to: string;
  label: string;
  icon: LucideIcon;
  badge?: string;
  onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors duration-[var(--duration-fast)]",
          isActive
            ? "bg-primary-subtle text-primary-text"
            : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
        )
      }
    >
      <Icon size={17} className="shrink-0" />
      <span className="flex-1">{label}</span>
      {badge ? <Badge tone="error">{badge}</Badge> : null}
    </NavLink>
  );
}
export function AgentLayout() {
  const [sidebar, setSidebar] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  // Sidebar counts have to come from the same source as the dashboard, or they drift.
  useEffect(() => {
    let active = true;
    ticketService
      .getDashboardMetrics()
      .then((next) => active && setMetrics(next))
      .catch((error) => console.error("[AgentLayout/metrics]", error));
    return () => {
      active = false;
    };
  }, []);
  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-[248px] shrink-0 flex-col border-r border-border-subtle bg-surface-sunken transition-transform duration-200 md:sticky md:top-0 md:h-screen md:translate-x-0",
          sidebar ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex items-center justify-between border-b border-border-subtle px-3 py-3.5">
          <Logo />
          <IconButton
            className="md:hidden"
            icon={X}
            aria-label="Close menu"
            onClick={() => setSidebar(false)}
          />
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
          <span className="mb-1 px-2.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
            Workspace
          </span>
          {workspaceLinks.map(({ count, ...link }) => (
            <SidebarLink
              key={link.to}
              {...link}
              badge={
                count && metrics?.[count] ? String(metrics[count]) : undefined
              }
              onClick={() => setSidebar(false)}
            />
          ))}
        </nav>
        <div className="flex flex-col gap-0.5 border-t border-border-subtle p-3">
          <SidebarLink
            to="/agent/settings"
            label="Settings"
            icon={Settings}
            onClick={() => setSidebar(false)}
          />
          <div className="mt-2 flex gap-2.5 rounded-md bg-surface-hover px-2.5 py-2.5">
            <ShieldAlert
              size={16}
              className="mt-0.5 shrink-0 text-primary-solid"
            />
            <span className="flex flex-col">
              <strong className="text-xs font-semibold text-text-primary">
                Secure workspace
              </strong>
              <small className="text-xs text-text-muted">
                Human approval required
              </small>
            </span>
          </div>
        </div>
      </aside>
      <div className="agent-main flex min-w-0 flex-1 flex-col">
        <header className="agent-top">
          <IconButton
            className="menu-button"
            icon={Menu}
            aria-label="Open menu"
            onClick={() => setSidebar(true)}
          />
          <Input
            icon={Search}
            placeholder="Search ID, customer or subject…"
            aria-label="Global search"
            className="flex-1"
          />
          <div className="nav-tools">
            <span className="relative">
              <IconButton icon={Bell} aria-label="3 notifications" />
              <span
                className="absolute -right-1 -top-1 flex h-[18px] w-[18px] items-center justify-center rounded-full bg-error-solid text-[10px] font-semibold text-text-inverse"
                aria-hidden="true"
              >
                3
              </span>
            </span>
            <LanguageSelector />
            <ThemeSwitcher />
            <ProfileMenu />
          </div>
        </header>
        <main className="agent-page">
          <Outlet />
        </main>
      </div>
      {sidebar ? (
        <button
          className="fixed inset-0 z-30 bg-surface-overlay md:hidden"
          onClick={() => setSidebar(false)}
          aria-label="Close navigation"
        />
      ) : null}
    </div>
  );
}
export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}
