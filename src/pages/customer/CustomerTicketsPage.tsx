import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "../../components/layout/Layouts";
import { EmptyState, ErrorState, LoadingSkeleton, Pagination, TicketCards, TicketFilters, TicketTable } from "../../components/tickets/TicketComponents";
import { mockTicketService } from "../../services/ticketService";
import type { FilterState, Ticket } from "../../types";
import { filterTickets } from "../../lib/utils";
const initial:FilterState={search:"",status:"all",priority:"all",language:"all",category:"all"};
export function CustomerTicketsPage(){
  const [tickets,setTickets]=useState<Ticket[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState(false);const [filters,setFilters]=useState(initial);const [page,setPage]=useState(1);
  const load=()=>{setLoading(true);setError(false);const state=new URLSearchParams(location.search).get("state");if(state==="error"){setTimeout(()=>{setLoading(false);setError(true)},300);return;}mockTicketService.getTickets().then(data=>setTickets(data.slice(0,10))).catch(()=>setError(true)).finally(()=>setLoading(false))};useEffect(load,[]);
  const filtered=useMemo(()=>filterTickets(tickets,filters),[tickets,filters]);const shown=filtered.slice((page-1)*6,page*6);
  return <><PageHeader eyebrow="Support history" title="My tickets" description="Track requests, status updates, and approved responses."/><div className="card list-card"><TicketFilters filters={filters} onChange={p=>{setFilters(v=>({...v,...p}));setPage(1)}} onClear={()=>setFilters(initial)}/>{loading?<LoadingSkeleton/>:error?<ErrorState retry={load}/>:shown.length===0?<EmptyState detail={tickets.length?"No tickets match the selected filters.":"You have not submitted any tickets yet."}/>:<><div className="desktop-only"><TicketTable tickets={shown}/></div><div className="mobile-list"><TicketCards tickets={shown}/></div><Pagination page={page} pages={Math.max(1,Math.ceil(filtered.length/6))} onChange={setPage}/></>}</div></>;
}
