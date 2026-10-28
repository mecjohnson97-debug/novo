import React from 'react';
import { ShieldAlert, MessageCircle, Plus, HandHeart, Sun } from 'lucide-react';

export default function WelcomeStrip({ userName, onNeedHelp, onWantHelp }) {
  const first = (userName || '').split(' ')[0];
  return (
    <section className="feed-welcome fade-up" data-testid="welcome-banner">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-[#A0703F]">
            <Sun size={14} /> Bem-vindo de volta
          </p>
          <h1 className="mt-1 font-heading text-2xl sm:text-3xl font-bold text-[#2C221E] leading-tight" data-testid="welcome-title">
            Olá, {first || 'amigo'}.
          </h1>
          <p className="mt-1 text-sm text-[#5C524B]">Veja quem precisa e quem oferece ajuda hoje.</p>
        </div>
        <div className="flex flex-shrink-0 gap-2">
          <a href="tel:112" className="feed-sos" data-testid="sos-emergency-btn" aria-label="Emergência 112">
            <ShieldAlert size={16} /> SOS
          </a>
          <a
            href="https://wa.me/5514996078465?text=Olá! Preciso de ajuda."
            target="_blank"
            rel="noopener noreferrer"
            className="feed-whats"
            data-testid="whatsapp-talk-btn"
          >
            <MessageCircle size={16} /> <span className="hidden sm:inline">Fale comigo</span>
          </a>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2.5">
        <button onClick={onNeedHelp} className="feed-cta feed-cta-gold" data-testid="i-need-help-cta">
          <Plus size={18} /> Preciso de ajuda
        </button>
        <button onClick={onWantHelp} className="feed-cta feed-cta-sage" data-testid="i-want-to-help-cta">
          <HandHeart size={18} /> Quero ajudar
        </button>
      </div>
    </section>
  );
}
