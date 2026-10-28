import React, { useContext } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Home, MessageCircle, Search, User, Settings, Users, MapPin, Briefcase } from 'lucide-react';
import { AuthContext } from '../App';
import { useTranslation } from 'react-i18next';

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useContext(AuthContext);
  const { t } = useTranslation();

  const navItems = [
    { icon: Home, label: 'Home', path: '/home', testId: 'nav-home' },
    { icon: Briefcase, label: t('work'), path: '/jobs', testId: 'nav-jobs' },
    { icon: Users, label: t('helpNav'), path: '/volunteers', testId: 'nav-volunteers' },
    { icon: MessageCircle, label: t('chat'), path: '/chat', testId: 'nav-chat' },
    { icon: MapPin, label: t('map'), path: '/nearby', testId: 'nav-nearby' },
    { icon: User, label: t('profile'), path: '/profile', testId: 'nav-profile' },
  ];

  if (user?.role === 'admin') {
    navItems.push({ icon: Settings, label: 'Admin', path: '/admin', testId: 'nav-admin' });
  }

  return (
    <div className="bottom-nav h-16 sm:h-18 flex items-center justify-around px-1 sm:px-4" data-testid="bottom-navigation">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path;
        return (
          <button
            key={item.path}
            data-testid={item.testId}
            onClick={() => navigate(item.path)}
            className={`flex flex-col items-center justify-center gap-0.5 sm:gap-1 px-2 sm:px-4 py-2 rounded-xl transition-all min-w-0 ${
              isActive
                ? 'text-primary'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <Icon size={22} className="sm:w-6 sm:h-6" strokeWidth={isActive ? 2.5 : 2} />
            <span className="text-[10px] sm:text-xs font-medium text-center leading-tight">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
