import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider";
import type { UserRole } from "../../types";
import { AgentLayout, CustomerLayout } from "../../components/layout/Layouts";
import { LoginPage } from "../../pages/LoginPage";
import { RegisterPage } from "../../pages/RegisterPage";
import { SubmitTicketPage } from "../../pages/customer/SubmitTicketPage";
import { CustomerTicketsPage } from "../../pages/customer/CustomerTicketsPage";
import { CustomerTicketDetailPage } from "../../pages/customer/CustomerTicketDetailPage";
import { AgentDashboardPage } from "../../pages/agent/AgentDashboardPage";
import { AgentQueuePage } from "../../pages/agent/AgentQueuePage";
import { AgentTicketDetailPage } from "../../pages/agent/AgentTicketDetailPage";
import { NotFoundPage, PlaceholderPage } from "../../pages/UtilityPages";

function ProtectedRoute({ role }: { role: UserRole }) {
  const { user } = useAuth();
  const location = useLocation();
  if (!user)
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (user.role !== role)
    return (
      <Navigate
        to={user.role === "agent" ? "/agent/dashboard" : "/customer/submit"}
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
            element={<PlaceholderPage title="Reports" />}
          />
          <Route
            path="/agent/settings"
            element={<PlaceholderPage title="Settings" />}
          />
        </Route>
      </Route>
      <Route path="/not-found" element={<NotFoundPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
