import React, { useEffect, useState } from 'react';
import { ExternalLink, Phone, Megaphone } from 'lucide-react';
import { API } from './feedConfig';

const LABELS = { job: 'Vaga', donation: 'Doação', motivation: 'Inspiração' };

export default function FeedSidebar() {
  const [items, setItems] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/sidebar-content`)
      .then((r) => (r.ok ? r.json() : { items: [] }))
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]));
  }, []);

  return (
    <aside className="hidden w-80 flex-shrink-0 space-y-4 lg:block" data-testid="sidebar-advertisements">
      <div className="feed-card overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1596450514537-fae68a81346b?crop=entropy&cs=srgb&fm=jpg&w=640&q=70"
          alt="Comunidade"
          loading="lazy"
          className="h-36 w-full object-cover"
        />
        <div className="p-4">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-[#A0703F]"><Megaphone size={13} /> Mural</p>
          <p className="mt-1 text-sm text-[#5C524B]">Vagas, doações e mensagens de apoio da comunidade.</p>
        </div>
      </div>

      {items === null && <div className="feed-card h-40 animate-pulse bg-[#F7F4EE]" />}

      {(items || []).slice(0, 6).map((item, idx) => {
        const kind = item.item_type || item.type;
        return (
          <div key={item.id || idx} className="feed-card p-4" data-testid={`sidebar-item-${idx}`}>
            <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#A0703F]">{LABELS[kind] || 'Aviso'}</span>
            <h4 className="mt-1 line-clamp-2 text-sm font-semibold text-[#2C221E]">{item.title}</h4>
            {item.content && <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-[#5C524B]">{item.content}</p>}
            {item.link_url && (
              <a href={item.link_url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#1F7A6F] hover:underline">
                {item.link_text || 'Saiba mais'} <ExternalLink size={12} />
              </a>
            )}
          </div>
        );
      })}

      <div className="feed-card border-[#F5C9BC] bg-[#FDF0ED] p-4" data-testid="sidebar-emergency">
        <p className="text-sm font-semibold text-[#B4462B]">Contatos de emergência</p>
        <ul className="mt-2 space-y-1.5 text-sm text-[#5C524B]">
          <li><a href="tel:112" className="inline-flex items-center gap-2 hover:underline"><Phone size={13} /> 112 · Emergência</a></li>
          <li><a href="tel:115" className="inline-flex items-center gap-2 hover:underline"><Phone size={13} /> 115 · SAMU Social (abrigo)</a></li>
        </ul>
      </div>
    </aside>
  );
}
