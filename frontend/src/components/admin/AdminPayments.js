import React, { useContext, useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2, Eye } from 'lucide-react';
import { toast } from 'sonner';
import { AuthContext } from '../../App';
import { Dialog, DialogContent, DialogTitle } from '../ui/dialog';
import { brl } from '../../utils/money';

const API = process.env.REACT_APP_BACKEND_URL;
const LABEL = { pending: 'Aguardando', review: 'Avisou pagamento', approved: 'Aprovado', rejected: 'Recusado' };
const CLS = { pending: 'bg-amber-100 text-amber-800', review: 'bg-cyan-100 text-cyan-800', approved: 'bg-emerald-100 text-emerald-800', rejected: 'bg-rose-100 text-rose-800' };

function PixSettings({ headers }) {
  const [s, setS] = useState(null);
  const [saving, setSaving] = useState(false);
  useEffect(() => { fetch(`${API}/api/admin/pix-settings`, { headers }).then((r) => r.json()).then(setS); }, []);
  const save = async () => {
    setSaving(true);
    const res = await fetch(`${API}/api/admin/pix-settings`, { method: 'PUT', headers, body: JSON.stringify(s) });
    setSaving(false);
    if (res.ok) toast.success('Chave Pix salva'); else toast.error('Verifique os dados');
  };
  if (!s) return null;
  return (
    <div className="rounded-2xl border bg-white p-5" data-testid="admin-pix-settings">
      <h3 className="font-bold text-gray-900">Chave Pix do recebedor</h3>
      <p className="text-sm text-gray-500">Usada para gerar o QR Code de todos os pacotes.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {[['key', 'Chave Pix (CPF, e-mail, telefone ou aleatória)'], ['name', 'Nome do recebedor'], ['city', 'Cidade']].map(([k, label]) => (
          <label key={k} className="text-xs font-medium text-gray-600">{label}
            <input value={s[k]} onChange={(e) => setS({ ...s, [k]: e.target.value })} className="mt-1 h-10 w-full rounded-lg border px-3 text-sm text-gray-900" data-testid={`admin-pix-${k}`} />
          </label>
        ))}
      </div>
      <button onClick={save} disabled={saving} className="mt-4 rounded-lg bg-primary px-5 py-2 text-sm font-semibold text-white" data-testid="admin-pix-save">{saving ? 'Salvando…' : 'Salvar'}</button>
    </div>
  );
}

export default function AdminPayments() {
  const { token } = useContext(AuthContext);
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState('');
  const [receipt, setReceipt] = useState(null);

  const load = async () => {
    const res = await fetch(`${API}/api/admin/payments${filter ? `?status=${filter}` : ''}`, { headers });
    if (res.ok) setData(await res.json());
  };
  useEffect(() => { void load(); }, [filter]);

  const act = async (id, action) => {
    const res = await fetch(`${API}/api/admin/payments/${id}/${action}`, { method: 'POST', headers });
    const d = await res.json();
    if (!res.ok) return toast.error(d.detail);
    toast.success(action === 'approve' ? 'Pagamento aprovado e pacote liberado' : 'Pagamento recusado');
    void load();
  };
  const viewReceipt = async (id) => {
    const res = await fetch(`${API}/api/admin/payments/${id}/receipt`, { headers });
    if (res.ok) setReceipt((await res.json()).receipt);
  };

  if (!data) return <Loader2 className="mx-auto animate-spin" />;
  const st = data.stats;
  return (
    <div className="space-y-6" data-testid="admin-payments">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[['Total faturado', brl(st.revenue), 'revenue'], ['Pagamentos pendentes', st.pending, 'pending'], ['Planos ativos', st.active_subscriptions, 'subs'], ['Caronas publicadas', st.rides, 'rides']].map(([l, v, k]) => (
          <div key={k} className="rounded-2xl border bg-white p-4" data-testid={`admin-stat-${k}`}>
            <p className="text-xs text-gray-500">{l}</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{v}</p>
          </div>
        ))}
      </div>

      <PixSettings headers={headers} />

      <div className="rounded-2xl border bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-bold text-gray-900">Pagamentos Pix</h3>
          <div className="flex gap-1">
            {[['', 'Todos'], ['review', 'Avisados'], ['pending', 'Aguardando'], ['approved', 'Aprovados']].map(([v, l]) => (
              <button key={v} onClick={() => setFilter(v)} className={`rounded-full px-3 py-1 text-xs font-medium ${filter === v ? 'bg-primary text-white' : 'bg-gray-100 text-gray-600'}`} data-testid={`admin-payments-filter-${v || 'all'}`}>{l}</button>
            ))}
          </div>
        </div>
        <div className="mt-4 divide-y">
          {data.payments.length === 0 && <p className="py-6 text-center text-sm text-gray-500">Nenhum pagamento.</p>}
          {data.payments.map((p) => (
            <div key={p.id} className="flex flex-wrap items-center justify-between gap-3 py-3" data-testid={`admin-payment-${p.id}`}>
              <div className="min-w-0">
                <p className="font-medium text-gray-900">{p.item_name} · {brl(p.amount)}</p>
                <p className="text-xs text-gray-500">{p.user_name} ({p.user_email}) · #{p.txid} · {new Date(p.created_at).toLocaleString('pt-BR')}</p>
                {p.note && <p className="mt-1 text-xs text-gray-600">“{p.note}”</p>}
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${CLS[p.status]}`}>{LABEL[p.status]}</span>
                {p.has_receipt && <button onClick={() => viewReceipt(p.id)} className="rounded-lg border p-1.5 text-gray-600" title="Ver comprovante" data-testid={`admin-payment-receipt-${p.id}`}><Eye size={16} /></button>}
                {p.status !== 'approved' && p.status !== 'rejected' && (
                  <>
                    <button onClick={() => act(p.id, 'approve')} className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white" data-testid={`admin-payment-approve-${p.id}`}><CheckCircle size={14} /> Aprovar</button>
                    <button onClick={() => act(p.id, 'reject')} className="flex items-center gap-1 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white" data-testid={`admin-payment-reject-${p.id}`}><XCircle size={14} /> Recusar</button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <Dialog open={!!receipt} onOpenChange={() => setReceipt(null)}>
        <DialogContent className="max-w-lg">
          <DialogTitle>Comprovante</DialogTitle>
          {receipt && <img src={receipt} alt="Comprovante" className="max-h-[70vh] w-full rounded-xl object-contain" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
