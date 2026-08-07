import { useEffect, useState } from "react";
import { PageHeader } from "../../components/layout/Layouts";
import { ticketService } from "../../services/serviceSelector";
import type { AdminAudit, AdminQueue, AdminSetting, AdminUserRecord, UserRole } from "../../types";
import { formatDate } from "../../lib/utils";

const Notice=({text}:{text:string})=>text?<div className="success-alert">{text}</div>:null;

export function AdminUsersPage(){
 const [users,setUsers]=useState<AdminUserRecord[]>([]),[query,setQuery]=useState(""),[notice,setNotice]=useState("");
 const load=()=>ticketService.getAdminUsers().then(setUsers); useEffect(()=>{void load()},[]);
 const update=async(id:string,patch:{role?:UserRole;is_active?:boolean})=>{try{await ticketService.updateAdminUser(id,patch);setNotice("User updated and audited.");load();}catch(e){setNotice(e instanceof Error?e.message:"Update failed");}};
 return <><PageHeader eyebrow="Access governance" title="User management" description="Manage roles, account status, and access without exposing credentials."/><Notice text={notice}/><section className="card"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search name or email…"/><div className="table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead><tbody>{users.filter(u=>(u.name+u.email).toLowerCase().includes(query.toLowerCase())).map(u=><tr key={u.id}><td><strong>{u.name}</strong><small>{u.email}</small></td><td><select value={u.role} onChange={e=>update(u.id,{role:e.target.value as UserRole})}><option value="customer">Customer</option><option value="agent">Support agent</option><option value="administrator">Administrator</option></select></td><td>{u.isActive?"Active":"Disabled"}</td><td>{formatDate(u.createdAt)}</td><td><button className="btn secondary small" onClick={()=>update(u.id,{is_active:!u.isActive})}>{u.isActive?"Deactivate":"Activate"}</button></td></tr>)}</tbody></table></div></section></>;
}

export function AdminQueuesPage(){
 const [queues,setQueues]=useState<AdminQueue[]>([]),[name,setName]=useState(""),[description,setDescription]=useState(""),[notice,setNotice]=useState(""); const load=()=>ticketService.getAdminQueues().then(setQueues);useEffect(()=>{void load()},[]);
 const create=async()=>{try{await ticketService.createAdminQueue({name,description});setName("");setDescription("");setNotice("Queue created and audited.");load();}catch(e){setNotice(e instanceof Error?e.message:"Create failed");}};
 return <><PageHeader eyebrow="Routing configuration" title="Queue management" description="Create and maintain support queues. Queues with open tickets cannot be deactivated."/><Notice text={notice}/><section className="card"><h2>Create queue</h2><div className="filters"><input value={name} onChange={e=>setName(e.target.value)} placeholder="Queue name"/><input value={description} onChange={e=>setDescription(e.target.value)} placeholder="Description"/><button className="btn" disabled={name.trim().length<2} onClick={create}>Create queue</button></div></section><section className="card list-card"><div className="table-wrap"><table><thead><tr><th>Queue</th><th>Tickets</th><th>Status</th><th>Action</th></tr></thead><tbody>{queues.map(q=><tr key={q.id}><td><strong>{q.name}</strong><small>{q.description}</small></td><td>{q.ticketCount}</td><td>{q.isActive?"Active":"Inactive"}</td><td><button className="btn secondary small" onClick={async()=>{try{await ticketService.updateAdminQueue(q.id,{is_active:!q.isActive});setNotice("Queue updated.");load();}catch(e){setNotice(e instanceof Error?e.message:"Update failed");}}}>{q.isActive?"Deactivate":"Activate"}</button></td></tr>)}</tbody></table></div></section></>;
}

export function AdminAuditPage(){
 const [items,setItems]=useState<AdminAudit[]>([]),[query,setQuery]=useState("");useEffect(()=>{ticketService.getAdminAudit().then(setItems)},[]);
 return <><PageHeader eyebrow="Immutable activity" title="Audit logs" description="Review privileged changes and operational actions. Audit entries cannot be edited or deleted."/><section className="card"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Filter action, actor or entity…"/><div className="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Detail</th></tr></thead><tbody>{items.filter(x=>(x.actor+x.action+x.entityType).toLowerCase().includes(query.toLowerCase())).map(x=><tr key={x.id}><td>{formatDate(x.createdAt)}</td><td>{x.actor}</td><td>{x.action.replaceAll("_"," ")}</td><td>{x.entityType}<small>{x.entityId}</small></td><td>{x.detail||"—"}</td></tr>)}</tbody></table></div></section></>;
}

export function AdminSettingsPage(){
 const [settings,setSettings]=useState<AdminSetting[]>([]),[notice,setNotice]=useState("");useEffect(()=>{ticketService.getAdminSettings().then(setSettings)},[]);
 const set=(key:string,value:string)=>setSettings(s=>s.map(x=>x.key===key?{...x,value}:x));
 const save=async()=>{try{setSettings(await ticketService.updateAdminSettings(Object.fromEntries(settings.map(x=>[x.key,x.value]))));setNotice("Settings saved and audited.");}catch(e){setNotice(e instanceof Error?e.message:"Save failed");}};
 return <><PageHeader eyebrow="Operational policy" title="System settings" description="Only allow-listed, non-secret settings are available here."/><Notice text={notice}/><section className="card form-card">{settings.map(s=><label key={s.key}>{s.description}{s.valueType==="boolean"?<select value={s.value} onChange={e=>set(s.key,e.target.value)}><option value="true">Enabled</option><option value="false">Disabled</option></select>:<input type={s.valueType==="string"?"text":"number"} step={s.valueType==="number"?"0.05":"1"} value={s.value} onChange={e=>set(s.key,e.target.value)}/>}<small>{s.key}</small></label>)}<button className="btn" onClick={save}>Save settings</button></section></>;
}
