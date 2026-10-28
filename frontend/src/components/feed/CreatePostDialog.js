import React, { useRef, useState } from 'react';
import { ImagePlus, MapPin, X, Loader2, Video } from 'lucide-react';
import EmojiPicker from '../EmojiPicker';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { CATEGORIES, API, authHeaders } from './feedConfig';
import compressImage from '../../utils/compressImage';

const empty = (role) => ({ type: role === 'migrant' ? 'need' : 'offer', category: 'food', title: '', description: '', images: [], location: null });

export default function CreatePostDialog({ open, onOpenChange, user, token, onCreated }) {
  const fileRef = useRef(null);
  const videoRef = useRef(null);
  const [video, setVideo] = useState(null);
  const [post, setPost] = useState(empty(user?.role));
  const [submitting, setSubmitting] = useState(false);
  const set = (patch) => setPost((p) => ({ ...p, ...patch }));

  const addImage = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (post.images.length >= 4) return toast.error('Máximo de 4 fotos');
    try {
      const img = await compressImage(file);
      setPost((p) => ({ ...p, images: [...p.images, img] }));
    } catch {
      toast.error('Não foi possível ler a imagem');
    }
  };

  const addVideo = (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (!file.type.startsWith('video/') && !/\.(mp4|mov|webm|3gp|mkv|m4v)$/i.test(file.name)) return toast.error('Escolha um arquivo de vídeo');
    if (file.size > 50 * 1024 * 1024) return toast.error('Vídeo muito grande (máximo 50MB)');
    setVideo({ file, preview: URL.createObjectURL(file) });
  };

  const getLocation = () => {
    if (!navigator.geolocation) return toast.error('Seu navegador não suporta geolocalização');
    navigator.geolocation.getCurrentPosition(
      (pos) => { set({ location: { lat: pos.coords.latitude, lng: pos.coords.longitude, address: 'Localização atual' } }); toast.success('Localização adicionada'); },
      () => toast.error('Não foi possível obter a localização'),
      { timeout: 15000 }
    );
  };

  const submit = async () => {
    if (!post.title.trim() || !post.description.trim()) return toast.error('Preencha título e detalhes');
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/api/posts`, {
        method: 'POST',
        headers: { ...authHeaders(token), 'Content-Type': 'application/json' },
        body: JSON.stringify(post),
      });
      if (!res.ok) throw new Error();
      let videoFailed = false;
      if (video) {
        const created = await res.json();
        const fd = new FormData();
        fd.append('file', video.file);
        const vr = await fetch(`${API}/api/posts/${created.id}/video`, { method: 'POST', headers: authHeaders(token), body: fd });
        if (!vr.ok) {
          videoFailed = true;
          const detail = (await vr.json().catch(() => ({}))).detail;
          toast.error(`Post publicado, mas o vídeo não foi enviado${detail ? `: ${detail}` : ` (erro ${vr.status})`}`);
        }
      }
      if (!videoFailed) toast.success('Publicado com sucesso!');
      setPost(empty(user?.role));
      setVideo(null);
      onOpenChange(false);
      onCreated();
    } catch {
      toast.error('Erro ao publicar');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="feed-dialog flex max-h-[90vh] max-w-xl flex-col rounded-3xl" data-testid="create-post-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading text-2xl text-[#2C221E]">Nova publicação</DialogTitle>
          <DialogDescription>Conte com clareza o que você precisa ou oferece.</DialogDescription>
        </DialogHeader>

        <div className="-mx-1 flex-1 space-y-5 overflow-y-auto px-1 py-1">
          <div className="grid grid-cols-2 gap-2">
            {[['need', 'Preciso de ajuda'], ['offer', 'Quero ajudar']].map(([k, l]) => (
              <button key={k} onClick={() => set({ type: k })} className={`feed-type py-2.5 ${post.type === k ? 'is-active' : ''}`} data-testid={`create-post-type-${k}`}>{l}</button>
            ))}
          </div>

          <div>
            <p className="feed-label">Categoria</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {CATEGORIES.map(({ value, label, icon: Icon }) => (
                <button key={value} onClick={() => set({ category: value })} className={`feed-chip justify-start ${post.category === value ? 'is-active' : ''}`} data-testid={`create-post-category-${value}`}>
                  <Icon size={15} /> {label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="feed-label">Título</p>
            <div className="flex items-center gap-1">
              <input value={post.title} onChange={(e) => set({ title: e.target.value })} placeholder="Ex: Preciso de roupas de inverno" className="feed-input w-full" data-testid="create-post-title-input" />
              <EmojiPicker onPick={(em) => setPost((p) => ({ ...p, title: p.title + em }))} testId="create-post-title-emoji-button" />
            </div>
          </div>

          <div>
            <p className="feed-label">Detalhes</p>
            <textarea value={post.description} onChange={(e) => set({ description: e.target.value })} rows={4} placeholder="Tamanhos, quantidades, quando precisa…" className="feed-input w-full resize-none" data-testid="create-post-description-input" />
            <div className="mt-1 flex items-center gap-1 text-xs text-[#8C827A]">
              <EmojiPicker onPick={(em) => setPost((p) => ({ ...p, description: p.description + em }))} testId="create-post-emoji-button" /> Adicionar emoji
            </div>
          </div>

          <div className="flex gap-2">
            <button onClick={() => fileRef.current?.click()} className="feed-ghost border border-[#E8E2D9]" data-testid="create-post-add-image"><ImagePlus size={16} /> Foto</button>
            <button onClick={() => videoRef.current?.click()} className="feed-ghost border border-[#E8E2D9]" data-testid="create-post-add-video"><Video size={16} /> Vídeo</button>
            <button onClick={getLocation} className="feed-ghost border border-[#E8E2D9]" data-testid="create-post-add-location"><MapPin size={16} /> {post.location ? 'Localização ok' : 'Localização'}</button>
            <input ref={fileRef} type="file" accept="image/*" onChange={addImage} className="hidden" data-testid="create-post-file-input" />
            <input ref={videoRef} type="file" accept="video/*" onChange={addVideo} className="hidden" data-testid="create-post-video-input" />
          </div>

          {video && (
            <div className="relative overflow-hidden rounded-xl bg-black" data-testid="create-post-video-preview">
              <video src={video.preview} controls className="max-h-56 w-full" />
              <button onClick={() => setVideo(null)} className="absolute right-2 top-2 rounded-full bg-black/60 p-1 text-white" data-testid="create-post-remove-video"><X size={14} /></button>
            </div>
          )}

          {post.images.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {post.images.map((img, i) => (
                <div key={i} className="relative h-20 w-20 overflow-hidden rounded-xl">
                  <img src={img} alt="" className="h-full w-full object-cover" />
                  <button onClick={() => set({ images: post.images.filter((_, j) => j !== i) })} className="absolute right-1 top-1 rounded-full bg-black/60 p-0.5 text-white" data-testid={`create-post-remove-image-${i}`}><X size={12} /></button>
                </div>
              ))}
            </div>
          )}
        </div>

        <button onClick={submit} disabled={submitting} className="feed-cta feed-cta-gold mt-2 w-full" data-testid="create-post-submit-btn">
          {submitting ? <><Loader2 size={18} className="animate-spin" /> {video ? 'Enviando vídeo…' : 'Publicando…'}</> : 'Publicar agora'}
        </button>
      </DialogContent>
    </Dialog>
  );
}
