import React, { useContext, useRef, useState } from 'react';
import { Camera, Loader2, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { AuthContext } from '../App';
import Avatar from './Avatar';
import compressImage from '../utils/compressImage';

const API = process.env.REACT_APP_BACKEND_URL;

export default function AvatarUploader() {
  const { user, token, login } = useContext(AuthContext);
  const fileRef = useRef(null);
  const [busy, setBusy] = useState(false);

  const save = async (method, body) => {
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/profile/avatar`, {
        method,
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      const { avatar_version } = await res.json();
      login(token, { ...user, avatar_version });
      toast.success(avatar_version ? 'Foto atualizada!' : 'Foto removida');
    } catch (e) {
      toast.error(e.message || 'Não foi possível salvar a foto');
    } finally {
      setBusy(false);
    }
  };

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (!file.type.startsWith('image/')) return toast.error('Escolha uma imagem');
    try {
      const image = await compressImage(file, 400, 0.82);
      await save('PUT', { image });
    } catch {
      toast.error('Não foi possível ler a imagem');
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <button type="button" onClick={() => fileRef.current?.click()} disabled={busy} className="group relative rounded-full" aria-label="Alterar foto de perfil" data-testid="avatar-upload-button">
        <Avatar userId={user?.id} version={user?.avatar_version} name={user?.name} size={104} className="ring-4 ring-[#FEFAE0]" testId="profile-avatar" />
        <span className="absolute bottom-0 right-0 grid h-9 w-9 place-items-center rounded-full border-2 border-white bg-[#2A9D8F] text-white shadow">
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Camera size={16} />}
        </span>
      </button>
      <input ref={fileRef} type="file" accept="image/*" onChange={onFile} className="hidden" data-testid="avatar-file-input" />
      {user?.avatar_version ? (
        <button type="button" onClick={() => save('DELETE')} disabled={busy} className="inline-flex items-center gap-1 text-xs font-medium text-[#8C827A] hover:text-[#B4462B]" data-testid="avatar-remove-button">
          <Trash2 size={12} /> Remover foto
        </button>
      ) : (
        <span className="text-xs text-[#8C827A]">Toque para adicionar sua foto</span>
      )}
    </div>
  );
}
