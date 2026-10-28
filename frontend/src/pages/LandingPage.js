import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { HandHeart, HeartHandshake, Shield, Award, Users, ArrowRight, Utensils, Home, Scale, Briefcase } from 'lucide-react';

const IMG = {
  hero: 'https://images.pexels.com/photos/6646873/pexels-photo-6646873.jpeg?auto=compress&cs=tinysrgb&w=1400',
  need: 'https://images.unsplash.com/photo-1593113616828-6f22bca04804?crop=entropy&cs=srgb&fm=jpg&w=900&q=70',
  help: 'https://images.unsplash.com/photo-1628717341663-0007b0ee2597?crop=entropy&cs=srgb&fm=jpg&w=900&q=70',
  care: 'https://images.pexels.com/photos/6436179/pexels-photo-6436179.jpeg?auto=compress&cs=tinysrgb&w=1000',
  food: 'https://images.unsplash.com/photo-1599059813005-11265ba4b4ce?crop=entropy&cs=srgb&fm=jpg&w=700&q=70',
};

const LANGS = ['pt', 'fr', 'en', 'es'];
const keyAct = (fn) => (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); } };

function ChoiceCard({ img, icon: Icon, title, desc, accent, onClick, testId, cta }) {
  return (
    <div role="button" tabIndex={0} onClick={onClick} onKeyDown={keyAct(onClick)} className="land-card group" data-testid={testId}>
      <div className="relative h-44 overflow-hidden sm:h-52">
        <img src={img} alt="" loading="lazy" className="land-card-img h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/45 to-transparent" />
        <span className={`absolute bottom-3 left-3 grid h-11 w-11 place-items-center rounded-2xl text-white ${accent}`}><Icon size={22} /></span>
      </div>
      <div className="p-5 text-left">
        <h2 className="font-heading text-xl font-bold text-[#2C221E]">{title}</h2>
        <p className="mt-1.5 text-[15px] leading-relaxed text-[#5C524B]">{desc}</p>
        <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-[#1F7A6F]">{cta} <ArrowRight size={16} className="land-arrow" /></span>
      </div>
    </div>
  );
}

function Feature({ icon: Icon, title, desc }) {
  return (
    <div className="rounded-2xl border border-[#ECE5DA] bg-white p-5">
      <span className="grid h-11 w-11 place-items-center rounded-xl bg-[#FEFAE0] text-[#A0703F]"><Icon size={22} /></span>
      <h3 className="mt-3 font-semibold text-[#2C221E]">{title}</h3>
      <p className="mt-1 text-sm leading-relaxed text-[#5C524B]">{desc}</p>
    </div>
  );
}

export default function LandingPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  return (
    <div className="land-root min-h-screen" data-testid="landing-page">
      <header className="relative">
        <img src={IMG.hero} alt={t('landingHeroAlt')} className="absolute inset-0 h-full w-full object-cover" data-testid="landing-hero-image" />
        <div className="absolute inset-0 bg-gradient-to-b from-[#2C221E]/75 via-[#2C221E]/60 to-[#2C221E]/45" />
        <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-b from-transparent to-[#FDFBF7]" />
        <div className="relative mx-auto max-w-5xl px-5 pb-20 pt-6 sm:pb-28">
          <div className="flex items-center justify-between">
            <span className="font-heading text-lg font-bold text-white">Watizat</span>
            <div className="flex gap-1.5" data-testid="language-selector">
              {LANGS.map((code) => (
                <button key={code} onClick={() => i18n.changeLanguage(code)} data-testid={`lang-${code}`}
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase transition-colors ${i18n.language === code ? 'bg-white text-[#2C221E]' : 'bg-white/15 text-white hover:bg-white/30'}`}>
                  {code}
                </button>
              ))}
            </div>
          </div>
          <div className="max-w-2xl pt-16 sm:pt-24">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#F3D9B5]">{t('landingKicker')}</p>
            <h1 className="mt-3 font-heading text-4xl font-bold leading-[1.1] text-white sm:text-6xl" data-testid="landing-title">{t('welcome')}</h1>
            <p className="mt-4 max-w-xl text-lg leading-relaxed text-white/90">{t('tagline')}</p>
            <div className="mt-6 flex flex-wrap gap-2 text-xs font-medium text-white/90">
              {[[Utensils, t('landingFood')], [Home, t('landingHousing')], [Scale, t('landingLegal')], [Briefcase, t('landingWork')]].map(([Icon, l]) => (
                <span key={l} className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5"><Icon size={13} /> {l}</span>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="relative mx-auto -mt-8 max-w-5xl px-5">
        <div className="grid gap-5 md:grid-cols-2">
          <ChoiceCard img={IMG.need} icon={HandHeart} title={t('needHelp')} desc={t('needHelpDesc')} accent="bg-[#C8894F]" onClick={() => navigate('/auth?role=migrant')} testId="need-help-card" cta={t('landingStart')} />
          <ChoiceCard img={IMG.help} icon={HeartHandshake} title={t('wantToHelp')} desc={t('wantToHelpDesc')} accent="bg-[#2A9D8F]" onClick={() => navigate('/auth?role=helper')} testId="want-to-help-card" cta={t('landingStart')} />
        </div>

        <div className="mt-8 flex flex-col items-center gap-3 text-center">
          <p className="text-[#8C827A]">{t('alreadyAccount')}</p>
          <button onClick={() => navigate('/auth')} className="feed-cta feed-cta-outline px-10" data-testid="login-button">{t('login')}</button>
        </div>

        <section className="mt-16 grid items-center gap-8 md:grid-cols-2">
          <div className="grid grid-cols-2 gap-3">
            <img src={IMG.care} alt={t('landingCareAlt')} loading="lazy" className="h-64 w-full rounded-3xl object-cover sm:h-80" />
            <img src={IMG.food} alt={t('landingFoodAlt')} loading="lazy" className="mt-8 h-64 w-full rounded-3xl object-cover sm:h-80" />
          </div>
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-[#E9F5F3] px-3 py-1.5 text-xs font-semibold text-[#1F7A6F]"><Shield size={14} /> {t('forProfessionals')}</span>
            <h2 className="mt-3 font-heading text-3xl font-bold text-[#2C221E]">{t('volunteerTitle')}</h2>
            <p className="mt-3 leading-relaxed text-[#5C524B]">{t('volunteerDesc')}</p>
            <button onClick={() => navigate('/volunteer-register')} className="feed-cta feed-cta-sage mt-6 px-8" data-testid="volunteer-register-button">
              <Shield size={18} /> {t('registerVolunteer')}
            </button>
          </div>
        </section>

        <section className="mt-14 grid gap-4 pb-16 sm:grid-cols-3">
          <Feature icon={Award} title={t('verifiedProfile')} desc={t('verifiedDesc')} />
          <Feature icon={Users} title={t('targetedConnections')} desc={t('targetedDesc')} />
          <Feature icon={HeartHandshake} title={t('impactMeasure')} desc={t('impactDesc')} />
        </section>
      </main>

      <footer className="border-t border-[#ECE5DA] py-8 text-center text-sm text-[#8C827A]">© 2026 Watizat · {t('landingFooter')}</footer>
    </div>
  );
}
