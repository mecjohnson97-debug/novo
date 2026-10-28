import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, MapPin, Calendar, Clock, Users, Car, Loader2, MessageCircle, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import BottomNav from '../components/BottomNav';
import PixQr from '../components/PixQr';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { brl } from '../utils/money';

const API = process.env.REACT_APP_BACKEND_URL;
const HERO = 'https://images.unsplash.com/photo-1656390239119-9907645cd479?crop=entropy&cs=srgb&fm=jpg&w=1400&q=70';
const emptyRide = { origin: '', destination: '', date: '', time: '', seats: 3, price: 0, car: '', notes: '', pix_key: '' };
const fmtDate = (d) => new Date(`${d}T12:00:00`).toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' });

function RideCard({ ride, onBook, onChat }) {
  return (
    <div className="vz-rise rounded-2xl border border-slate-700/60 bg-[#1C2541] p-5 transition-colors hover:border-cyan-500/40" data-testid={`ride-card-${ride.id}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Calendar size={13} /> {fmtDate(ride.date)} <Clock size={13} className="ml-2" /> {ride.time}
          </div>
          <p className="mt-2 flex flex-wrap items-center gap-2 font-heading text-lg font-bold text-white">
            {ride.origin} <ArrowRight size={16} className="text-cyan-400" /> {ride.destination}
          </p>
          <p className="mt-1 text-sm text-slate-400">{ride.driver_name}{ride.car ? ` · ${ride.car}` : ''}</p>
          {ride.notes && <p className="mt-2 line-clamp-2 text-sm text-slate-400">{ride.notes}</p>}
        </div>
        <div className="shrink-0 text-right">
          <p className="font-mono text-2xl font-bold text-white" data-testid={`ride-price-${ride.id}`}>{ride.price > 0 ? brl(ride.price) : 'Grátis'}</p>
          <p className="text-xs text-slate-500">por vaga</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <span className="vz-chip" data-testid={`ride-seats-${ride.id}`}><Users size={12} /> {ride.seats_left} vaga(s)</span>
          {ride.has_pix && <span className="rounded-full border border-[#32BCAD]/30 bg-[#32BCAD]/10 px-2.5 py-1 text-xs font-semibold text-[#32BCAD]">Aceita Pix</span>}
        </div>
        {ride.is_mine ? <span className="text-xs text-slate-500">Sua carona</span> : (
          <div className="flex gap-2">
            <button onClick={() => onChat(ride.driver_id)} className="vz-btn-outline px-3 py-2 text-sm" data-testid={`ride-chat-${ride.id}`}><MessageCircle size={15} /></button>
            <button onClick={() => onBook(ride)} className="vz-btn-primary px-4 py-2 text-sm" data-testid={`ride-book-${ride.id}`}>Reservar</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default function RidesPage() {
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [tab, setTab] = useState('search');
  const [q, setQ] = useState({ origin: '', destination: '', date: '' });
  const [rides, setRides] = useState([]);
  const [mine, setMine] = useState({ offered: [], booked: [] });
  const [loading, setLoading] = useState(true);
  const [publish, setPublish] = useState(false);
  const [form, setForm] = useState(emptyRide);
  const [booking, setBooking] = useState(null);
  const [seats, setSeats] = useState(1);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  const search = async (params = q) => {
    setLoading(true);
    const res = await fetch(`${API}/api/rides?${new URLSearchParams(params)}`, { headers });
    setRides(res.ok ? await res.json() : []);
    setLoading(false);
  };
  const loadMine = async () => {
    const res = await fetch(`${API}/api/rides/mine`, { headers });
    if (res.ok) setMine(await res.json());
  };
  useEffect(() => { void search(); void loadMine(); }, []);

  const submitRide = async () => {
    if (!form.origin || !form.destination || !form.date || !form.time) return toast.error('Preencha origem, destino, data e horário');
    setBusy(true);
    const res = await fetch(`${API}/api/rides`, { method: 'POST', headers, body: JSON.stringify({ ...form, seats: Number(form.seats), price: Number(form.price), pix_key: form.pix_key || null }) });
    const d = await res.json();
    setBusy(false);
    if (!res.ok) return toast.error(typeof d.detail === 'string' ? d.detail : 'Verifique os dados da viagem');
    toast.success('Carona publicada!');
    setPublish(false);
    setForm(emptyRide);
    void search();
    void loadMine();
  };

  const confirmBook = async () => {
    setBusy(true);
    const res = await fetch(`${API}/api/rides/${booking.id}/book`, { method: 'POST', headers, body: JSON.stringify({ seats: Number(seats) }) });
    const d = await res.json();
    setBusy(false);
    if (!res.ok) return toast.error(d.detail || 'Não foi possível reservar');
    toast.success('Vaga reservada! O motorista foi avisado no chat.');
    setResult(d);
    void search();
    void loadMine();
  };

  const cancelBooking = async (id) => {
    const res = await fetch(`${API}/api/rides/bookings/${id}/cancel`, { method: 'POST', headers });
    if (res.ok) { toast.success('Reserva cancelada'); void loadMine(); void search(); }
  };
  const cancelRide = async (id) => {
    const res = await fetch(`${API}/api/rides/${id}/cancel`, { method: 'POST', headers });
    if (res.ok) { toast.success('Carona cancelada'); void loadMine(); void search(); }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="vz-dark min-h-screen pb-28" data-testid="rides-page">
      <header className="relative overflow-hidden">
        <img src={HERO} alt="Motorista e passageiros em viagem" className="absolute inset-0 h-full w-full object-cover opacity-30" />
        <div className="absolute inset-0 bg-gradient-to-b from-[#0B132B]/70 to-[#0B132B]" />
        <div className="relative mx-auto max-w-4xl px-5 pb-8 pt-8">
          <div className="flex items-center justify-between">
            <h1 className="font-heading text-3xl font-extrabold text-white sm:text-4xl">Caronas</h1>
            <button onClick={() => setPublish(true)} className="vz-btn-amber px-4 py-2.5 text-sm" data-testid="rides-publish-button"><Plus size={16} /> Publicar viagem</button>
          </div>
          <p className="mt-2 text-slate-300">Viaje junto, divida os custos e conheça seus vizinhos.</p>
          <form onSubmit={(e) => { e.preventDefault(); setTab('search'); void search(); }} className="mt-6 grid gap-2 rounded-2xl border border-slate-700/60 bg-slate-900/80 p-2 backdrop-blur-xl sm:grid-cols-[1fr_1fr_auto_auto]" data-testid="rides-search-form">
            <input value={q.origin} onChange={(e) => setQ({ ...q, origin: e.target.value })} placeholder="Saindo de" className="vz-input h-12 px-3" data-testid="rides-origin-input" />
            <input value={q.destination} onChange={(e) => setQ({ ...q, destination: e.target.value })} placeholder="Indo para" className="vz-input h-12 px-3" data-testid="rides-destination-input" />
            <input type="date" value={q.date} onChange={(e) => setQ({ ...q, date: e.target.value })} className="vz-input h-12 px-3" data-testid="rides-date-input" />
            <button type="submit" className="vz-btn-primary h-12 px-5" data-testid="rides-search-button"><Search size={17} /> Buscar</button>
          </form>
        </div>
      </header>

      <div className="mx-auto max-w-4xl px-5">
        <div className="mb-5 flex gap-2">
          {[['search', `Viagens (${rides.length})`], ['offered', `Oferecidas (${mine.offered.length})`], ['booked', `Reservadas (${mine.booked.filter((b) => b.status === 'confirmed').length})`]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${tab === id ? 'bg-[#1E40AF] text-white' : 'bg-[#1C2541] text-slate-400 hover:text-white'}`} data-testid={`rides-tab-${id}`}>{label}</button>
          ))}
        </div>

        {tab === 'search' && (loading ? <Loader2 className="mx-auto mt-10 animate-spin text-cyan-400" /> : rides.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-700 p-10 text-center" data-testid="rides-empty">
            <Car className="mx-auto text-slate-500" size={36} />
            <p className="mt-3 text-slate-300">Nenhuma carona encontrada para essa busca.</p>
            <button onClick={() => setPublish(true)} className="vz-btn-outline mx-auto mt-4 px-5 py-2 text-sm" data-testid="rides-empty-publish">Publicar a primeira</button>
          </div>
        ) : (
          <div className="space-y-4" data-testid="rides-list">
            {rides.map((r) => <RideCard key={r.id} ride={r} onBook={(ride) => { setBooking(ride); setSeats(1); setResult(null); }} onChat={(uid) => navigate(`/direct-chat/${uid}`)} />)}
          </div>
        ))}

        {tab === 'offered' && (
          <div className="space-y-4" data-testid="rides-offered-list">
            {mine.offered.length === 0 && <p className="text-slate-400">Você ainda não publicou viagens.</p>}
            {mine.offered.map((r) => (
              <div key={r.id} className="rounded-2xl border border-slate-700/60 bg-[#1C2541] p-5" data-testid={`offered-ride-${r.id}`}>
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-white">{r.origin} → {r.destination}</p>
                  <span className={`text-xs ${r.status === 'active' ? 'text-emerald-400' : 'text-rose-400'}`}>{r.status === 'active' ? 'Ativa' : 'Cancelada'}</span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{fmtDate(r.date)} às {r.time} · {r.seats_left}/{r.seats} vagas livres · {brl(r.price)}</p>
                {r.bookings?.length > 0 && <ul className="mt-3 space-y-1 text-sm text-slate-300">{r.bookings.map((b) => <li key={b.id}>• {b.passenger_name} — {b.seats} vaga(s)</li>)}</ul>}
                {r.status === 'active' && <button onClick={() => cancelRide(r.id)} className="mt-3 text-sm text-rose-400 hover:underline" data-testid={`cancel-ride-${r.id}`}>Cancelar viagem</button>}
              </div>
            ))}
          </div>
        )}

        {tab === 'booked' && (
          <div className="space-y-4" data-testid="rides-booked-list">
            {mine.booked.length === 0 && <p className="text-slate-400">Você ainda não reservou caronas.</p>}
            {mine.booked.map((b) => (
              <div key={b.id} className="rounded-2xl border border-slate-700/60 bg-[#1C2541] p-5" data-testid={`booking-${b.id}`}>
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-white">{b.origin} → {b.destination}</p>
                  <span className={`text-xs ${b.status === 'confirmed' ? 'text-emerald-400' : 'text-rose-400'}`}>{b.status === 'confirmed' ? 'Confirmada' : 'Cancelada'}</span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{fmtDate(b.date)} às {b.time} · {b.seats} vaga(s) · {brl(b.total)} · {b.driver_name}</p>
                {b.status === 'confirmed' && (
                  <div className="mt-3 flex gap-4 text-sm">
                    <button onClick={() => navigate(`/direct-chat/${b.driver_id}`)} className="text-cyan-400 hover:underline" data-testid={`booking-chat-${b.id}`}>Conversar</button>
                    {b.pix_code && <button onClick={() => setResult(b)} className="text-[#32BCAD] hover:underline" data-testid={`booking-pix-${b.id}`}>Ver Pix</button>}
                    <button onClick={() => cancelBooking(b.id)} className="text-rose-400 hover:underline" data-testid={`cancel-booking-${b.id}`}>Cancelar</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Dialog open={publish} onOpenChange={setPublish}>
        <DialogContent className="max-h-[90vh] overflow-y-auto border-slate-700 bg-[#1C2541] text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-white">Publicar viagem</DialogTitle>
            <DialogDescription className="text-slate-400">Passageiros reservam vagas e falam com você pelo chat.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-3" data-testid="ride-form">
            <div className="grid grid-cols-2 gap-3">
              <input value={form.origin} onChange={set('origin')} placeholder="Origem" className="vz-input h-11 px-3" data-testid="ride-form-origin" />
              <input value={form.destination} onChange={set('destination')} placeholder="Destino" className="vz-input h-11 px-3" data-testid="ride-form-destination" />
              <input type="date" value={form.date} onChange={set('date')} className="vz-input h-11 px-3" data-testid="ride-form-date" />
              <input type="time" value={form.time} onChange={set('time')} className="vz-input h-11 px-3" data-testid="ride-form-time" />
              <label className="text-xs text-slate-400">Vagas<input type="number" min={1} max={8} value={form.seats} onChange={set('seats')} className="vz-input mt-1 h-11 w-full px-3" data-testid="ride-form-seats" /></label>
              <label className="text-xs text-slate-400">Preço por vaga (R$)<input type="number" min={0} step="0.5" value={form.price} onChange={set('price')} className="vz-input mt-1 h-11 w-full px-3" data-testid="ride-form-price" /></label>
            </div>
            <input value={form.car} onChange={set('car')} placeholder="Carro (ex: Onix prata)" className="vz-input h-11 px-3" data-testid="ride-form-car" />
            <input value={form.pix_key} onChange={set('pix_key')} placeholder="Sua chave Pix (opcional, gera QR Code para o passageiro)" className="vz-input h-11 px-3" data-testid="ride-form-pix" />
            <textarea value={form.notes} onChange={set('notes')} placeholder="Observações: ponto de encontro, bagagem..." className="vz-input h-20 resize-none p-3" data-testid="ride-form-notes" />
            <button onClick={submitRide} disabled={busy} className="vz-btn-primary py-3" data-testid="ride-form-submit">{busy ? <Loader2 size={16} className="animate-spin" /> : 'Publicar'}</button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={!!booking || !!result} onOpenChange={() => { setBooking(null); setResult(null); }}>
        <DialogContent className="max-h-[90vh] overflow-y-auto border-slate-700 bg-[#1C2541] text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-white">{result ? 'Reserva confirmada' : 'Reservar vagas'}</DialogTitle>
            <DialogDescription className="text-slate-400">{(result || booking)?.origin} → {(result || booking)?.destination}</DialogDescription>
          </DialogHeader>
          {result ? (
            <div className="space-y-4" data-testid="booking-result">
              <p className="text-sm text-slate-300">{result.seats} vaga(s) · total {brl(result.total)}. Combine os detalhes com {result.driver_name} pelo chat.</p>
              {result.pix_code && <PixQr code={result.pix_code} amount={result.total} receiver={result.driver_name} testPrefix="ride-pix" />}
              <button onClick={() => navigate(`/direct-chat/${result.driver_id}`)} className="vz-btn-primary w-full py-3" data-testid="booking-result-chat">Conversar com o motorista</button>
            </div>
          ) : booking && (
            <div className="space-y-4">
              <label className="block text-sm text-slate-300">Quantas vagas?
                <input type="number" min={1} max={booking.seats_left} value={seats} onChange={(e) => setSeats(e.target.value)} className="vz-input mt-1 h-11 w-full px-3" data-testid="booking-seats-input" />
              </label>
              <p className="font-mono text-xl text-white" data-testid="booking-total">Total: {brl(booking.price * Number(seats || 0))}</p>
              <button onClick={confirmBook} disabled={busy || seats < 1 || seats > booking.seats_left} className="vz-btn-primary w-full py-3" data-testid="booking-confirm-button">{busy ? <Loader2 size={16} className="animate-spin" /> : 'Confirmar reserva'}</button>
            </div>
          )}
        </DialogContent>
      </Dialog>
      <BottomNav />
    </div>
  );
}
