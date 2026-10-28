import React, { useState } from 'react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';

const API = process.env.REACT_APP_BACKEND_URL;

const post = async (path, body) => {
  const res = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Verifique os dados informados');
  return data;
};

export default function ForgotPasswordDialog({ open, onOpenChange, initialEmail = '' }) {
  const [step, setStep] = useState('email');
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);

  const close = (v) => {
    onOpenChange(v);
    if (!v) { setStep('email'); setCode(''); setPassword(''); setConfirm(''); }
  };

  const requestCode = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await post('/api/auth/forgot-password', { email });
      toast.success(data.message);
      setStep('reset');
    } catch (err) { toast.error(err.message); } finally { setLoading(false); }
  };

  const reset = async (e) => {
    e.preventDefault();
    if (password.length < 6) return toast.error('A senha deve ter pelo menos 6 caracteres');
    if (password !== confirm) return toast.error('As senhas não coincidem');
    setLoading(true);
    try {
      await post('/api/auth/reset-password', { email, code, new_password: password });
      toast.success('Senha redefinida! Faça login com a nova senha.');
      close(false);
    } catch (err) { toast.error(err.message); } finally { setLoading(false); }
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-w-md rounded-2xl" data-testid="forgot-password-dialog">
        <DialogHeader>
          <DialogTitle>Recuperar senha</DialogTitle>
          <DialogDescription>
            {step === 'email' ? 'Informe seu e-mail e enviaremos um código de 6 dígitos.' : `Digite o código enviado para ${email} e escolha uma nova senha.`}
          </DialogDescription>
        </DialogHeader>
        {step === 'email' ? (
          <form onSubmit={requestCode} className="space-y-4">
            <div>
              <Label htmlFor="fp-email">E-mail</Label>
              <Input id="fp-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="rounded-xl" data-testid="forgot-email-input" />
            </div>
            <Button type="submit" disabled={loading} className="w-full rounded-full" data-testid="forgot-send-code-button">{loading ? 'Enviando...' : 'Enviar código'}</Button>
          </form>
        ) : (
          <form onSubmit={reset} className="space-y-4">
            <div>
              <Label htmlFor="fp-code">Código</Label>
              <Input id="fp-code" inputMode="numeric" maxLength={6} required value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} className="rounded-xl tracking-[0.4em] text-center text-lg" data-testid="forgot-code-input" />
            </div>
            <div>
              <Label htmlFor="fp-pass">Nova senha</Label>
              <Input id="fp-pass" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="rounded-xl" data-testid="forgot-new-password-input" />
            </div>
            <div>
              <Label htmlFor="fp-confirm">Confirmar nova senha</Label>
              <Input id="fp-confirm" type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} className="rounded-xl" data-testid="forgot-confirm-password-input" />
            </div>
            <Button type="submit" disabled={loading || code.length !== 6} className="w-full rounded-full" data-testid="forgot-reset-button">{loading ? 'Salvando...' : 'Redefinir senha'}</Button>
            <button type="button" onClick={() => setStep('email')} className="w-full text-sm text-textSecondary hover:text-primary" data-testid="forgot-resend-link">Não recebeu? Enviar novamente</button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
