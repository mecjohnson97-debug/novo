import React, { useState } from 'react';
import { CalendarCheck, Clock, MapPin, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../ui/button';
import { MODES } from './AppointmentDialog';

const STATUS = {
  pending: { label: 'Aguardando resposta', cls: 'bg-yellow-100 text-yellow-800' },
  accepted: { label: 'Aceito', cls: 'bg-green-100 text-green-800' },
  declined: { label: 'Recusado', cls: 'bg-red-100 text-red-700' },
  cancelled: { label: 'Cancelado', cls: 'bg-gray-200 text-gray-700' },
};

export default function AppointmentCard({ msg, isMine, token, onChanged }) {
  const appt = msg.appointment;
  const [busy, setBusy] = useState(false);
  const [y, m, d] = appt.date.split('-');
  const status = STATUS[appt.status] || STATUS.pending;
  const modeLabel = MODES.find(x => x.value === appt.mode)?.label || appt.mode;

  const respond = async (action) => {
    setBusy(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/appointments/${msg.id}/respond`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erro');
      onChanged?.();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white text-[#2C221E] rounded-2xl border-2 border-[#2A9D8F]/30 shadow-sm w-72 sm:w-80 overflow-hidden" data-testid="appointment-card">
      <div className="bg-[#E9F5F3] px-4 py-2 flex items-center justify-between">
        <span className="flex items-center gap-2 text-sm font-bold text-[#1F7A6F]"><CalendarCheck size={16} /> Agendamento</span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${status.cls}`} data-testid="appointment-status">{status.label}</span>
      </div>
      <div className="px-4 py-3 space-y-2 text-sm">
        <p className="flex items-center gap-2 font-semibold"><Clock size={16} className="text-[#2A9D8F]" /> {`${d}/${m}/${y}`} às {appt.time}</p>
        <p className="flex items-center gap-2"><MapPin size={16} className="text-[#2A9D8F]" /> {modeLabel}</p>
        {appt.info ? (
          <p className="bg-[#F7F4EE] rounded-lg p-2 whitespace-pre-wrap" data-testid="appointment-info">{appt.info}</p>
        ) : appt.has_info ? (
          <p className="flex items-center gap-2 text-xs text-[#8C827A]"><Lock size={14} /> Informações práticas reveladas após aceitar</p>
        ) : null}
        {appt.status === 'pending' && !isMine && (
          <div className="flex gap-2 pt-1">
            <Button size="sm" disabled={busy} onClick={() => respond('accept')} className="flex-1 rounded-full bg-[#2A9D8F] hover:bg-[#238578]" data-testid="appointment-accept-button">Aceitar</Button>
            <Button size="sm" disabled={busy} variant="outline" onClick={() => respond('decline')} className="flex-1 rounded-full" data-testid="appointment-decline-button">Recusar</Button>
          </div>
        )}
        {appt.status === 'pending' && isMine && (
          <Button size="sm" disabled={busy} variant="ghost" onClick={() => respond('cancel')} className="w-full rounded-full text-red-600 hover:bg-red-50" data-testid="appointment-cancel-button">Cancelar proposta</Button>
        )}
      </div>
    </div>
  );
}
