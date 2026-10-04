import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Bell, CreditCard, Landmark, Sparkles } from 'lucide-react'
import { api, ApiError, type Integration, type PaymentIntent, type Webhook } from '../api/client'
import { StatusBadge } from '../components/StatusBadge'
import { DataTable } from '../components/DataTable'
import { useAuth } from '../auth/AuthContext'
import { subscribeLiveMessages } from '../hooks/useWebSocket'

function money(minor?: number) { return minor == null ? '—' : `KES ${(minor / 100).toFixed(2)}` }
function greetingName(user: { display_name?: string | null; email?: string } | null) {
  if (!user) return null
  if (user.display_name?.trim()) return user.display_name.trim().split(/\s+/)[0]
  return user.email?.split('@')[0] || null
}

const btn='inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm font-medium text-[var(--text)] no-underline shadow-[var(--shadow-sm)] hover:bg-[var(--panel-2)] hover:no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]'
const primary=`${btn} border-[var(--accent)] bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)]`

export function Home() {
  const { user } = useAuth(); const navigate = useNavigate()
  const [payments,setPayments]=useState<PaymentIntent[]>([]); const [integrations,setIntegrations]=useState<Integration[]>([])
  const [hooks,setHooks]=useState(0); const [error,setError]=useState<string|null>(null); const [loading,setLoading]=useState(true)
  async function load(quiet=false){ if(!quiet)setLoading(true); try{
    const [pay,integ]=await Promise.all([api.get<PaymentIntent[]>('/v1/payment-intents'),api.get<Integration[]>('/v1/integrations')])
    setPayments((pay||[]).slice(0,5)); setIntegrations(integ||[]); const tid=user?.tenant_id
    if(tid){try{const w=await api.get<Webhook[]>(`/v1/webhooks?tenant_id=${tid}`);setHooks(w.length)}catch{setHooks(0)}}
  }catch(e){setError(e instanceof ApiError?e.detail:'Could not load dashboard')}finally{setLoading(false)}}
  useEffect(()=>{load()},[user])
  useEffect(()=>subscribeLiveMessages(m=>{if(m.type==='payment.update'||m.type==='notification')load(true)}),[user])
  const first=greetingName(user), hasShortcode=integrations.length>0, waitingCount=payments.filter(p=>p.status==='provider_requested'||p.status==='created').length
  const nextStep=!hasShortcode?{title:'Add a shortcode',body:'Connect a paybill or till so you can request payments from customers.',to:'/integrations',label:'Add shortcode',Icon:Landmark}:waitingCount>0?{title:'Payments waiting on the customer',body:'A phone prompt is open. It usually settles within a minute — open a payment for details.',to:'/intents',label:'View payments',Icon:CreditCard}:{title:'Request a payment',body:'Send a prompt to a customer’s phone and track the result here.',to:'/intents',label:'New payment',Icon:CreditCard}
  const NextIcon=nextStep.Icon
  return <div className="w-full" data-testid="home-page">
    <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
      <div><p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">Overview</p><h1 className="m-0 text-[1.65rem] font-semibold tracking-tight">Hello{first ? `, ${first}` : ''}</h1><p className="mt-1 max-w-md text-sm text-[var(--muted)]">A calm view of recent collections and what needs attention next.</p></div>
      <Link className={primary} to="/intents"><CreditCard size={16} strokeWidth={1.75}/>New payment</Link>
    </div>
    {error&&<div className="mb-4 rounded-lg border border-[var(--danger)]/30 bg-[var(--danger)]/10 px-4 py-3 text-sm text-[var(--danger)]">{error}</div>}
    <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
      {[[Landmark,'Shortcodes',integrations.length,'Manage','/integrations'],[Bell,'App endpoints',hooks,'Configure','/webhooks'],[CreditCard,'Recent',payments.length,'All payments','/intents']].map(([Icon,label,value,action,to])=><div key={String(label)} className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
        <div className="flex items-center gap-1 text-xs font-medium text-[var(--muted)]"><Icon size={14} strokeWidth={1.75}/>{label}</div><div className="my-1 text-2xl font-bold tracking-tight">{loading?'—':value as number}</div><Link to={String(to)} className="inline-flex items-center gap-1 text-xs text-[var(--muted)] hover:text-[var(--accent)]"><span>{String(action)}</span><ArrowRight size={12}/></Link>
      </div>)}
    </div>
    <section className="mb-4 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
      <div className="mb-3 flex items-center justify-between"><h2 className="m-0 flex items-center gap-2 text-base font-semibold"><Sparkles size={16} strokeWidth={1.75}/>Suggested next step</h2></div>
      <div className="flex items-start gap-3"><NextIcon size={20} strokeWidth={1.75} className="mt-1 shrink-0 text-[var(--accent)]"/><div><div className="text-sm font-semibold">{nextStep.title}</div><p className="my-1.5 mb-3 text-xs text-[var(--muted)]">{nextStep.body}</p><Link className={btn} to={nextStep.to}>{nextStep.label}<ArrowRight size={14}/></Link></div></div>
    </section>
    <section className="w-full rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] p-4 shadow-[var(--shadow)]">
      <div className="mb-3 flex items-center justify-between"><h2 className="m-0 text-base font-semibold">Recent payments</h2><Link to="/intents" className="text-xs text-[var(--accent)]">View all</Link></div>
      {loading?<p className="text-xs text-[var(--muted)]">Loading…</p>:<DataTable rows={payments} getRowId={p=>p.id} searchPlaceholder="Search…" defaultPageSize={5} pageSizeOptions={[5,10]} maxHeight="320px" emptyTitle="No payments yet" emptyHint="Create a payment to see it here." onRowClick={p=>navigate(`/intents/${p.id}`)} columns={[
        {id:'amount',header:'Amount',searchValue:p=>money(p.amount_minor),cell:p=><span className="font-mono text-[0.85em]">{money(p.amount_minor)}</span>},
        {id:'phone',header:'Phone',searchValue:p=>p.phone||'',cell:p=><span className="font-mono text-xs">{p.phone}</span>},
        {id:'status',header:'Status',searchValue:p=>p.status,cell:p=><StatusBadge value={p.status}/>},
        {id:'when',header:'When',cell:p=><span className="text-xs text-[var(--muted)]">{p.created_at?new Date(p.created_at).toLocaleString():'—'}</span>},
      ]}/>}
    </section>
  </div>
}
