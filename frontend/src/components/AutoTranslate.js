import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const API = process.env.REACT_APP_BACKEND_URL;
const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'CODE', 'PRE', 'TEXTAREA', 'SVG', 'PATH']);
const ATTRS = ['placeholder', 'title', 'aria-label'];
const original = new WeakMap();
const attrOriginal = new WeakMap();

const cacheKey = (lang) => `tr_cache_${lang}`;
const loadCache = (lang) => { try { return JSON.parse(localStorage.getItem(cacheKey(lang))) || {}; } catch { return {}; } };

const translatable = (s) => {
  const t = s.trim();
  return t.length > 1 && /\p{L}{2,}/u.test(t) && !/^[\w.+-]+@[\w.-]+\.\w+$/.test(t) && !/^https?:\/\//.test(t);
};

const skipped = (el) => {
  for (let e = el; e && e !== document.body; e = e.parentElement) {
    if (SKIP_TAGS.has(e.tagName) || e.isContentEditable || e.classList?.contains('notranslate') || e.hasAttribute?.('data-no-translate')) return true;
  }
  return false;
};

export default function AutoTranslate() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || 'pt').slice(0, 2);

  useEffect(() => {
    document.documentElement.lang = lang;
    const cache = loadCache(lang);
    const pending = new Map();
    let timer = null;
    let inflight = false;

    const apply = (text) => cache[text.trim()];

    const handleText = (node) => {
      const cur = node.nodeValue;
      const rec = original.get(node);
      if (rec && rec.done && cur === rec.shown) return;
      const src = cur;
      if (lang === 'pt') { if (rec) original.delete(node); return; }
      if (!translatable(src) || skipped(node.parentElement)) return;
      const hit = apply(src);
      if (hit !== undefined) {
        const shown = src.replace(src.trim(), hit);
        original.set(node, { src, shown, done: true });
        node.nodeValue = shown;
      } else {
        original.set(node, { src, shown: src, done: false });
        pending.set(src.trim(), true);
      }
    };

    const handleAttrs = (el) => {
      if (skipped(el)) return;
      const rec = attrOriginal.get(el) || {};
      ATTRS.forEach((a) => {
        const v = el.getAttribute(a);
        if (!v || (rec[a]?.done && v === rec[a].shown)) return;
        if (lang === 'pt' || !translatable(v)) return;
        const hit = apply(v);
        if (hit !== undefined) { rec[a] = { src: v, shown: hit, done: true }; el.setAttribute(a, hit); }
        else { rec[a] = { src: v, shown: v, done: false }; pending.set(v.trim(), true); }
      });
      attrOriginal.set(el, rec);
    };

    const scan = (root) => {
      if (!root) return;
      if (root.nodeType === Node.TEXT_NODE) return handleText(root);
      if (root.nodeType !== Node.ELEMENT_NODE || SKIP_TAGS.has(root.tagName)) return;
      handleAttrs(root);
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
      let n = walker.nextNode();
      while (n) {
        if (n.nodeType === Node.TEXT_NODE) handleText(n); else handleAttrs(n);
        n = walker.nextNode();
      }
      schedule();
    };

    const flush = async () => {
      if (inflight || pending.size === 0) return;
      inflight = true;
      const texts = [...pending.keys()].slice(0, 120);
      texts.forEach((t) => pending.delete(t));
      try {
        const res = await fetch(`${API}/api/translate`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ texts, lang }),
        });
        if (res.ok) {
          const { translations } = await res.json();
          texts.forEach((t, i) => { cache[t] = translations[i]; });
          try { localStorage.setItem(cacheKey(lang), JSON.stringify(cache)); } catch { /* quota */ }
          scan(document.body);
        }
      } catch { /* offline */ }
      inflight = false;
      if (pending.size) schedule();
    };

    const schedule = () => { clearTimeout(timer); timer = setTimeout(flush, 250); };

    const restore = () => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
      let n = walker.nextNode();
      while (n) {
        if (n.nodeType === Node.TEXT_NODE) {
          const rec = original.get(n);
          if (rec && n.nodeValue === rec.shown) n.nodeValue = rec.src;
          original.delete(n);
        } else {
          const rec = attrOriginal.get(n);
          if (rec) Object.entries(rec).forEach(([a, r]) => { if (n.getAttribute(a) === r.shown) n.setAttribute(a, r.src); });
          attrOriginal.delete(n);
        }
        n = walker.nextNode();
      }
    };

    restore();
    if (lang === 'pt') return undefined;
    scan(document.body);
    const observer = new MutationObserver((muts) => {
      muts.forEach((m) => {
        if (m.type === 'characterData') handleText(m.target);
        else if (m.type === 'attributes') handleAttrs(m.target);
        else m.addedNodes.forEach(scan);
      });
      schedule();
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    return () => { observer.disconnect(); clearTimeout(timer); };
  }, [lang]);

  return null;
}
