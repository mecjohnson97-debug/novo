import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { MapPin, MessageSquare, MessageCircle, Clock } from 'lucide-react';
import { Dialog, DialogContent, DialogTitle } from '../ui/dialog';
import PostComments from './PostComments';
import Avatar from '../Avatar';
import { API, ROLES, TYPES, getCategory } from './feedConfig';

const timeAgo = (iso) => {
  try { return formatDistanceToNow(new Date(iso), { addSuffix: true, locale: ptBR }); } catch { return ''; }
};

const linkify = (text) =>
  (text || '').split(/(https?:\/\/[^\s]+)/g).map((part, i) =>
    /^https?:\/\//.test(part)
      ? <a key={i} href={part} target="_blank" rel="noopener noreferrer" className="text-[#1F7A6F] underline break-all">{part}</a>
      : part
  );

export default function PostCard({ post, token, currentUserId, onChat, index = 0 }) {
  const [open, setOpen] = useState(false);
  const [lightbox, setLightbox] = useState(null);
  const [count, setCount] = useState(post.comment_count || 0);
  const name = post.user?.name || 'Usuário';
  const type = TYPES[post.type];
  const images = (post.image_urls || []).map((u) => `${API}${u}`);
  const canChat = post.user_id !== 'system' && post.user_id !== currentUserId;

  return (
    <article className="feed-card p-5 fade-up" style={{ animationDelay: `${Math.min(index, 6) * 60}ms` }} data-testid={`post-card-${post.id}`}>
      <header className="flex items-center gap-3">
        <Avatar userId={post.user?.id} version={post.user?.avatar_version} name={name} testId={`post-avatar-${post.id}`} />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold text-[#2C221E]" data-testid={`post-author-${post.id}`}>{name}</p>
          <p className="flex items-center gap-1.5 whitespace-nowrap text-xs text-[#8C827A]">
            {ROLES[post.user?.role] || 'Membro'} <span>·</span> <Clock size={11} className="flex-shrink-0" /> <span className="truncate">{timeAgo(post.created_at)}</span>
          </p>
        </div>
        {type && <span className={`feed-badge ${type.badge}`} data-testid={`post-type-${post.id}`}>{type.label}</span>}
      </header>

      <h3 className="mt-4 font-heading text-lg font-semibold leading-snug text-[#2C221E]" data-testid={`post-title-${post.id}`}>{post.title}</h3>
      <p className="mt-1.5 whitespace-pre-line text-[15px] leading-relaxed text-[#5C524B]">{linkify(post.description)}</p>

      {images.length > 0 && (
        <div className={`mt-4 grid gap-2 ${images.length > 1 ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {images.slice(0, 4).map((src, i) => (
            <button key={src} onClick={() => setLightbox(src)} className="overflow-hidden rounded-xl bg-[#F7F4EE]" data-testid={`post-image-${post.id}-${i}`}>
              <img src={src} alt="" loading="lazy" decoding="async" className={`w-full object-cover ${images.length > 1 ? 'h-40' : 'max-h-96'}`} />
            </button>
          ))}
        </div>
      )}

      {post.video_url && (
        <video src={`${API}${post.video_url}`} controls playsInline preload="metadata" className="mt-4 max-h-[28rem] w-full rounded-xl bg-black" data-testid={`post-video-${post.id}`} />
      )}

      <div className="mt-4 flex flex-wrap items-center gap-1.5">
        {(post.categories || []).map((c) => {
          const cat = getCategory(c);
          if (!cat) return null;
          const Icon = cat.icon;
          return <span key={c} className={`feed-badge ${cat.badge}`}><Icon size={12} /> {cat.label}</span>;
        })}
        {post.location && (
          <span className="feed-badge border-[#E8E2D9] bg-white text-[#5C524B]"><MapPin size={12} /> {post.location.address || 'Localização'}</span>
        )}
      </div>

      <footer className="mt-4 flex items-center gap-2 border-t border-[#EFE8DD] pt-3">
        <button onClick={() => setOpen(!open)} className="feed-ghost" data-testid={`post-comments-toggle-${post.id}`}>
          <MessageSquare size={16} /> {count > 0 ? `${count} comentário${count > 1 ? 's' : ''}` : 'Comentar'}
        </button>
        {canChat && (
          <button onClick={() => onChat(post.user_id)} className="feed-ghost ml-auto text-[#1F7A6F]" data-testid={`post-chat-button-${post.id}`}>
            <MessageCircle size={16} /> Conversar
          </button>
        )}
      </footer>

      {open && <PostComments postId={post.id} token={token} onAdded={() => setCount((n) => n + 1)} />}

      <Dialog open={!!lightbox} onOpenChange={() => setLightbox(null)}>
        <DialogContent className="max-w-3xl border-0 bg-transparent p-0 shadow-none">
          <DialogTitle className="sr-only">Imagem do post</DialogTitle>
          {lightbox && <img src={lightbox} alt="" className="max-h-[85vh] w-full rounded-2xl object-contain" />}
        </DialogContent>
      </Dialog>
    </article>
  );
}
