import React from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Copy } from 'lucide-react';
import { toast } from 'sonner';
import { brl, copyText } from '../utils/money';

export default function PixQr({ code, amount, receiver, testPrefix = 'pix' }) {
  const copy = async () => {
    if (await copyText(code)) toast.success('Código Pix copiado!');
    else toast.error('Não foi possível copiar');
  };
  return (
    <div className="vz-pix-card" data-testid={`${testPrefix}-card`}>
      <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-start">
        <div className="rounded-2xl bg-white p-3" data-testid={`${testPrefix}-qrcode`}>
          <QRCodeSVG value={code} size={196} level="M" />
        </div>
        <div className="min-w-0 flex-1 text-center sm:text-left">
          <p className="text-xs font-semibold uppercase tracking-wider text-[#32BCAD]">Pague com Pix</p>
          <p className="mt-1 font-mono text-3xl font-bold text-white" data-testid={`${testPrefix}-amount`}>{brl(amount)}</p>
          {receiver && <p className="mt-1 text-sm text-slate-400">Recebedor: {receiver}</p>}
          <ol className="mt-4 space-y-1 text-left text-sm text-slate-300">
            <li>1. Abra o app do seu banco e escolha <b>Pix</b>.</li>
            <li>2. Escaneie o QR Code ou use o <b>Pix Copia e Cola</b>.</li>
            <li>3. Confirme o valor e pague.</li>
          </ol>
        </div>
      </div>
      <div className="mt-5">
        <p className="mb-1.5 text-xs font-medium text-slate-400">Pix Copia e Cola</p>
        <div className="flex gap-2">
          <code className="min-w-0 flex-1 truncate rounded-xl border border-slate-700 bg-slate-950/60 px-3 py-3 font-mono text-xs text-slate-300" data-testid={`${testPrefix}-code`}>{code}</code>
          <button onClick={copy} className="vz-btn-pix shrink-0 px-4" data-testid={`${testPrefix}-copy-button`}><Copy size={16} /> Copiar</button>
        </div>
      </div>
    </div>
  );
}
