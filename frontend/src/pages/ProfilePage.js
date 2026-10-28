import React, { useContext, useState, useEffect } from 'react';
import { AuthContext } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import BottomNav from '../components/BottomNav';
import AvatarUploader from '../components/AvatarUploader';
import ProfilePhotos from '../components/ProfilePhotos';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { User, Mail, Globe, LogOut, Edit, Check, Heart } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';

const HELP_CATEGORIES = [
  { value: 'food', label: 'Alimentação', icon: '🍽️' },
  { value: 'legal', label: 'Jurídico', icon: '⚖️' },
  { value: 'health', label: 'Saúde', icon: '🏥' },
  { value: 'housing', label: 'Moradia', icon: '🏠' },
  { value: 'work', label: 'Trabalho', icon: '💼' },
  { value: 'education', label: 'Educação', icon: '📚' },
  { value: 'social', label: 'Social', icon: '🤝' },
  { value: 'clothes', label: 'Roupas', icon: '👕' },
  { value: 'furniture', label: 'Móveis', icon: '🪑' },
  { value: 'transport', label: 'Transporte', icon: '🚗' }
];

export default function ProfilePage() {
  const { user, logout, token, login } = useContext(AuthContext);
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showCategoriesDialog, setShowCategoriesDialog] = useState(false);
  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [useDisplayName, setUseDisplayName] = useState(user?.use_display_name || false);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [savingCategories, setSavingCategories] = useState(false);

  useEffect(() => {
    // Carregar categorias atuais do usuário
    void fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedCategories(data.help_categories || []);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const saveDisplayName = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          display_name: displayName,
          use_display_name: useDisplayName
        })
      });

      if (response.ok) {
        toast.success('Nome fictício atualizado!');
        setShowEditDialog(false);
        window.location.reload();
      }
    } catch (error) {
      toast.error('Erro ao atualizar');
    }
  };

  const toggleCategory = (category) => {
    setSelectedCategories(prev => 
      prev.includes(category) 
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const saveCategories = async () => {
    setSavingCategories(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          help_categories: selectedCategories
        })
      });

      if (response.ok) {
        toast.success('Categorias atualizadas!');
        setShowCategoriesDialog(false);
      } else {
        toast.error('Erro ao salvar categorias');
      }
    } catch (error) {
      toast.error('Erro de conexão');
    } finally {
      setSavingCategories(false);
    }
  };

  const getCategoryInfo = (value) => {
    return HELP_CATEGORIES.find(c => c.value === value) || { icon: '📝', label: value };
  };

  return (
    <div className="min-h-screen bg-background pb-20" data-testid="profile-page">
      <div className="bg-white border-b border-gray-100 sticky top-0 z-10 glassmorphism">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-heading font-bold text-textPrimary">{t('profile')}</h1>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-2xl">
        <div className="bg-white rounded-3xl p-8 shadow-card space-y-6">
          <div className="flex flex-col items-center text-center space-y-4">
            <AvatarUploader />
            <div>
              <div className="flex items-center gap-2 justify-center">
                <h2 className="text-2xl font-heading font-bold text-textPrimary" data-testid="user-name">
                  {user?.use_display_name && user?.display_name ? user.display_name : user?.name}
                </h2>
                <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
                  <DialogTrigger asChild>
                    <button className="p-2 hover:bg-gray-100 rounded-full transition-all">
                      <Edit size={18} className="text-primary" />
                    </button>
                  </DialogTrigger>
                  <DialogContent className="rounded-3xl">
                    <DialogHeader>
                      <DialogTitle>Nome Fictício (Privacidade)</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label>Nome Fictício</Label>
                        <Input
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                          placeholder="Ex: Maria S., João A."
                          className="rounded-xl mt-2"
                        />
                        <p className="text-xs text-textMuted mt-2">
                          Este nome aparecerá nos posts em vez do seu nome real
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={useDisplayName}
                          onChange={(e) => setUseDisplayName(e.target.checked)}
                          className="w-5 h-5 rounded border-gray-300"
                        />
                        <Label>Usar nome fictício nos posts</Label>
                      </div>
                      <Button
                        onClick={saveDisplayName}
                        className="w-full rounded-full py-6 bg-primary hover:bg-primary-hover"
                      >
                        Salvar
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
              {user?.use_display_name && user?.display_name && (
                <p className="text-xs text-textMuted">Nome fictício ativo</p>
              )}
              <p className="text-textMuted capitalize" data-testid="user-role">
                {user?.role === 'migrant' ? t('migrant') : user?.role === 'helper' ? t('helper') : user?.role}
              </p>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-6 space-y-4">
            <div className="flex items-center gap-3 text-textSecondary">
              <Mail size={20} />
              <span data-testid="user-email">{user?.email}</span>
            </div>
            {user?.languages && user.languages.length > 0 && (
              <div className="flex items-center gap-3 text-textSecondary">
                <Globe size={20} />
                <div className="flex gap-2">
                  {user.languages.map(lang => (
                    <span key={lang} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                      {lang.toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Seção de Categorias de Ajuda */}
          <div className="border-t border-gray-100 pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-textPrimary flex items-center gap-2">
                <Heart size={20} className="text-primary" />
                {user?.role === 'migrant' ? 'Categorias em que preciso de ajuda' : 'Categorias que você ajuda'}
              </h3>
              <Dialog open={showCategoriesDialog} onOpenChange={setShowCategoriesDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm" className="rounded-full">
                    <Edit size={16} className="mr-1" />
                    Editar
                  </Button>
                </DialogTrigger>
                <DialogContent className="rounded-3xl max-h-[85vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                      🤝 Categorias de Ajuda
                    </DialogTitle>
                    <p className="text-sm text-textSecondary">
                      Selecione as categorias em que você pode oferecer ajuda
                    </p>
                  </DialogHeader>
                  
                  <div className="grid grid-cols-2 gap-3 my-4">
                    {HELP_CATEGORIES.map(cat => (
                      <button
                        key={cat.value}
                        type="button"
                        onClick={() => toggleCategory(cat.value)}
                        className={`p-3 rounded-xl border-2 transition-all text-left relative ${
                          selectedCategories.includes(cat.value)
                            ? 'bg-primary/10 border-primary shadow-md'
                            : 'bg-white border-gray-200 hover:border-primary/50'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{cat.icon}</span>
                          <span className={`text-sm font-medium ${
                            selectedCategories.includes(cat.value) ? 'text-primary' : 'text-textPrimary'
                          }`}>
                            {cat.label}
                          </span>
                        </div>
                        {selectedCategories.includes(cat.value) && (
                          <div className="absolute top-2 right-2">
                            <Check size={14} className="text-primary" />
                          </div>
                        )}
                      </button>
                    ))}
                  </div>

                  {selectedCategories.length > 0 && (
                    <div className="p-3 bg-green-50 rounded-xl border border-green-200 mb-4">
                      <p className="text-sm text-green-700 flex items-center gap-2">
                        <Check size={16} />
                        {selectedCategories.length} categoria{selectedCategories.length > 1 ? 's' : ''} selecionada{selectedCategories.length > 1 ? 's' : ''}
                      </p>
                    </div>
                  )}

                  <Button
                    onClick={saveCategories}
                    disabled={savingCategories}
                    className="w-full rounded-full py-6 bg-primary hover:bg-primary-hover"
                  >
                    {savingCategories ? 'Salvando...' : 'Salvar Categorias'}
                  </Button>
                </DialogContent>
              </Dialog>
            </div>

            {selectedCategories.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {selectedCategories.map(cat => {
                  const info = getCategoryInfo(cat);
                  return (
                    <span 
                      key={cat}
                      className="px-3 py-2 bg-primary/10 text-primary rounded-full text-sm font-medium flex items-center gap-1"
                    >
                      {info.icon} {info.label}
                    </span>
                  );
                })}
              </div>
            ) : (
              <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-200">
                <p className="text-sm text-yellow-800">
                  Você ainda não selecionou categorias. Clique em "Editar" para escolher.
                </p>
              </div>
            )}
          </div>

          {user?.bio && (
            <div className="border-t border-gray-100 pt-6">
              <h3 className="font-bold text-textPrimary mb-2">Sobre</h3>
              <p className="text-textSecondary leading-relaxed">{user.bio}</p>
            </div>
          )}

          <ProfilePhotos />

          <div className="border-t border-gray-100 pt-6">
            <h3 className="font-bold text-textPrimary mb-3">Idioma do aplicativo</h3>
            <LanguageSwitcher />
          </div>

          <div className="border-t border-gray-100 pt-6">
            <Button
              data-testid="logout-button"
              onClick={handleLogout}
              variant="outline"
              className="w-full rounded-full py-6 text-red-600 border-red-200 hover:bg-red-50"
            >
              <LogOut size={20} className="mr-2" />
              Sair
            </Button>
          </div>
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
