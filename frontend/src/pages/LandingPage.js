import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Wrench, Leaf, Truck, GraduationCap, Sparkles, Car, Baby, Briefcase, ArrowRight, MessageCircle, ShieldCheck, QrCode, Star, Check } from 'lucide-react';

const IMG = {
  hero: 'https://images.unsplash.com/photo-1461938337379-4b537cd2db74?crop=entropy&cs=srgb&fm=jpg&w=1600&q=70',
  worker: 'https://images.unsplash.com/photo-1649768870222-17848797d6b4?crop=entropy&cs=srgb&fm=jpg&w=900&q=70',
  ride: 'https://images.unsplash.com/photo-1563161084-d8d8ff841bae?crop=entropy&cs=srgb&fm=jpg&w=1000&q=70',
};

const CATEGORIES = [
  { icon: Wrench, label: 'Reformas e reparos' },
  { icon: Sparkles, label: 'Limpeza e diarista' },
  { icon: Leaf, label: 'Jardinagem' },
  { icon: Truck, label: 'Mudanças e fretes' },
  { icon: GraduationCap, label: 'Aulas particulares' },
  { icon: Baby, label: 'Babá e cuidados' },
  { icon: Car, label: 'Caronas' },
  { icon: Briefcase, label: 'Vagas de emprego' },
];

const STEPS = [
  { icon: MessageCircle, title: 'Publique seu pedido', desc: 'Diga do que precisa em poucos segundos: um encanador, uma faxina, uma carona.' },
  { icon: Star, title: 'Receba propostas', desc: 'Vizinhos e profissionais perto de você respondem. Compare perfis, fotos e avaliações.' },
  { icon: QrCode, title: 'Pague com Pix', desc: 'Pacotes e destaques pagos pelo QR Code Pix, rápido e sem taxa no cartão.' },
];

