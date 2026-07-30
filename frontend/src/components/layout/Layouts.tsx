import { Bell, ChevronDown, CircleCheckBig, Gauge, LifeBuoy, LogOut, Menu, Search, Settings, ShieldAlert, Ticket, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/providers/AuthProvider";
import { useLanguage } from "../../app/providers/LanguageProvider";
import { LanguageSelector, Logo, ThemeSwitcher } from "../common/Controls";
import { cn } from "../../lib/utils";

function ProfileMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  return <div className="profile"><button className="profile-button" onClick={()=>setOpen(!open)} aria-expanded={open}><span className="avatar">{user?.name.split(" ").map(x=>x[0]).join("").slice(0,2)}</span><span><strong>{user?.name}</strong><small>{user?.role === "agent" ? "Support agent" : "Customer"}</small></span><ChevronDown size={15}/></button>{open&&<div className="profile-menu"><button onClick={async()=>{await logout();navigate("/login");}}><LogOut size={16}/>Log out</button></div>}</div>;
}
export function CustomerLayout() {
  const { t } = useLanguage();
  return <div className="app-shell"><header className="customer-nav"><Link to="/customer/submit"><Logo/></Link><nav aria-label="Customer navigation"><NavLink to="/customer/submit">{t.submit}</NavLink><NavLink to="/customer/tickets">{t.tickets}</NavLink></nav><div className="nav-tools"><LanguageSelector/><ThemeSwitcher/><ProfileMenu/></div></header><main className="page"><Outlet/></main><footer className="footer"><span>Swift Support prototype</span><span>Never share passwords or PINs in a ticket.</span></footer></div>;
}
const links = [
  ["/agent/dashboard","Dashboard",Gauge],
  ["/agent/tickets","Ticket Queue",Ticket],
  ["/agent/high-priority","High Priority",ShieldAlert],
  ["/agent/escalated","Escalated",LifeBuoy],
  ["/agent/resolved","Resolved",CircleCheckBig],
  ["/agent/reports","Reports",Gauge],
  ["/agent/settings","Settings",Settings],
] as const;
export function AgentLayout() {
  const [sidebar, setSidebar] = useState(false);
  return <div className="agent-shell"><aside className={cn("sidebar",sidebar&&"open")}><div className="sidebar-head"><Logo/><button className="icon-btn mobile-only" onClick={()=>setSidebar(false)}><X/><span className="sr-only">Close menu</span></button></div><nav>{links.map(([path,label,Icon])=><NavLink key={path} to={path} onClick={()=>setSidebar(false)}><Icon/><span>{label}</span>{label==="High Priority"&&<em>5</em>}</NavLink>)}</nav><div className="security-note"><ShieldAlert/><span><strong>Secure workspace</strong><small>Human approval required</small></span></div></aside><div className="agent-main"><header className="agent-top"><button className="icon-btn menu-button" onClick={()=>setSidebar(true)}><Menu/><span className="sr-only">Open menu</span></button><label className="global-search"><Search/><span className="sr-only">Global search</span><input placeholder="Search ID, customer or subject…"/></label><div className="nav-tools"><button className="icon-btn notice"><Bell/><span>3</span><span className="sr-only">3 notifications</span></button><LanguageSelector/><ThemeSwitcher/><ProfileMenu/></div></header><main className="agent-page"><Outlet/></main></div>{sidebar&&<button className="sidebar-overlay" onClick={()=>setSidebar(false)} aria-label="Close navigation"/>}</div>;
}
export function PageHeader({ eyebrow, title, description, actions }: {eyebrow?:string;title:string;description?:string;actions?:React.ReactNode}) {
  return <header className="page-header"><div>{eyebrow&&<span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1>{description&&<p>{description}</p>}</div>{actions&&<div className="page-actions">{actions}</div>}</header>;
}
