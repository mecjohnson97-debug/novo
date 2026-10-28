import React, { useEffect, useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { API, authHeaders, ROLES } from './feedConfig';
import Avatar from '../Avatar';
import EmojiPicker from '../EmojiPicker';

export default function PostComments({ postId, token, onAdded }) {
  const [items, setItems] = useState(null);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);

  const load = async () => {
    const res = await fetch(`${API}/api/posts/${postId}/comments`, { headers: authHeaders(token) });
    if (res.ok) setItems(await res.json());
    else setItems([]);
  };

  useEffect(() => { void load(); }, [postId]);

  const send = async () => {
    if (!text.trim()) return;
    setSending(true);
    try {
      const res = await fetch(`${API}/api/posts/${postId}/comments`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment: text.trim() }),
      });
      if (!res.ok) throw new Error();
      setText('');
      onAdded?.();
      void load();
    } catch {
      toast.error('Erro ao adicionar comentário');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="mt-4 border-t border-[#EFE8DD] pt-4" data-testid={`post-comments-${postId}`}>
      {items === null ? (
        <p className="text-xs text-[#8C827A]">Carregando comentários…</p>
      ) : items.length === 0 ? (
        <p className="text-xs text-[#8C827A]">Seja o primeiro a comentar.</p>
      ) : (
        <ul className="space-y-2.5">
          {items.map((c) => (
            <li key={c.id} className="flex gap-2.5">
              <Avatar userId={c.user?.id} version={c.user?.avatar_version} name={c.user?.name} size={30} />
              <div className="min-w-0 flex-1 rounded-xl bg-[#F7F4EE] px-3 py-2">
              <p className="text-xs font-semibold text-[#2C221E]">
                {c.user?.name || 'Usuário'} <span className="font-normal text-[#8C827A]">· {ROLES[c.user?.role] || ''}</span>
              </p>
              <p className="text-sm text-[#5C524B]">{c.comment}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-3 flex items-center gap-2">
        <EmojiPicker onPick={(em) => setText((t) => t + em)} testId={`post-comment-emoji-${postId}`} />
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Escreva um comentário gentil…"
          className="feed-input flex-1"
          data-testid={`post-comment-input-${postId}`}
        />
        <button onClick={send} disabled={sending} className="feed-icon-btn" data-testid={`post-comment-submit-${postId}`} aria-label="Enviar">
          {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  );
}
