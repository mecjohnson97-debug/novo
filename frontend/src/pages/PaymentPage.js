import React, { useContext, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Clock, XCircle, Loader2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import BottomNav from '../components/BottomNav';
import PixQr from '../components/PixQr';
import compressImage from '../utils/compressImage';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS = {
  pending: { label: 'Aguardando pagamento', icon: Clock, cls: 'border-amber-500/30 bg-amber-500/10 text-amber-300' },
  review: { label: 'Em análise pelo administrador', icon: Clock, cls: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300' },
  approved: { label: 'Pagamento aprovado', icon: CheckCircle2, cls: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
  rejected: { label: 'Pagamento recusado', icon: XCircle, cls: 'border-rose-500/30 bg-rose-500/10 text-rose-300' },
};

export default function PaymentPage() {
  const { id } = useParams();
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [note, setNote] = useState('');
  const [receipt, setReceipt] = useState(null);
  const [sending, setSending] = useState(false);
  const fileRef = useRef(null);
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const load = async () => {
    const res = await fetch(`${API}/api/payments/${id}`, { headers });
    if (res.ok) setP(await res.json());
    else toast.error('Pagamento não encontrado');
  };

  useEffect(() => {
    void load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [id]);

  const pickReceipt = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    try {
      setReceipt(await compressImage(file, 1400, 0.8));
    } catch {
      toast.error('Use uma imagem JPG ou PNG do comprovante');
    }
  };

  const notify = async () => {
    setSending(true);
    const res = await fetch(`${API}/api/payments/${id}/notify`, { method: 'POST', headers, body: JSON.stringify({ note: note || null, receipt }) });
    const d = await res.json();
    setSending(false);
    if (!res.ok) return toast.error(d.detail || 'Erro ao enviar aviso');
    toast.success('Aviso enviado! Vamos liberar assim que o pagamento for confirmado.');
    void load();
  };

  if (!p) return <div className="vz-dark grid min-h-screen place-items-center"><Loader2 className="animate-spin text-cyan-400" /></div>;
  const st = STATUS[p.status] || STATUS.pending;
  const StIcon = st.icon;

  return (
    <div className="vz-dark min-h-screen pb-28" data-testid="payment-page">
      <div className="mx-auto max-w-2xl px-5 pt-6">
        <button onClick={() => navigate('/pacotes')} className="flex items-center gap-1 text-sm text-slate-400 hover:text-white" data-testid="payment-back"><ArrowLeft size={16} /> Pacotes</button>
        <h1 className="mt-5 font-heading text-3xl font-extrabold text-white">Pagamento</h1>

        <div className="mt-5 rounded-2xl border border-slate-700/60 bg-[#1C2541] p-5" data-testid="payment-summary">
          <p className="text-xs uppercase tracking-wider text-slate-500">Resumo do pedido</p>
          <div className="mt-2 flex items-center justify-between">
            <p className="font-semibold text-white" data-testid="payment-item-name">{p.item_name}</p>
            <span className="font-mono text-xs text-slate-500">#{p.txid}</span>
          </div>
          <div className={`mt-4 inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium ${st.cls}`} data-testid="payment-status">
            <StIcon size={16} /> {st.label}
          </div>
        </div>

        {p.status !== 'approved' && (
          <div className="mt-5">
            <PixQr code={p.pix_code} amount={p.amount} receiver={p.pix_name} testPrefix="payment-pix" />
          </div>
        )}

        {p.status === 'approved' && (
          <div className="mt-5 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-6 text-emerald-200" data-testid="payment-approved-box">
            <p className="font-semibold">Tudo certo! Seu {p.kind === 'plan' ? 'plano' : 'destaque'} já está ativo.</p>
            <button onClick={() => navigate('/home')} className="vz-btn-primary mt-4 px-5 py-2.5" data-testid="payment-go-home">Ir para o início</button>
          </div>
        )}

        {p.status === 'pending' && (
          <div className="mt-5 rounded-2xl border border-slate-700/60 bg-[#1C2541] p-5" data-testid="payment-notify-box">
            <h2 className="font-semibold text-white">Já pagou?</h2>
            <p className="mt-1 text-sm text-slate-400">Avise aqui e, se quiser, anexe o comprovante. O administrador confirma e libera seu pacote.</p>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} placeholder="Observação (opcional)" className="vz-input mt-4 h-20 w-full resize-none p-3" data-testid="payment-note-input" />
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <button onClick={() => fileRef.current?.click()} className="vz-btn-outline px-4 py-2.5 text-sm" data-testid="payment-receipt-button"><Upload size={16} /> {receipt ? 'Trocar comprovante' : 'Anexar comprovante'}</button>
              {receipt && <img src={receipt} alt="Comprovante" className="h-12 w-12 rounded-lg object-cover" data-testid="payment-receipt-preview" />}
              <input ref={fileRef} type="file" accept="image/*" onChange={pickReceipt} className="hidden" data-testid="payment-receipt-input" />
            </div>
            <button onClick={notify} disabled={sending} className="vz-btn-primary mt-4 w-full py-3" data-testid="payment-notify-button">
              {sending ? <Loader2 size={16} className="animate-spin" /> : 'Já paguei, avisar administrador'}
            </button>
          </div>
        )}
      </div>
      <BottomNav />
    </div>
  );
}
