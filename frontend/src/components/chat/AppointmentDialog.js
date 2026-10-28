import React, { useState } from 'react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { CalendarDays, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Calendar } from '../ui/calendar';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';

export const MODES = [
  { value: 'in_person', label: 'Presencial' },
  { value: 'video', label: 'Chamada de vídeo' },
  { value: 'phone', label: 'Telefone' },
  { value: 'other', label: 'Outro' },
];

const BENEFITS = ['Compromisso mútuo', 'Data e hora registradas na conversa', 'Endereço revelado só após aceite', 'Confirmação ou recusa com um toque'];

const today = () => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; };

export default function AppointmentDialog({ open, onOpenChange, otherName, toUserId, token, onCreated }) {
  const [date, setDate] = useState(today());
  const [calOpen, setCalOpen] = useState(false);
  const [time, setTime] = useState('');
  const [mode, setMode] = useState('in_person');
  const [info, setInfo] = useState('');
  const [ack, setAck] = useState(false);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!date || !time) return toast.error('Escolha a data e a hora');
    if (!ack) return toast.error('Marque a caixa de confirmação');
    setSaving(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/appointments`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ to_user_id: toUserId, date: format(date, 'yyyy-MM-dd'), time, mode, info, acknowledged: ack }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Erro ao agendar');
      toast.success('Agendamento proposto!');
      setTime(''); setInfo(''); setAck(false); setMode('in_person'); setDate(today());
      onOpenChange(false);
      onCreated?.();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[92vh] overflow-y-auto rounded-2xl" data-testid="appointment-dialog">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-[#2C221E]">Propor um agendamento</DialogTitle>
        </DialogHeader>

        <div className="bg-[#E9F5F3] rounded-xl p-4 text-sm text-[#2C221E]">
          <p className="font-semibold mb-1">Vantagens do agendamento:</p>
          <ul className="list-disc pl-5 space-y-0.5">{BENEFITS.map(b => <li key={b}>{b}</li>)}</ul>
        </div>

        <div className="space-y-2">
          <Label>Data</Label>
          <Popover open={calOpen} onOpenChange={setCalOpen}>
            <PopoverTrigger asChild>
              <button type="button" data-testid="appointment-date-button"
                className="w-full flex items-center justify-between border-2 border-[#2C221E]/70 rounded-xl px-4 py-3 text-left hover:border-[#2A9D8F] transition-colors">
                <span>{date ? format(date, 'dd/MM/yyyy') : 'Escolha uma data'}</span>
                <CalendarDays size={20} />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar mode="single" selected={date} locale={ptBR} disabled={{ before: today() }}
                onSelect={(d) => { if (d) { setDate(d); setCalOpen(false); } }} initialFocus data-testid="appointment-calendar" />
            </PopoverContent>
          </Popover>
        </div>

        <div className="space-y-2">
          <Label htmlFor="appt-time">Hora</Label>
          <div className="relative">
            <input id="appt-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} data-testid="appointment-time-input"
              className="w-full border-2 border-[#2C221E]/20 rounded-xl px-4 py-3 focus:outline-none focus:border-[#2A9D8F]" />
            <Clock size={20} className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-[#5C524B]" />
          </div>
        </div>

        <div className="space-y-2">
          <Label>Modo do encontro</Label>
          <RadioGroup value={mode} onValueChange={setMode} className="space-y-1">
            {MODES.map(m => (
              <div key={m.value} className="flex items-center gap-3">
                <RadioGroupItem value={m.value} id={`mode-${m.value}`} data-testid={`appointment-mode-${m.value}`} />
                <Label htmlFor={`mode-${m.value}`} className="font-normal cursor-pointer">{m.label}</Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <Label htmlFor="appt-info">Informações práticas</Label>
            <span className="text-xs text-[#8C827A]">Opcional</span>
          </div>
          <Textarea id="appt-info" value={info} maxLength={500} rows={4} onChange={(e) => setInfo(e.target.value)}
            placeholder="Ex.: Endereço, andar, código do portão, interfone..." className="rounded-xl" data-testid="appointment-info-input" />
          <p className="text-xs text-right text-[#8C827A]">{info.length}/500 máx.</p>
        </div>

        <label className="flex items-start gap-3 cursor-pointer text-sm text-[#2C221E]">
          <Checkbox checked={ack} onCheckedChange={(v) => setAck(!!v)} className="mt-0.5" data-testid="appointment-ack-checkbox" />
          <span>Entendo que o endereço e as informações práticas serão comunicados quando o agendamento for aceito por {otherName || 'esta pessoa'}.</span>
        </label>

        <div className="flex justify-center pt-2">
          <Button onClick={submit} disabled={saving} data-testid="appointment-submit-button"
            className="rounded-full px-8 py-6 text-base font-bold bg-[#2C3E50] hover:bg-[#1F2D3A]">
            {saving ? 'Enviando...' : 'Propor o agendamento'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
