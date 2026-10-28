import React, { useState, useEffect, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import './i18n';
import './App.css';

// Páginas críticas - carregadas imediatamente
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import AutoTranslate from './components/AutoTranslate';

// Páginas com lazy loading - carregadas sob demanda
const HomePage = React.lazy(() => import('./pages/HomePage'));
const AIChat = React.lazy(() => import('./pages/AIChat'));
const ServicesPage = React.lazy(() => import('./pages/ServicesPage'));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage'));
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'));
const DirectChatPage = React.lazy(() => import('./pages/DirectChatPage'));
const VolunteersPage = React.lazy(() => import('./pages/VolunteersPage'));
const VolunteerRegisterPage = React.lazy(() => import('./pages/VolunteerRegisterPage'));
const NearbyHelpersPage = React.lazy(() => import('./pages/NearbyHelpersPage'));
const MapPage = React.lazy(() => import('./pages/MapPage'));
const JobsPage = React.lazy(() => import('./pages/JobsPage'));
const HousingPage = React.lazy(() => import('./pages/HousingPage'));

// Componente de loading para Suspense
const LoadingComponent = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-gray-600">Carregando...</p>
    </div>
  </div>
);

export const AuthContext = React.createContext();

function App() {
  // Usuário em cache: a tela abre na hora enquanto o perfil é validado (evita espera no cold start do Render)
  const cachedUser = (() => { try { return JSON.parse(localStorage.getItem('user')); } catch { return null; } })();
  const [user, setUser] = useState(localStorage.getItem('token') ? cachedUser : null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(!!localStorage.getItem('token') && !cachedUser);
  const { i18n } = useTranslation();

  useEffect(() => {
    if (token) {
      void fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
      } else if (response.status === 401 || response.status === 403) {
        logout();
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = (newToken, userData) => {
    localStorage.setItem('token', newToken);
    if (userData) localStorage.setItem('user', JSON.stringify(userData));
    setToken(newToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  if (loading) {
    return <LoadingComponent />;
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <AutoTranslate />
      <BrowserRouter>
        <Suspense fallback={<LoadingComponent />}>
          <Routes>
            <Route path="/" element={!user ? <LandingPage /> : <Navigate to="/home" />} />
            <Route path="/auth" element={!user ? <AuthPage /> : <Navigate to="/home" />} />
            <Route path="/home" element={user ? <HomePage /> : <Navigate to="/" />} />
            <Route path="/chat" element={user ? <AIChat /> : <Navigate to="/" />} />
            <Route path="/services" element={user ? <ServicesPage /> : <Navigate to="/" />} />
            <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/" />} />
            <Route path="/admin" element={user && user.role === 'admin' ? <AdminDashboard /> : (user ? <Navigate to="/home" /> : <Navigate to="/" />)} />
            <Route path="/direct-chat/:userId" element={user ? <DirectChatPage /> : <Navigate to="/" />} />
            <Route path="/volunteers" element={user ? <VolunteersPage /> : <Navigate to="/" />} />
            <Route path="/jobs" element={user ? <JobsPage /> : <Navigate to="/" />} />
            <Route path="/housing" element={user ? <HousingPage /> : <Navigate to="/" />} />
            <Route path="/nearby" element={user ? <NearbyHelpersPage /> : <Navigate to="/" />} />
            <Route path="/map" element={user ? <MapPage /> : <Navigate to="/" />} />
            <Route path="/volunteer-register" element={<VolunteerRegisterPage />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}

export default App;
