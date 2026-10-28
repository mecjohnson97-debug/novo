import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';

export default function LoginButtons({ className = '' }) {
  const navigate = useNavigate();

  const handleDefaultLogin = () => {
    navigate('/auth');
  };

  const handleEmailLogin = () => {
    navigate('/auth?method=email');
  };

  const handleGoogleLogin = async () => {
    // Placeholder: iniciar fluxo OAuth Google.
    // Recomendo usar @react-oauth/google ou outro pacote OAuth e chamar aqui.
    // Ex.: abrir modal / chamar hook que troca token e redireciona para /home.
    navigate('/auth?method=google');
  };

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-center gap-3 ${className}`}>
      <Button
        onClick={handleDefaultLogin}
        className="rounded-full px-8 py-3 text-lg"
      >
        Entrar
      </Button>

      <Button
        onClick={handleGoogleLogin}
        variant="outline"
        className="rounded-full px-6 py-3 text-lg bg-white border border-gray-200"
      >
        Entrar com Google
      </Button>

      <Button
        onClick={handleEmailLogin}
        variant="ghost"
        className="rounded-full px-6 py-3 text-lg"
      >
        Entrar com Email
      </Button>
    </div>
  );
}
