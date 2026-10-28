import React from 'react';
import { LayoutGrid } from 'lucide-react';
import { CATEGORIES, TYPES } from './feedConfig';

export default function FeedFilters({ category, type, onCategory, onType }) {
  return (
    <div className="space-y-2.5" data-testid="feed-filters">
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        <button
          onClick={() => onCategory('all')}
          className={`feed-chip ${category === 'all' ? 'is-active' : ''}`}
          data-testid="category-chip-all"
        >
          <LayoutGrid size={15} /> Todas
        </button>
        {CATEGORIES.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => onCategory(value)}
            className={`feed-chip ${category === value ? 'is-active' : ''}`}
            data-testid={`category-chip-${value}`}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>
      <div className="flex gap-1.5 overflow-x-auto scrollbar-hide">
        {[['all', 'Todos'], ...Object.entries(TYPES).map(([k, v]) => [k, v.label])].map(([key, label]) => (
          <button
            key={key}
            onClick={() => onType(key)}
            className={`feed-type ${type === key ? 'is-active' : ''}`}
            data-testid={`type-filter-${key}`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
