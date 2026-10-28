import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Zap, Crown, Rocket, Loader2, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import BottomNav from '../components/BottomNav';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { brl } from '../utils/money';

const API = process.env.REACT_APP_BACKEND_URL;
const ICONS = { free: Zap, premium: Crown, pro: Rocket };

export default function PlansPage() {
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [sub, setSub] = useState(null);
  const [busy, setBusy] = useState('');
  const [boost, setBoost] = useState(null);
  const [myPosts, setMyPosts] = useState([]);
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => {
    fetch(`${API}/api/plans`).then((r) => r.json()).then(setData);
    if (token) fetch(`${API}/api/subscription/me`, { headers }).then((r) => r.ok && r.json()).then((s) => s && setSub(s));
  }, [token]);

  const needLogin = () => { toast.info('Entre na sua conta para continuar'); navigate('/auth'); };

  const pay = async (body) => {
    if (!user) return needLogin();
    setBusy(body.item_id);
    try {
      const res = await fetch(`${API}/api/payments`, { method: 'POST', headers, body: JSON.stringify(body) });
      const p = await res.json();
      if (!res.ok) throw new Error(p.detail);
      navigate(`/pagamento/${p.id}`);
    } catch (e) {
      toast.error(e.message || 'Não foi possível gerar o Pix');
    } finally {
      setBusy('');
    }
  };

  const trial = async (plan) => {
    if (!user) return needLogin();
    setBusy(`trial-${plan}`);
    const res = await fetch(`${API}/api/subscription/trial`, { method: 'POST', headers, body: JSON.stringify({ plan }) });
    const d = await res.json();
    setBusy('');
    if (!res.ok) return toast.error(d.detail);
    toast.success(`3 dias grátis do ${plan === 'pro' ? 'Pro' : 'Premium'} ativados!`);
    setSub({ ...sub, plan: d.plan, expires_at: d.expires_at, trial: true, trial_available: false });
  };

  const openBoost = async (b) => {
    if (!user) return needLogin();
    const res = await fetch(`${API}/api/posts?user_id=${user.id}&limit=50`, { headers });
    setMyPosts(res.ok ? (await res.json()).posts : []);
    setBoost(b);
  };

  const current = sub?.plan || 'free';

  return (
    <div className="vz-dark min-h-screen pb-28" data-testid="plans-page">
      <div className="mx-auto max-w-6xl px-5 pt-6">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-slate-400 hover:text-white" data-testid="plans-back"><ArrowLeft size={16} /> Voltar</button>
        <div className="mt-6 max-w-2xl">
          <span className="vz-trial">Teste 3 dias grátis</span>
          <h1 className="mt-4 font-heading text-4xl font-extrabold text-white sm:text-5xl">Pacotes e destaques</h1>
          <p className="mt-3 text-lg text-slate-400">Escolha o plano ideal, apareça para mais vizinhos e pague na hora com Pix.</p>
          {sub && current !== 'free' && (
            <p className="mt-4 inline-flex rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300" data-testid="plans-current">
              Plano atual: <b className="mx-1">{current === 'pro' ? 'Pro' : 'Premium'}</b>{sub.trial && '(teste grátis)'} até {new Date(sub.expires_at).toLocaleDateString('pt-BR')}
            </p>
          )}
        </div>

        {!data ? <Loader2 className="mx-auto mt-16 animate-spin text-cyan-400" /> : (
          <>
            <div className="mt-10 grid items-stretch gap-5 md:grid-cols-3" data-testid="plans-grid">
              {data.plans.map((p, i) => {
                const Icon = ICONS[p.id];
                const featured = p.id === 'premium';
                return (
                  <div key={p.id} style={{ animationDelay: `${i * 80}ms` }} className={`vz-rise relative flex flex-col rounded-3xl border p-7 ${featured ? 'border-cyan-500/60 bg-gradient-to-b from-[#1E40AF]/50 to-[#1C2541] shadow-2xl shadow-cyan-500/10' : 'border-slate-700/60 bg-[#1C2541]'}`} data-testid={`plan-card-${p.id}`}>
                    {featured && <span className="absolute -top-3 left-7 rounded-full bg-cyan-400 px-3 py-1 text-xs font-bold text-slate-950">Mais escolhido</span>}
                    <Icon size={26} className={featured ? 'text-cyan-300' : 'text-amber-400'} />
                    <h2 className="mt-4 font-heading text-2xl font-bold text-white">{p.name}</h2>
                    <p className="mt-2 font-mono text-4xl font-bold text-white" data-testid={`plan-price-${p.id}`}>{brl(p.price)}<span className="text-sm font-normal text-slate-400">/mês</span></p>
                    <ul className="mt-6 flex-1 space-y-3">
                      {p.features.map((f) => <li key={f} className="flex gap-2 text-sm text-slate-300"><Check size={17} className="mt-0.5 shrink-0 text-emerald-400" />{f}</li>)}
                    </ul>
                    {p.price > 0 ? (
                      <div className="mt-7 space-y-2">
                        {(!sub || sub.trial_available) && current === 'free' && (
                          <button onClick={() => trial(p.id)} disabled={!!busy} className="vz-btn-amber w-full py-3" data-testid={`plan-trial-${p.id}`}>
                            {busy === `trial-${p.id}` ? <Loader2 size={16} className="animate-spin" /> : 'Começar 3 dias grátis'}
                          </button>
                        )}
                        <button onClick={() => pay({ kind: 'plan', item_id: p.id })} disabled={!!busy} className={`${featured ? 'vz-btn-primary' : 'vz-btn-outline'} w-full py-3`} data-testid={`plan-buy-${p.id}`}>
                          {busy === p.id ? <Loader2 size={16} className="animate-spin" /> : `Assinar com Pix`}
                        </button>
                      </div>
                    ) : (
                      <div className="mt-7 rounded-xl border border-slate-700 py-3 text-center text-sm text-slate-400" data-testid="plan-free-current">{current === 'free' ? 'Seu plano atual' : 'Plano básico'}</div>
                    )}
                  </div>
                );
              })}
            </div>

            <section className="mt-16" data-testid="boosts-section">
              <h2 className="font-heading text-2xl font-bold text-white">Destaques avulsos</h2>
              <p className="mt-1 text-slate-400">Coloque uma publicação no topo do feed, sem assinatura.</p>
              <div className="mt-6 grid gap-4 sm:grid-cols-3">
                {data.boosts.map((b) => (
                  <div key={b.id} className="flex items-center justify-between rounded-2xl border border-slate-700/60 bg-[#1C2541] p-5" data-testid={`boost-card-${b.id}`}>
                    <div>
                      <p className="font-semibold text-slate-100">{b.name}</p>
                      <p className="mt-1 font-mono text-xl font-bold text-amber-400">{brl(b.price)}</p>
                    </div>
                    <button onClick={() => openBoost(b)} className="vz-btn-primary px-4 py-2 text-sm" data-testid={`boost-buy-${b.id}`}>Destacar</button>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>

      <Dialog open={!!boost} onOpenChange={() => setBoost(null)}>
        <DialogContent className="border-slate-700 bg-[#1C2541] text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-white">{boost?.name}</DialogTitle>
            <DialogDescription className="text-slate-400">Escolha qual publicação vai ficar em destaque.</DialogDescription>
          </DialogHeader>
          <div className="max-h-72 space-y-2 overflow-y-auto" data-testid="boost-post-list">
            {myPosts.length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-400" data-testid="boost-no-posts">Você ainda não tem publicações. Publique algo no início primeiro.</p>
            ) : myPosts.map((p) => (
              <button key={p.id} onClick={() => pay({ kind: 'boost', item_id: boost.id, post_id: p.id })} disabled={!!busy}
                className="w-full rounded-xl border border-slate-700 p-3 text-left transition-colors hover:border-cyan-500/60 hover:bg-slate-800" data-testid={`boost-post-${p.id}`}>
                <p className="line-clamp-1 font-medium text-slate-100">{p.title}</p>
                <p className="line-clamp-1 text-xs text-slate-400">{p.description}</p>
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
      {user && <BottomNav />}
    </div>
  );
}
