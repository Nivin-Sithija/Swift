import { createContext, useContext, useState, type ReactNode } from "react";
type UiLanguage = "en" | "si" | "ta";
const labels = {
  en: { submit: "Submit ticket", tickets: "My tickets", dashboard: "Dashboard", queue: "Ticket queue", logout: "Log out" },
  si: { submit: "ටිකට්පතක් යොමු කරන්න", tickets: "මගේ ටිකට්පත්", dashboard: "උපකරණ පුවරුව", queue: "ටිකට් පෝලිම", logout: "ඉවත් වන්න" },
  ta: { submit: "கோரிக்கையை சமர்ப்பிக்கவும்", tickets: "எனது கோரிக்கைகள்", dashboard: "முகப்புப் பலகை", queue: "கோரிக்கை வரிசை", logout: "வெளியேறு" },
};
const LanguageContext = createContext<{ language: UiLanguage; setLanguage: (v: UiLanguage) => void; t: typeof labels.en } | null>(null);
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setState] = useState<UiLanguage>(() => (localStorage.getItem("swift-language") as UiLanguage) || "en");
  const setLanguage = (value: UiLanguage) => {
    localStorage.setItem("swift-language", value);
    setState(value);
  };
  return <LanguageContext.Provider value={{ language, setLanguage, t: labels[language] }}>{children}</LanguageContext.Provider>;
}
export const useLanguage = () => {
  const value = useContext(LanguageContext);
  if (!value) throw new Error("useLanguage must be used within LanguageProvider");
  return value;
};
