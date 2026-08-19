import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ticketService } from "../../services/serviceSelector";
import type { User, UserRole } from "../../types";
const AuthContext = createContext<{
  user: User | null;
  login: (
    email: string,
    password: string,
    role: UserRole,
    remember?: boolean,
  ) => Promise<User>;
  register: (input: { name: string; email: string; password: string; role: UserRole; preferredLanguage: "english" | "sinhala" | "tamil"; agentCode?: string }) => Promise<void>;
  logout: () => Promise<void>;
  restoring: boolean;
} | null>(null);
export function MockAuthProvider({ children }: { children: ReactNode }) {
  const [storedUser] = useState<User | null>(() => {
    const raw =
      sessionStorage.getItem("swift-session") ||
      localStorage.getItem("swift-session");
    try {
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  });
  const [user, setUser] = useState<User | null>(storedUser);
  const [restoring, setRestoring] = useState(Boolean(storedUser));
  useEffect(() => {
    if (!storedUser) return;
    let active = true;
    ticketService
      .restoreSession(storedUser)
      .then((restored) => {
        if (active) setUser(restored);
      })
      .catch(() => {
        if (!active) return;
        localStorage.removeItem("swift-session");
        sessionStorage.removeItem("swift-session");
        setUser(null);
      })
      .finally(() => active && setRestoring(false));
    return () => { active = false; };
  }, [storedUser]);
  const login = async (
    email: string,
    password: string,
    role: UserRole,
    remember = false,
  ) => {
    const next = await ticketService.login(email, password, role);
    (remember ? localStorage : sessionStorage).setItem(
      "swift-session",
      JSON.stringify(next),
    );
    setUser(next);
    return next;
  };
  const logout = async () => {
    await ticketService.logout();
    localStorage.removeItem("swift-session");
    sessionStorage.removeItem("swift-session");
    setUser(null);
  };
  const register = async (input: { name: string; email: string; password: string; role: UserRole; preferredLanguage: "english" | "sinhala" | "tamil"; agentCode?: string }) => {
    const next = await ticketService.register(input);
    sessionStorage.setItem("swift-session", JSON.stringify(next));
    setUser(next);
  };
  return (
    <AuthContext.Provider value={{ user, login, register, logout, restoring }}>
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used within MockAuthProvider");
  return value;
};
