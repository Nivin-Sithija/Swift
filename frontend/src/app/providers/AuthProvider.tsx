import { createContext, useContext, useState, type ReactNode } from "react";
import { mockTicketService } from "../../services/ticketService";
import type { User, UserRole } from "../../types";
const AuthContext = createContext<{
  user: User | null;
  login: (
    email: string,
    password: string,
    role: UserRole,
    remember?: boolean,
  ) => Promise<void>;
  logout: () => Promise<void>;
} | null>(null);
export function MockAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw =
      sessionStorage.getItem("swift-session") ||
      localStorage.getItem("swift-session");
    try {
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  });
  const login = async (
    email: string,
    password: string,
    role: UserRole,
    remember = false,
  ) => {
    const next = await mockTicketService.login(email, password, role);
    (remember ? localStorage : sessionStorage).setItem(
      "swift-session",
      JSON.stringify(next),
    );
    setUser(next);
  };
  const logout = async () => {
    await mockTicketService.logout();
    localStorage.removeItem("swift-session");
    sessionStorage.removeItem("swift-session");
    setUser(null);
  };
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within MockAuthProvider");
  return value;
};
