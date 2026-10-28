import React from 'react';
import { FileText } from 'lucide-react';
import { getCategory } from './feedConfig';

export const catIcon = (value, size = 16) => {
  const Icon = getCategory(value)?.icon || FileText;
  return <Icon size={size} className="inline-block align-[-2px]" />;
};
