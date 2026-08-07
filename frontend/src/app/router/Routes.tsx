import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider";
import type { UserRole } from "../../types";
import { AdministratorLayout, AgentLayout, CustomerLayout } from "../../components/layout/Layouts";
import { LoginPage } from "../../pages/LoginPage";
import { RegisterPage } from "../../pages/RegisterPage";
import { SubmitTicketPage } from "../../pages/customer/SubmitTicketPage";
import { CustomerTicketsPage } from "../../pages/customer/CustomerTicketsPage";
import { CustomerTicketDetailPage } from "../../pages/customer/CustomerTicketDetailPage";
import { AgentDashboardPage } from "../../pages/agent/AgentDashboardPage";
import { AgentQueuePage } from "../../pages/agent/AgentQueuePage";
import { AgentTicketDetailPage } from "../../pages/agent/AgentTicketDetailPage";
import { AgentReportsPage } from "../../pages/agent/AgentReportsPage";
import { AgentSettingsPage } from "../../pages/agent/AgentSettingsPage";
import { NotFoundPage } from "../../pages/UtilityPages";
import { AdminDashboardPage } from "../../pages/admin/AdminDashboardPage";
import { AdminAuditPage, AdminQueuesPage, AdminSettingsPage, AdminUsersPage } from "../../pages/admin/AdminManagementPages";

const homeForRole = (role: UserRole) =>
  role === "administrator" ? "/admin/dashboard" : role === "agent" ? "/agent/dashboard" : "/customer/submit";

function ProtectedRoute({ role }: { role: UserRole }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user)
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (user.role !== role)
    return (
      <Navigate
        to={homeForRole(user.role)}
        replace
      />
    );
  return <Outlet />;
}
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute role="customer" />}>
        <Route element={<CustomerLayout />}>
          <Route path="/customer/submit" element={<SubmitTicketPage />} />
          <Route path="/customer/tickets" element={<CustomerTicketsPage />} />
          <Route
            path="/customer/tickets/:ticketId"
            element={<CustomerTicketDetailPage />}
          />
        </Route>
      </Route>
      <Route element={<ProtectedRoute role="agent" />}>
        <Route element={<AgentLayout />}>
          <Route path="/agent/dashboard" element={<AgentDashboardPage />} />
          <Route path="/agent/tickets" element={<AgentQueuePage />} />
          <Route
            path="/agent/tickets/:ticketId"
            element={<AgentTicketDetailPage />}
          />
          <Route
            path="/agent/high-priority"
            element={<AgentQueuePage mode="high" />}
          />
          <Route
            path="/agent/escalated"
            element={<AgentQueuePage mode="escalated" />}
          />
          <Route
            path="/agent/resolved"
            element={<AgentQueuePage mode="resolved" />}
          />
          <Route
            path="/agent/reports"
            element={<AgentReportsPage />}
          />
          <Route
            path="/agent/settings"
            element={<AgentSettingsPage />}
          />
        </Route>
      </Route>
      <Route element={<ProtectedRoute role="administrator" />}>
        <Route element={<AdministratorLayout />}>
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/queues" element={<AdminQueuesPage />} />
          <Route path="/admin/audit" element={<AdminAuditPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
        </Route>
      </Route>
      <Route path="/not-found" element={<NotFoundPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
