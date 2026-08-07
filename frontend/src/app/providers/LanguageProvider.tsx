import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
export type UiLanguage = "en" | "si" | "ta";
const labels = {
  en: {
    submit: "Submit ticket",
    tickets: "My tickets",
    dashboard: "Dashboard",
    queue: "Ticket queue",
    logout: "Log out",
  },
  si: {
    submit: "ටිකට්පතක් යොමු කරන්න",
    tickets: "මගේ ටිකට්පත්",
    dashboard: "උපකරණ පුවරුව",
    queue: "ටිකට් පෝලිම",
    logout: "ඉවත් වන්න",
  },
  ta: {
    submit: "கோரிக்கையை சமர்ப்பிக்கவும்",
    tickets: "எனது கோரிக்கைகள்",
    dashboard: "முகப்புப் பலகை",
    queue: "கோரிக்கை வரிசை",
    logout: "வெளியேறு",
  },
};
const translations: Record<Exclude<UiLanguage, "en">, Record<string, string>> = {
  si: {
    "Interface language": "අතුරුමුහුණත් භාෂාව", "Search tickets…": "ටිකට් සොයන්න…",
    "Search": "සොයන්න", "Clear search": "සෙවීම ඉවත් කරන්න", "Log out": "ඉවත් වන්න",
    "Customer": "පාරිභෝගිකයා", "Support agent": "සහාය නිලධාරියා", "Workspace": "වැඩබිම",
    "Dashboard": "උපකරණ පුවරුව", "Ticket Queue": "ටිකට් පෝලිම", "High Priority": "ඉහළ ප්‍රමුඛතාව",
    "Escalated": "ඉහළට යොමු කළ", "Resolved": "විසඳූ", "Reports": "වාර්තා", "Settings": "සැකසුම්",
    "Secure workspace": "ආරක්ෂිත වැඩබිම", "Human approval required": "මානව අනුමැතිය අවශ්‍යයි",
    "Swift Support prototype": "Swift සහාය මූලාකෘතිය", "Never share passwords or PINs in a ticket.": "ටිකට්පතක මුරපද හෝ PIN කිසිවිටෙක බෙදා නොගන්න.",
    "My tickets": "මගේ ටිකට්පත්", "Submit ticket": "ටිකට්පත යොමු කරන්න", "Customer support": "පාරිභෝගික සහාය",
    "How can we help?": "අපට ඔබට උදව් කළ හැක්කේ කෙසේද?", "Tell us what happened": "සිදු වූ දේ අපට කියන්න",
    "Subject": "මාතෘකාව", "Detailed description": "විස්තරාත්මක විස්තරය", "Preferred response language": "පිළිතුරු භාෂාව",
    "Category selection": "ප්‍රවර්ග තේරීම", "Let the system detect": "පද්ධතියට හඳුනාගැනීමට ඉඩ දෙන්න",
    "Add image evidence": "රූප සාක්ෂි එක් කරන්න", "Optional": "විකල්ප", "Clear": "ඉවත් කරන්න",
    "Submit another ticket": "තවත් ටිකට්පතක් යොමු කරන්න", "View ticket": "ටිකට්පත බලන්න",
    "Before you submit": "යොමු කිරීමට පෙර", "Human review is built in": "මානව සමාලෝචනය ඇතුළත්ය",
    "Support history": "සහාය ඉතිහාසය", "Track requests, status updates, and approved responses.": "ඉල්ලීම්, තත්ත්ව යාවත්කාලීන සහ අනුමත පිළිතුරු නිරීක්ෂණය කරන්න.",
    "All statuses": "සියලු තත්ත්ව", "All priorities": "සියලු ප්‍රමුඛතා", "All languages": "සියලු භාෂා", "Clear filters": "පෙරහන් ඉවත් කරන්න",
    "Ticket": "ටිකට්පත", "Language": "භාෂාව", "Category": "ප්‍රවර්ගය", "Priority": "ප්‍රමුඛතාව",
    "Status": "තත්ත්වය", "Updated": "යාවත්කාලීන කළ", "View": "බලන්න", "Page": "පිටුව", "of": "න්",
    "No tickets found": "ටිකට් හමු නොවීය", "Try again": "නැවත උත්සාහ කරන්න", "Service temporarily unavailable": "සේවාව තාවකාලිකව නොමැත",
    "Welcome to Swift": "Swift වෙත සාදරයෙන් පිළිගනිමු", "Email address": "විද්‍යුත් තැපැල් ලිපිනය", "Password": "මුරපදය",
    "Remember me": "මාව මතක තබාගන්න", "Forgot password?": "මුරපදය අමතකද?", "Sign in securely": "ආරක්ෂිතව පිවිසෙන්න",
    "Good morning": "සුභ උදෑසනක්", "Good afternoon": "සුභ දහවලක්", "Good evening": "සුභ සන්ධ්‍යාවක්",
    "Open queue": "පෝලිම විවෘත කරන්න", "New tickets": "නව ටිකට්", "Assigned to me": "මට පවරා ඇත",
    "Critical": "අතිශය වැදගත්", "Resolved today": "අද විසඳූ", "Low confidence": "අඩු විශ්වාසය",
    "Tickets by category": "ප්‍රවර්ග අනුව ටිකට්", "Multilingual mix": "බහුභාෂා මිශ්‍රණය", "Recent ticket queue": "මෑත ටිකට් පෝලිම",
    "Support operations": "සහාය මෙහෙයුම්", "High-priority review": "ඉහළ ප්‍රමුඛතා සමාලෝචනය", "Escalated tickets": "ඉහළට යොමු කළ ටිකට්",
    "Resolved tickets": "විසඳූ ටිකට්", "Ticket queue": "ටිකට් පෝලිම", "Priority first": "ප්‍රමුඛතාව පළමුව", "Newest": "නවතම",
    "Lowest confidence": "අඩුම විශ්වාසය", "Longest waiting": "වැඩිම කාලයක් බලා සිටින", "Assign to me": "මට පවරන්න", "Escalate": "ඉහළට යොමු කරන්න",
  },
  ta: {
    "Interface language": "இடைமுக மொழி", "Search tickets…": "கோரிக்கைகளைத் தேடுங்கள்…",
    "Search": "தேடல்", "Clear search": "தேடலை அழி", "Log out": "வெளியேறு",
    "Customer": "வாடிக்கையாளர்", "Support agent": "ஆதரவு முகவர்", "Workspace": "பணியிடம்",
    "Dashboard": "முகப்புப் பலகை", "Ticket Queue": "கோரிக்கை வரிசை", "High Priority": "உயர் முன்னுரிமை",
    "Escalated": "மேல்நிலைக்கு அனுப்பப்பட்டது", "Resolved": "தீர்க்கப்பட்டது", "Reports": "அறிக்கைகள்", "Settings": "அமைப்புகள்",
    "Secure workspace": "பாதுகாப்பான பணியிடம்", "Human approval required": "மனித ஒப்புதல் தேவை",
    "Swift Support prototype": "Swift ஆதரவு முன்மாதிரி", "Never share passwords or PINs in a ticket.": "கோரிக்கையில் கடவுச்சொல் அல்லது PIN-ஐ பகிர வேண்டாம்.",
    "My tickets": "எனது கோரிக்கைகள்", "Submit ticket": "கோரிக்கையை சமர்ப்பிக்கவும்", "Customer support": "வாடிக்கையாளர் ஆதரவு",
    "How can we help?": "நாங்கள் எவ்வாறு உதவலாம்?", "Tell us what happened": "என்ன நடந்தது என்று கூறுங்கள்",
    "Subject": "தலைப்பு", "Detailed description": "விரிவான விளக்கம்", "Preferred response language": "விருப்பமான பதில் மொழி",
    "Category selection": "வகைத் தேர்வு", "Let the system detect": "கணினி கண்டறியட்டும்",
    "Add image evidence": "பட ஆதாரத்தைச் சேர்க்கவும்", "Optional": "விருப்பத்தேர்வு", "Clear": "அழி",
    "Submit another ticket": "மற்றொரு கோரிக்கையை சமர்ப்பிக்கவும்", "View ticket": "கோரிக்கையைப் பார்க்கவும்",
    "Before you submit": "சமர்ப்பிக்கும் முன்", "Human review is built in": "மனித மதிப்பாய்வு உள்ளமைக்கப்பட்டுள்ளது",
    "Support history": "ஆதரவு வரலாறு", "Track requests, status updates, and approved responses.": "கோரிக்கைகள், நிலை மாற்றங்கள் மற்றும் ஒப்புதலளிக்கப்பட்ட பதில்களைக் கண்காணிக்கவும்.",
    "All statuses": "அனைத்து நிலைகள்", "All priorities": "அனைத்து முன்னுரிமைகள்", "All languages": "அனைத்து மொழிகள்", "Clear filters": "வடிகட்டிகளை அழி",
    "Ticket": "கோரிக்கை", "Language": "மொழி", "Category": "வகை", "Priority": "முன்னுரிமை", "Status": "நிலை",
    "Updated": "புதுப்பிக்கப்பட்டது", "View": "பார்க்க", "Page": "பக்கம்", "of": "இல்",
    "No tickets found": "கோரிக்கைகள் இல்லை", "Try again": "மீண்டும் முயலவும்", "Service temporarily unavailable": "சேவை தற்காலிகமாக கிடைக்கவில்லை",
    "Welcome to Swift": "Swift-க்கு வரவேற்கிறோம்", "Email address": "மின்னஞ்சல் முகவரி", "Password": "கடவுச்சொல்",
    "Remember me": "என்னை நினைவில் கொள்", "Forgot password?": "கடவுச்சொல் மறந்துவிட்டதா?", "Sign in securely": "பாதுகாப்பாக உள்நுழைக",
    "Good morning": "காலை வணக்கம்", "Good afternoon": "மதிய வணக்கம்", "Good evening": "மாலை வணக்கம்",
    "Open queue": "வரிசையைத் திறக்கவும்", "New tickets": "புதிய கோரிக்கைகள்", "Assigned to me": "எனக்கு ஒதுக்கப்பட்டது",
    "Critical": "மிக அவசரம்", "Resolved today": "இன்று தீர்க்கப்பட்டது", "Low confidence": "குறைந்த நம்பிக்கை",
    "Tickets by category": "வகை வாரியான கோரிக்கைகள்", "Multilingual mix": "பல்மொழிக் கலவை", "Recent ticket queue": "சமீபத்திய கோரிக்கை வரிசை",
    "Support operations": "ஆதரவு செயல்பாடுகள்", "High-priority review": "உயர் முன்னுரிமை மதிப்பாய்வு", "Escalated tickets": "மேல்நிலைக்கு அனுப்பிய கோரிக்கைகள்",
    "Resolved tickets": "தீர்க்கப்பட்ட கோரிக்கைகள்", "Ticket queue": "கோரிக்கை வரிசை", "Priority first": "முன்னுரிமை முதலில்", "Newest": "புதியவை",
    "Lowest confidence": "குறைந்த நம்பிக்கை", "Longest waiting": "நீண்ட நேரம் காத்திருப்பு", "Assign to me": "எனக்கு ஒதுக்கவும்", "Escalate": "மேல்நிலைக்கு அனுப்பவும்",
  },
};
const LanguageContext = createContext<{
  language: UiLanguage;
  setLanguage: (v: UiLanguage) => void;
  t: typeof labels.en;
  tr: (text: string) => string;
} | null>(null);
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setState] = useState<UiLanguage>(
    () => (localStorage.getItem("swift-language") as UiLanguage) || "en",
  );
  const setLanguage = (value: UiLanguage) => {
    localStorage.setItem("swift-language", value);
    setState(value);
  };
  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);
  const tr = (text: string) => language === "en" ? text : translations[language][text] ?? text;
  return (
    <LanguageContext.Provider
      value={{ language, setLanguage, t: labels[language], tr }}
    >
      {children}
    </LanguageContext.Provider>
  );
}
export const useLanguage = () => {
  const value = useContext(LanguageContext);
  if (!value)
    throw new Error("useLanguage must be used within LanguageProvider");
  return value;
};
