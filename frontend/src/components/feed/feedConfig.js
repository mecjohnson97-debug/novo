import { Utensils, Scale, HeartPulse, Home, Briefcase, GraduationCap, Users, Shirt, Armchair, Truck } from 'lucide-react';

export const API = process.env.REACT_APP_BACKEND_URL;

export const CATEGORIES = [
  { value: 'food', label: 'Alimentação', icon: Utensils, badge: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
  { value: 'legal', label: 'Jurídico', icon: Scale, badge: 'bg-sky-50 text-sky-800 border-sky-200' },
  { value: 'health', label: 'Saúde', icon: HeartPulse, badge: 'bg-rose-50 text-rose-800 border-rose-200' },
  { value: 'housing', label: 'Moradia', icon: Home, badge: 'bg-purple-50 text-purple-800 border-purple-200' },
  { value: 'work', label: 'Trabalho', icon: Briefcase, badge: 'bg-amber-50 text-amber-800 border-amber-200' },
  { value: 'education', label: 'Educação', icon: GraduationCap, badge: 'bg-indigo-50 text-indigo-800 border-indigo-200' },
  { value: 'social', label: 'Social', icon: Users, badge: 'bg-pink-50 text-pink-800 border-pink-200' },
  { value: 'clothes', label: 'Roupas', icon: Shirt, badge: 'bg-orange-50 text-orange-800 border-orange-200' },
  { value: 'furniture', label: 'Móveis', icon: Armchair, badge: 'bg-teal-50 text-teal-800 border-teal-200' },
  { value: 'transport', label: 'Transporte', icon: Truck, badge: 'bg-cyan-50 text-cyan-800 border-cyan-200' },
];

export const TYPES = {
  need: { label: 'Precisa de ajuda', badge: 'bg-[#FDF0ED] text-[#B4462B] border-[#F5C9BC]' },
  offer: { label: 'Oferece ajuda', badge: 'bg-[#E9F5F3] text-[#1F7A6F] border-[#BFE3DD]' },
  job: { label: 'Vaga de emprego', badge: 'bg-[#FEFAE0] text-[#8A5A2B] border-[#EBD9B4]' },
};

export const ROLES = {
  migrant: 'Migrante',
  volunteer: 'Voluntário',
  helper: 'Ajudante',
  admin: 'Admin',
  assistant: 'Assistente',
};

export const getCategory = (value) => CATEGORIES.find((c) => c.value === value);

export const authHeaders = (token) => ({ Authorization: `Bearer ${token}` });