export default function LandingPage() {
  const navigate = useNavigate();
  const go = () => navigate('/auth');

  return (
    <div className="vz-dark min-h-screen" data-testid="landing-page">
      <header className="relative overflow-hidden">
        <img src={IMG.hero} alt="Profissional fazendo reparo em casa" className="absolute inset-0 h-full w-full object-cover opacity-35" data-testid="landing-hero-image" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B132B] via-[#0B132B]/90 to-[#0B132B]/40" />
        <div className="relative mx-auto max-w-6xl px-5 pb-20 pt-6 sm:pb-28">
          <nav className="flex items-center justify-between">
            <span className="font-heading text-xl font-extrabold tracking-tight text-white">Vizi<span className="text-cyan-400">nhos</span></span>
            <div className="flex items-center gap-2">
              <button onClick={() => navigate('/pacotes')} className="hidden rounded-full px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:text-white sm:block" data-testid="landing-plans-link">Pacotes</button>
              <button onClick={go} className="vz-btn-outline px-5 py-2 text-sm" data-testid="login-button">Entrar</button>
            </div>
          </nav>
          <div className="vz-rise max-w-2xl pt-16 sm:pt-24">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Serviços, caronas e vagas perto de você</p>
            <h1 className="mt-4 font-heading text-4xl font-extrabold leading-[1.05] text-white sm:text-6xl" data-testid="landing-title">
              Seus vizinhos resolvem.<br /><span className="text-cyan-400">Você descansa.</span>
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-slate-300">Peça ajuda, ofereça seus serviços e ganhe uma renda extra. Particulares e profissionais da sua região, em um só lugar.</p>
            <form onSubmit={(e) => { e.preventDefault(); go(); }} className="mt-8 flex max-w-xl flex-col gap-2 rounded-2xl border border-slate-700/60 bg-slate-900/80 p-2 backdrop-blur-xl sm:flex-row" data-testid="landing-search-form">
              <div className="flex flex-1 items-center gap-2 px-3">
                <Search size={18} className="text-slate-400" />
                <input placeholder="O que você precisa hoje? Ex: encanador, mudança" className="h-12 w-full bg-transparent text-white placeholder:text-slate-500 focus:outline-none" data-testid="landing-search-input" />
              </div>
              <button type="submit" className="vz-btn-primary h-12 px-6" data-testid="landing-search-button">Buscar</button>
            </form>
            <div className="mt-6 flex flex-wrap gap-3">
              <button onClick={() => navigate('/auth?role=migrant')} className="vz-btn-amber px-6 py-3" data-testid="need-help-card">Preciso de um serviço</button>
              <button onClick={() => navigate('/auth?role=helper')} className="vz-btn-outline px-6 py-3" data-testid="want-to-help-card">Quero oferecer serviços</button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5">
        <section className="-mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="landing-categories">
          {CATEGORIES.map(({ icon: Icon, label }, i) => (
            <button key={label} onClick={go} style={{ animationDelay: `${i * 60}ms` }} className="vz-rise group flex items-center gap-3 rounded-2xl border border-slate-700/60 bg-[#1C2541] p-4 text-left transition-colors hover:border-cyan-500/50 hover:bg-[#233056]" data-testid={`landing-category-${i}`}>
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-cyan-500/10 text-cyan-400 transition-transform group-hover:scale-110"><Icon size={20} /></span>
              <span className="text-sm font-semibold text-slate-100">{label}</span>
            </button>
          ))}
        </section>

        <section className="mt-20 grid items-center gap-10 md:grid-cols-2">
          <div>
            <h2 className="font-heading text-3xl font-bold text-white sm:text-4xl">Como funciona</h2>
            <div className="mt-8 space-y-6">
              {STEPS.map(({ icon: Icon, title, desc }, i) => (
                <div key={title} className="flex gap-4">
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[#1E40AF] text-white"><Icon size={22} /></span>
                  <div>
                    <h3 className="font-semibold text-slate-100"><span className="mr-2 font-mono text-cyan-400">0{i + 1}</span>{title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-400">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <img src={IMG.worker} alt="Prestador de serviço sorrindo" loading="lazy" className="h-80 w-full rounded-3xl object-cover sm:h-[26rem]" />
        </section>

        <section className="mt-20 overflow-hidden rounded-3xl border border-slate-700/60 bg-[#1C2541] md:grid md:grid-cols-2" data-testid="landing-rides">
          <img src={IMG.ride} alt="Carona na estrada" loading="lazy" className="h-60 w-full object-cover md:h-full" />
          <div className="p-8 sm:p-10">
            <span className="vz-chip">Novo · Caronas</span>
            <h2 className="mt-4 font-heading text-3xl font-bold text-white">Divida a viagem, divida o custo</h2>
            <p className="mt-3 leading-relaxed text-slate-400">Motoristas publicam o trajeto, passageiros reservam vagas. Combine tudo pelo chat do app.</p>
            <button onClick={go} className="vz-btn-primary mt-6 px-6 py-3" data-testid="landing-rides-button">Encontrar carona <ArrowRight size={16} /></button>
          </div>
        </section>

        <section className="mt-20" data-testid="landing-plans">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <span className="vz-trial">3 dias grátis</span>
              <h2 className="mt-3 font-heading text-3xl font-bold text-white sm:text-4xl">Pacotes para cada necessidade</h2>
            </div>
            <button onClick={() => navigate('/pacotes')} className="vz-btn-outline px-5 py-2.5 text-sm" data-testid="landing-see-plans">Ver todos os pacotes</button>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[['Grátis', 'R$ 0', 'Para começar a pedir e oferecer serviços'], ['Premium', 'R$ 29,90', 'Respostas ilimitadas e alertas de pedidos'], ['Pro', 'R$ 59,90', 'Para profissionais: selo, topo das buscas e destaques']].map(([n, p, d], i) => (
              <div key={n} className={`rounded-3xl border p-6 ${i === 2 ? 'border-cyan-500/50 bg-gradient-to-b from-[#1E40AF]/40 to-[#1C2541]' : 'border-slate-700/60 bg-[#1C2541]'}`}>
                <h3 className="font-heading text-xl font-bold text-white">{n}</h3>
                <p className="mt-2 font-mono text-3xl font-bold text-white">{p}<span className="text-sm font-normal text-slate-400">/mês</span></p>
                <p className="mt-3 flex gap-2 text-sm text-slate-400"><Check size={16} className="shrink-0 text-emerald-400" />{d}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-20 grid gap-4 pb-20 sm:grid-cols-3">
          {[[ShieldCheck, 'Perfis verificados', 'Fotos, avaliações e selo profissional para você escolher com confiança.'], [MessageCircle, 'Chat integrado', 'Combine preço, horário e detalhes sem sair do app.'], [QrCode, 'Pix na hora', 'QR Code e copia-e-cola para pagar pacotes em segundos.']].map(([Icon, t, d]) => (
            <div key={t} className="rounded-2xl border border-slate-700/60 bg-[#1C2541]/60 p-6">
              <Icon size={24} className="text-amber-400" />
              <h3 className="mt-3 font-semibold text-slate-100">{t}</h3>
              <p className="mt-1 text-sm leading-relaxed text-slate-400">{d}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-slate-800 py-8 text-center text-sm text-slate-500">© 2026 Vizinhos · Serviços, caronas e vagas</footer>
    </div>
  );
}
