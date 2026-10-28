import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

export const LANGS = [
  { code: 'pt', label: 'Português' },
  { code: 'fr', label: 'Français' },
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Español' },
];

export default function LanguageSwitcher({ className = '' }) {
  const { i18n } = useTranslation();
  const current = (i18n.language || 'pt').slice(0, 2);
  return (
    <div className={`notranslate flex items-center gap-2 ${className}`} data-testid="app-language-switcher">
      <Globe size={18} className="text-[#2A9D8F]" />
      <div className="flex flex-wrap gap-1.5">
        {LANGS.map(({ code, label }) => (
          <button key={code} type="button" onClick={() => i18n.changeLanguage(code)} data-testid={`app-lang-${code}`}
            className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${current === code ? 'bg-[#2A9D8F] text-white' : 'bg-[#F1EBE1] text-[#5C524B] hover:bg-[#E8E2D9]'}`}>
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
