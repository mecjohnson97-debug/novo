import React, { useContext, useEffect, useRef, useState } from 'react';
import { ImagePlus, Loader2, X } from 'lucide-react';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import { Dialog, DialogContent, DialogTitle } from './ui/dialog';
import compressImage from '../utils/compressImage';

const API = process.env.REACT_APP_BACKEND_URL;
const MAX = 6;

export default function ProfilePhotos() {
  const { user, token } = useContext(AuthContext);
  const fileRef = useRef(null);
  const [photos, setPhotos] = useState([]);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState(null);
  const headers = { Authorization: `Bearer ${token}` };

  const load = async () => {
    const res = await fetch(`${API}/api/users/${user.id}/photos`, { headers });
    if (res.ok) setPhotos(await res.json());
  };
  useEffect(() => { void load(); }, [user?.id]);

  const onFile = async (e) => {
    const files = [...(e.target.files || [])].slice(0, MAX - photos.length);
    e.target.value = '';
    if (!files.length) return;
    setBusy(true);
    try {
      for (const file of files) {
        const image = await compressImage(file, 1280, 0.82).catch(() => {
          throw new Error('Formato de foto não suportado. Use JPG, PNG ou WEBP.');
        });
        const res = await fetch(`${API}/api/profile/photos`, { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' }, body: JSON.stringify({ image }) });
        if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Erro ao enviar a foto (${res.status})`);
      }
      toast.success('Foto adicionada!');
    } catch (err) {
      toast.error(err.message || 'Não foi possível enviar a foto');
    } finally {
      setBusy(false);
      void load();
    }
  };

  const remove = async (id) => {
    const res = await fetch(`${API}/api/profile/photos/${id}`, { method: 'DELETE', headers });
    if (res.ok) setPhotos((p) => p.filter((x) => x.id !== id));
  };

  return (
    <div className="border-t border-gray-100 pt-6" data-testid="profile-photos-section">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-bold text-textPrimary">Minhas fotos</h3>
        <span className="text-xs text-textMuted">{photos.length}/{MAX}</span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {photos.map((p, i) => (
          <div key={p.id} className="group relative aspect-square overflow-hidden rounded-xl bg-[#F7F4EE]">
            <button type="button" onClick={() => setView(`${API}${p.url}`)} className="h-full w-full" data-testid={`profile-photo-${i}`}>
              <img src={`${API}${p.url}`} alt="" loading="lazy" className="h-full w-full object-cover" />
            </button>
            <button type="button" onClick={() => remove(p.id)} className="absolute right-1 top-1 rounded-full bg-black/60 p-1 text-white" aria-label="Remover" data-testid={`profile-photo-remove-${i}`}><X size={12} /></button>
          </div>
        ))}
        {photos.length < MAX && (
          <button type="button" onClick={() => fileRef.current?.click()} disabled={busy} data-testid="profile-photo-add-button"
            className="flex aspect-square flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-[#D9CFC2] text-[#8C827A] transition-colors hover:border-[#2A9D8F] hover:text-[#2A9D8F]">
            {busy ? <Loader2 size={22} className="animate-spin" /> : <ImagePlus size={22} />}
            <span className="text-xs font-medium">Adicionar</span>
          </button>
        )}
      </div>
      <input ref={fileRef} type="file" accept="image/*" multiple onChange={onFile} className="hidden" data-testid="profile-photo-file-input" />
      <Dialog open={!!view} onOpenChange={() => setView(null)}>
        <DialogContent className="max-w-3xl border-0 bg-transparent p-0 shadow-none">
          <DialogTitle className="sr-only">Foto</DialogTitle>
          {view && <img src={view} alt="" className="max-h-[85vh] w-full rounded-2xl object-contain" />}
        </DialogContent>
      </Dialog>
    </div>
  );
}
