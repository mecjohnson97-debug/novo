import React, { useState, useEffect, useContext, useRef } from 'react';
import { AuthContext } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import BottomNav from '../components/BottomNav';
import { Search, MapPin, Star, Clock, MessageCircle, Plus, Filter, Briefcase, Wrench, Home, Car, Utensils, Heart, GraduationCap, Monitor, Baby, Flower2, Package, MoreHorizontal, ExternalLink, Globe, Target } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import { requestLocationPermission } from '../utils/geolocation';

const REGIONS = [
  { value: 'br', label: 'Brasil', indeed: 'br' },
  { value: 'pt', label: 'Portugal', indeed: 'pt' },
  { value: 'fr', label: 'França', indeed: 'fr' },
  { value: 'be', label: 'Bélgica', indeed: 'be' },
  { value: 'ch', label: 'Suíça', indeed: 'ch' },
  { value: 'es', label: 'Espanha', indeed: 'es' },
  { value: 'it', label: 'Itália', indeed: 'it' },
  { value: 'de', label: 'Alemanha', indeed: 'de' },
  { value: 'gb', label: 'Reino Unido', indeed: 'uk' },
  { value: 'us', label: 'Estados Unidos', indeed: 'www' },
  { value: 'ca', label: 'Canadá', indeed: 'ca' },
  { value: 'latam', label: 'América Latina', indeed: 'mx' },
  { value: 'remote', label: 'Remoto', indeed: 'www' }
];
const regionOf = (v) => REGIONS.find((r) => r.value === v) || REGIONS[0];
const FRENCH_REGIONS = ['fr', 'be', 'ch'];

const SERVICE_CATEGORIES = [
  { value: 'all', label: 'Todos', icon: Briefcase },
  { value: 'construction', label: 'Construção', icon: Wrench },
  { value: 'cleaning', label: 'Limpeza', icon: Home },
  { value: 'driver', label: 'Motorista', icon: Car },
  { value: 'restaurant', label: 'Restaurante', icon: Utensils },
  { value: 'care', label: 'Cuidados', icon: Heart },
  { value: 'education', label: 'Educação', icon: GraduationCap },
  { value: 'tech', label: 'Tecnologia', icon: Monitor },
  { value: 'childcare', label: 'Babá', icon: Baby },
  { value: 'gardening', label: 'Jardinagem', icon: Flower2 },
  { value: 'logistics', label: 'Logística', icon: Package },
  { value: 'other', label: 'Outros', icon: MoreHorizontal }
];

const SEARCH_SUGGESTIONS = {
  construction: ['pedreiro', 'eletricista', 'pintor', 'encanador'],
  cleaning: ['limpeza', 'faxineira', 'camareira', 'diarista'],
  driver: ['motorista', 'entregador', 'motoboy', 'chofer'],
  restaurant: ['garçom', 'cozinheiro', 'auxiliar de cozinha', 'barista'],
  care: ['cuidador de idosos', 'enfermagem', 'acompanhante'],
  education: ['professor', 'monitor', 'tutor'],
  tech: ['desenvolvedor', 'suporte técnico', 'analista'],
  childcare: ['babá', 'cuidadora infantil', 'au pair'],
  gardening: ['jardineiro', 'paisagista'],
  logistics: ['estoquista', 'operador de armazém', 'auxiliar logístico'],
  other: ['emprego', 'vaga']
};

const REGION_PLATFORMS = {
  br: [
    { id: 'catho', name: 'Catho', url: (q) => `https://www.catho.com.br/vagas/${encodeURIComponent(q)}/` },
    { id: 'infojobs_br', name: 'InfoJobs Brasil', url: (q) => `https://www.infojobs.com.br/empregos.aspx?palabra=${encodeURIComponent(q)}` },
    { id: 'vagas', name: 'Vagas.com', url: (q) => `https://www.vagas.com.br/vagas-de-${encodeURIComponent(q)}` },
    { id: 'gupy', name: 'Gupy', url: (q) => `https://portal.gupy.io/job-search/term=${encodeURIComponent(q)}` }
  ],
  pt: [
    { id: 'netempregos', name: 'Net-Empregos', url: (q) => `https://www.net-empregos.com/pesquisa-empregos.asp?chaves=${encodeURIComponent(q)}` },
    { id: 'iefp', name: 'IEFP (Portugal)', url: () => 'https://iefponline.iefp.pt/IEFP/pesquisas/search.do' }
  ],
  es: [{ id: 'infojobs_es', name: 'InfoJobs España', url: (q) => `https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=${encodeURIComponent(q)}` }],
  it: [{ id: 'infojobs_it', name: 'InfoJobs Italia', url: (q) => `https://www.infojobs.it/offerte-lavoro/?keyword=${encodeURIComponent(q)}` }],
  de: [{ id: 'stepstone', name: 'StepStone', url: (q) => `https://www.stepstone.de/jobs/${encodeURIComponent(q)}` }],
  gb: [{ id: 'reed', name: 'Reed', url: (q) => `https://www.reed.co.uk/jobs/${encodeURIComponent(q)}-jobs` }],
  us: [{ id: 'glassdoor', name: 'Glassdoor', url: (q) => `https://www.glassdoor.com/Job/jobs.htm?sc.keyword=${encodeURIComponent(q)}` }],
  ca: [{ id: 'jobbank', name: 'Job Bank Canada', url: (q) => `https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=${encodeURIComponent(q)}` }],
  latam: [{ id: 'computrabajo', name: 'Computrabajo', url: (q) => `https://www.computrabajo.com/empleos?q=${encodeURIComponent(q)}` }],
  remote: [
    { id: 'remotive', name: 'Remotive', url: (q) => `https://remotive.com/remote-jobs?search=${encodeURIComponent(q)}` },
    { id: 'weworkremotely', name: 'We Work Remotely', url: (q) => `https://weworkremotely.com/remote-jobs/search?term=${encodeURIComponent(q)}` }
  ]
};

const FRENCH_PLATFORMS = [
  { id: 'pole_emploi', name: 'France Travail', baseUrl: 'https://candidat.francetravail.fr/offres/recherche' },
  { id: 'hellowork', name: 'HelloWork', baseUrl: 'https://www.hellowork.com/fr-fr/emploi/recherche.html' },
  { id: 'welcometothejungle', name: 'Welcome to the Jungle', baseUrl: 'https://www.welcometothejungle.com/fr/jobs' },
  { id: 'monster', name: 'Monster', baseUrl: 'https://www.monster.fr/emploi/recherche' },
  { id: 'apec', name: 'APEC', baseUrl: 'https://www.apec.fr/candidat/recherche-emploi.html/emploi' },
  { id: 'leboncoin', name: 'Leboncoin', baseUrl: 'https://www.leboncoin.fr/offres_d_emploi' }
];

export default function JobsPage() {
  const { token, user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [region, setRegion] = useState('br');
  const [locationLoading, setLocationLoading] = useState(false);
  const [jobOffers, setJobOffers] = useState([]);
  const [jobSeekers, setJobSeekers] = useState([]);
  const [externalJobs, setExternalJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showCreateOffer, setShowCreateOffer] = useState(false);
  const [viewMode, setViewMode] = useState('search');
  const [showAllPlatforms, setShowAllPlatforms] = useState(false);
  const [totalJobs, setTotalJobs] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobDetails, setShowJobDetails] = useState(false);

  const jobSearchTranslations = {
    'garçom': 'serveur', 'garcom': 'serveur', 'garçon': 'serveur',
    'garconete': 'serveuse', 'garçonete': 'serveuse',
    'cozinheiro': 'cuisinier', 'cozinha': 'cuisine', 'chef': 'chef cuisinier',
    'limpeza': 'nettoyage', 'faxineiro': 'agent de nettoyage', 'faxineira': 'agent de nettoyage',
    'construção': 'construction', 'pedreiro': 'maçon', 'pintor': 'peintre',
    'eletricista': 'électricien', 'encanador': 'plombier',
    'motorista': 'chauffeur', 'entregador': 'livreur', 'entrega': 'livraison',
    'babá': 'nounou', 'baba': 'nounou', 'cuidador': 'aide-soignant', 'cuidadora': 'aide-soignante',
    'jardineiro': 'jardinier', 'jardinagem': 'jardinage',
    'segurança': 'agent de sécurité', 'porteiro': 'gardien',
    'recepcionista': 'réceptionniste', 'vendedor': 'vendeur', 'vendedora': 'vendeuse',
    'caixa': 'caissier', 'atendente': 'employé', 'auxiliar': 'assistant', 'ajudante': 'aide',
    'operador': 'opérateur', 'montador': 'monteur', 'mecânico': 'mécanicien', 'mecanico': 'mécanicien',
    'padeiro': 'boulanger', 'açougueiro': 'boucher', 'acougueiro': 'boucher',
    'carpinteiro': 'charpentier', 'soldador': 'soudeur',
    'técnico': 'technicien', 'tecnico': 'technicien',
    'enfermeiro': 'infirmier', 'enfermeira': 'infirmière',
    'professor': 'professeur', 'professora': 'professeur',
    'secretário': 'secrétaire', 'secretaria': 'secrétaire',
    'contador': 'comptable', 'advogado': 'avocat',
    'programador': 'développeur', 'desenvolvedor': 'développeur',
    'designer': 'designer', 'marketing': 'marketing', 'vendas': 'vente',
    'administrativo': 'administratif', 'logística': 'logistique', 'logistica': 'logistique',
    'armazém': 'entrepôt', 'armazem': 'entrepôt', 'estoque': 'stock',
    'empilhadeira': 'cariste', 'carregador': 'manutentionnaire',
    'mudança': 'déménagement', 'mudanca': 'déménagement',
    'hotel': 'hôtel', 'restaurante': 'restaurant', 'bar': 'bar', 'café': 'café',
    'padaria': 'boulangerie', 'supermercado': 'supermarché', 'loja': 'magasin',
    'escritório': 'bureau', 'escritorio': 'bureau', 'fábrica': 'usine', 'fabrica': 'usine',
    'obra': 'chantier', 'hospital': 'hôpital', 'clínica': 'clinique', 'clinica': 'clinique',
    'escola': 'école', 'creche': 'crèche'
  };

  const translateSearchTerm = (term) => {
    const lowerTerm = term.toLowerCase().trim();
    if (jobSearchTranslations[lowerTerm]) return jobSearchTranslations[lowerTerm];
    for (const [pt, fr] of Object.entries(jobSearchTranslations)) {
      if (lowerTerm.includes(pt)) return lowerTerm.replace(pt, fr);
    }
    return term;
  };

  const normalizeLocationValue = (value) => (value || '').trim();

  const useMyLocation = async () => {
    setLocationLoading(true);
    try {
      const location = await requestLocationPermission({
        showToast: true,
        fallbackLocation: null,
        onStart: () => setLocationLoading(true),
        onError: () => setLocationLoading(false),
        onSuccess: () => setLocationLoading(false)
      });

      if (!location) {
        setLocationLoading(false);
        return;
      }

      const resolvedLocation = location.address
        ? location.address.split(',').slice(0, 2).join(', ')
        : 'Minha localização';

      const nextValue = normalizeLocationValue(resolvedLocation);
      setLocationQuery(nextValue);
      toast.success(`Busca configurada para: ${nextValue}`);

      if (searchQuery.trim()) {
        void searchExternalJobs(searchQuery, nextValue, 1);
      }
    } catch (err) {
      console.error('Error getting user location:', err);
      setLocationLoading(false);
    }
  };

  const handleRegion = (value) => {
    setRegion(value);
    setLocationQuery('');
    void searchExternalJobs(searchQuery.trim() || 'emprego', '', 1, false, value);
  };

  useEffect(() => {
    void fetchJobs();
    void searchExternalJobs('emprego', '');
  }, []);

  useEffect(() => {
    if (selectedCategory !== 'all') {
      const categoryQuery = SEARCH_SUGGESTIONS[selectedCategory]?.[0] || selectedCategory;
      void searchExternalJobs(categoryQuery, normalizeLocationValue(locationQuery));
    }
  }, [selectedCategory]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/posts?category=work&limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = (await response.json()).posts || [];
        const workPosts = data.filter(p => p.category === 'work');
        const offers = workPosts.filter(p => p.type === 'offer');
        const seekers = workPosts.filter(p => p.type === 'need');
        setJobOffers(offers);
        setJobSeekers(seekers);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const resultsRef = useRef(null);

  const searchExternalJobs = async (query, location, page = 1, scroll = false, reg = region) => {
    setSearchLoading(true);
    try {
      const rawQuery = query || 'emprego';
      const translatedQuery = FRENCH_REGIONS.includes(reg) ? translateSearchTerm(rawQuery) : rawQuery;
      const normalizedLocation = normalizeLocationValue(location);
      const params = new URLSearchParams({
        query: translatedQuery,
        location: normalizedLocation,
        region: reg,
        page: page.toString(),
        date_posted: 'all'
      });

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/jobs/search?${params}`
      );
      if (response.ok) {
        const data = await response.json();
        setExternalJobs(data.jobs || []);
        setTotalJobs(data.total || 0);
        setCurrentPage(page);
        setViewMode('search');
        if (data.jobs?.length > 0) {
          if (scroll) setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
          toast.success(`${data.jobs.length} vagas encontradas!`);
        } else {
          toast.info('Nenhuma vaga encontrada. Tente outros termos.');
        }
      } else {
        const error = await response.json().catch(() => ({}));
        toast.error(error.detail || 'Erro ao buscar vagas. Tente novamente.');
      }
    } catch (error) {
      console.error('Error searching external jobs:', error);
      toast.error('Erro de conexão ao buscar vagas');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearch = () => {
    const sanitizedQuery = searchQuery.trim();
    const sanitizedLocation = normalizeLocationValue(locationQuery);
    if (!sanitizedQuery) {
      toast.error('Digite algo para buscar');
      return;
    }
    void searchExternalJobs(sanitizedQuery, sanitizedLocation, 1, true);
    setViewMode('search');
  };

  const getTimeAgo = (dateString) => {
    if (!dateString) return 'Recente';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins} min atrás`;
    if (diffHours < 24) return `${diffHours}h atrás`;
    return `${diffDays} dias atrás`;
  };

  const regionInfo = regionOf(region);
  const JOB_PLATFORMS = [
    { id: 'indeed', name: `Indeed ${regionInfo.label}`, baseUrl: `https://${regionInfo.indeed}.indeed.com/jobs` },
    { id: 'linkedin', name: 'LinkedIn', baseUrl: 'https://www.linkedin.com/jobs/search' },
    ...(REGION_PLATFORMS[region] || []),
    ...(FRENCH_REGIONS.includes(region) ? FRENCH_PLATFORMS : [])
  ];

  const generateSearchUrl = (platform, query, location) => {
    const searchTerm = query || (selectedCategory !== 'all' ? SEARCH_SUGGESTIONS[selectedCategory]?.[0] : 'emprego');
    const loc = normalizeLocationValue(location) || (region === 'remote' ? 'Remote' : regionInfo.label);
    if (platform.url) return platform.url(searchTerm, loc);

    switch(platform.id) {
      case 'indeed':
        return `${platform.baseUrl}?q=${encodeURIComponent(searchTerm)}&l=${encodeURIComponent(region === 'remote' ? 'Remote' : normalizeLocationValue(location))}`;
      case 'pole_emploi':
        return `${platform.baseUrl}?motsCles=${encodeURIComponent(searchTerm)}&offresPartenaires=true`;
      case 'linkedin':
        return `${platform.baseUrl}?keywords=${encodeURIComponent(searchTerm)}&location=${encodeURIComponent(loc)}&f_TPR=r86400`;
      case 'leboncoin':
        return `https://www.leboncoin.fr/offres_d_emploi/offres?text=${encodeURIComponent(searchTerm)}`;
      case 'monster':
        return `${platform.baseUrl}?q=${encodeURIComponent(searchTerm)}&where=${encodeURIComponent(loc)}`;
      case 'hellowork':
        return `${platform.baseUrl}?k=${encodeURIComponent(searchTerm)}&l=${encodeURIComponent(loc)}`;
      case 'apec':
        return `${platform.baseUrl}?motsCles=${encodeURIComponent(searchTerm)}`;
      case 'welcometothejungle':
        return `${platform.baseUrl}?query=${encodeURIComponent(searchTerm)}&aroundQuery=${encodeURIComponent(loc)}`;
      default:
        return platform.baseUrl;
    }
  };

  const searchAllPlatforms = () => {
    const sanitizedQuery = searchQuery.trim();
    if (!sanitizedQuery) {
      toast.error('Digite algo para buscar');
      return;
    }
    const mainPlatforms = JOB_PLATFORMS.slice(0, 3);
    mainPlatforms.forEach((platform, index) => {
      setTimeout(() => {
        window.open(generateSearchUrl(platform, sanitizedQuery, locationQuery), '_blank');
      }, index * 500);
    });
    toast.success(`Buscando "${sanitizedQuery}" em ${mainPlatforms.length} plataformas!`);
  };

  const searchOnPlatform = (platform) => {
    const url = generateSearchUrl(platform, searchQuery, locationQuery);
    window.open(url, '_blank');
    toast.success(`Abrindo ${platform.name}...`);
  };

  const openJobDetails = (job) => {
    if (!job) return;
    setSelectedJob(job);
    setShowJobDetails(true);
  };

  const displayData = viewMode === 'offers' ? jobOffers : jobSeekers;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FDFBF7] to-white pb-20" data-testid="jobs-page">
      <div className="bg-white border-b shadow-sm">
        <div className="container mx-auto max-w-4xl px-4 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-bold text-[#2C221E]">Buscar Emprego</h1>
            <Button
              onClick={() => navigate('/home')}
              variant="outline"
              size="sm"
              className="rounded-full"
            >
              <Plus size={16} className="mr-1" />
              Publicar
            </Button>
          </div>

          <div className="bg-gradient-to-r from-[#2A9D8F] to-[#1F7A6F] rounded-2xl p-4 mb-4">
            <p className="text-white text-sm mb-3 font-medium">Escolha o país/região e busque vagas</p>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A89E95]" size={18} />
                <Input
                  placeholder="Ex: garçom, eletricista, cozinheiro..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="pl-10 rounded-xl bg-white h-12"
                  data-testid="jobs-search-input"
                />
              </div>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A89E95]" size={18} />
                <Input
                  placeholder="Cidade (opcional)"
                  value={locationQuery}
                  onChange={(e) => setLocationQuery(e.target.value)}
                  className="pl-10 rounded-xl bg-white h-12 w-full sm:w-44"
                  data-testid="jobs-location-input"
                />
              </div>
              <Button 
                onClick={handleSearch}
                data-testid="jobs-search-button"
                disabled={searchLoading}
                className="h-12 px-6 rounded-xl bg-[#C8894F] hover:bg-[#B67A43] text-white font-bold"
              >
                {searchLoading ? (
                  <>Buscando...</>
                ) : (
                  <><Search size={18} className="mr-2" /> Buscar Vagas</>
                )}
              </Button>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                type="button"
                onClick={useMyLocation}
                disabled={locationLoading}
                variant="secondary"
                className="h-8 px-3 rounded-full bg-white/15 text-white border border-white/20 hover:bg-white/25 text-xs"
              >
                <Target size={12} className="mr-1" />
                {locationLoading ? 'Buscando região...' : 'Usar meu GPS'}
              </Button>
              {REGIONS.map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => handleRegion(preset.value)}
                  data-testid={`jobs-region-${preset.value}`}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                    region === preset.value
                      ? 'bg-white text-[#1F7A6F] ring-2 ring-white/80'
                      : 'bg-white/15 text-white hover:bg-white/25'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {selectedCategory !== 'all' && SEARCH_SUGGESTIONS[selectedCategory] && (
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="text-white/70 text-xs">Sugestões:</span>
                {SEARCH_SUGGESTIONS[selectedCategory].map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => setSearchQuery(suggestion)}
                    className="px-2 py-1 bg-white/20 rounded-full text-xs text-white hover:bg-white/30"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2 mb-4 overflow-x-auto">
            <button
              onClick={() => setViewMode('search')} data-testid="jobs-tab-search"
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                viewMode === 'search'
                  ? 'bg-[#2A9D8F] text-white'
                  : 'bg-[#F1EBE1] text-[#5C524B] hover:bg-[#E8E2D9]'
              }`}
            >
              Vagas ({externalJobs.length})
            </button>
            <button
              onClick={() => setViewMode('platforms')} data-testid="jobs-tab-platforms"
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                viewMode === 'platforms'
                  ? 'bg-[#2A9D8F] text-white'
                  : 'bg-[#F1EBE1] text-[#5C524B] hover:bg-[#E8E2D9]'
              }`}
            >
              Plataformas
            </button>
            <button
              onClick={() => setViewMode('offers')} data-testid="jobs-tab-offers"
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                viewMode === 'offers'
                  ? 'bg-primary text-white'
                  : 'bg-[#F1EBE1] text-[#5C524B] hover:bg-[#E8E2D9]'
              }`}
            >
              Serviços ({jobOffers.length})
            </button>
            <button
              onClick={() => setViewMode('seekers')} data-testid="jobs-tab-seekers"
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                viewMode === 'seekers'
                  ? 'bg-green-600 text-white'
                  : 'bg-[#F1EBE1] text-[#5C524B] hover:bg-[#E8E2D9]'
              }`}
            >
              Procuram ({jobSeekers.length})
            </button>
          </div>

          <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
            {SERVICE_CATEGORIES.map(cat => {
              const IconComponent = cat.icon;
              return (
                <button
                  key={cat.value}
                  onClick={() => setSelectedCategory(cat.value)}
                  className={`flex flex-col items-center gap-1 min-w-[60px] p-2 rounded-xl transition-all ${
                    selectedCategory === cat.value
                      ? 'bg-primary text-white'
                      : 'bg-white text-[#5C524B] hover:bg-[#F1EBE1]'
                  }`}
                >
                  <IconComponent size={20} />
                  <span className="text-xs font-medium whitespace-nowrap">{cat.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="container mx-auto max-w-4xl px-4 py-4">
        {viewMode === 'search' && (
          <div className="space-y-4 scroll-mt-2" ref={resultsRef} data-testid="jobs-results-section">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-[#2C221E]">
                {totalJobs > 0 ? `${totalJobs} vagas encontradas` : 'Resultados da busca'}
              </h2>
              {externalJobs.length > 0 && (
                <span className="text-sm text-[#8C827A]" data-testid="jobs-region-label">
                  {regionInfo.label} · Página {currentPage}
                </span>
              )}
            </div>

            {searchLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#2A9D8F] mx-auto mb-4"></div>
                <p className="text-[#5C524B]">Buscando vagas em {locationQuery || regionInfo.label}...</p>
              </div>
            ) : externalJobs.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-2xl">
                <h3 className="font-bold text-[#2C221E] mb-2">Busque por vagas</h3>
                <p className="text-[#8C827A] mb-4">
                  Digite um cargo ou área de interesse para encontrar vagas disponíveis
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {['Garçom', 'Faxineira', 'Motorista', 'Cozinheiro', 'Eletricista'].map(term => (
                    <button
                      key={term}
                      onClick={() => {
                        setSearchQuery(term);
                        void searchExternalJobs(term, locationQuery, 1, true);
                      }}
                      className="px-3 py-1 bg-[#E9F5F3] text-[#1F7A6F] rounded-full text-sm hover:bg-[#BFE3DD]"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  {externalJobs.map((job) => (
                    <div role="button" tabIndex={0} data-testid={`job-card-${job.id}`} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.currentTarget.click(); } }}
                      key={job.id}
                      className="bg-white rounded-2xl p-4 shadow-sm border border-[#ECE5DA] hover:shadow-md transition-all cursor-pointer"
                      onClick={() => openJobDetails(job)}
                    >
                      <div className="flex gap-4">
                        <div className="flex-shrink-0">
                          {job.company_logo ? (
                            <img 
                              src={job.company_logo} 
                              alt={job.company}
                              className="w-14 h-14 rounded-xl object-cover border"
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                          ) : (
                            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#2A9D8F] to-[#1F7A6F] flex items-center justify-center text-white text-xl font-bold">
                              {job.company?.charAt(0) || '?'}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="font-bold text-[#2C221E] line-clamp-1">{job.title}</h3>
                            {job.is_remote && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs whitespace-nowrap">
                                Remoto
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-[#5C524B] mt-1">{job.company}</p>
                          <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-[#8C827A]">
                            <span className="flex items-center gap-1">
                              <MapPin size={12} />
                              {job.location || regionInfo.label}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock size={12} />
                              {getTimeAgo(job.date_posted)}
                            </span>
                            {job.employment_type && (
                              <span className="px-2 py-0.5 bg-[#F1EBE1] rounded-full">
                                {job.employment_type}
                              </span>
                            )}
                            {job.source && (
                              <span className="px-2 py-0.5 bg-[#F7F4EE] text-[#1F7A6F] rounded-full">
                                via {job.source}
                              </span>
                            )}
                          </div>
                          {(job.salary_min || job.salary_max) && (
                            <div className="mt-2 text-sm font-medium text-green-600">
                              {job.salary_min && `${job.salary_min.toLocaleString()}`}
                              {job.salary_min && job.salary_max && ' - '}
                              {job.salary_max && `${job.salary_max.toLocaleString()}`}
                              {job.salary_currency && ` ${job.salary_currency}`}
                            </div>
                          )}
                          {job.description && (
                            <p className="mt-2 text-sm text-[#5C524B] line-clamp-2">
                              {job.description.replace(/<[^>]*>/g, '').substring(0, 150)}...
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <Button
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(job.url, '_blank');
                          }}
                          className="flex-1 rounded-xl bg-[#2A9D8F] hover:bg-[#238578]"
                          size="sm"
                        >
                          <ExternalLink size={14} className="mr-1" />
                          Candidatar-se
                        </Button>
                        <Button
                          onClick={(e) => {
                            e.stopPropagation();
                            openJobDetails(job);
                          }}
                          variant="outline"
                          className="rounded-xl"
                          size="sm"
                        >
                          Ver mais
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {viewMode === 'platforms' && (
          <div className="space-y-4" data-testid="jobs-platforms-view">
            <Button onClick={searchAllPlatforms} className="w-full rounded-xl bg-[#2A9D8F] hover:bg-[#238578]" data-testid="jobs-search-all-platforms-btn">
              <Globe size={16} className="mr-2" />
              Buscar em todas as plataformas
            </Button>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {JOB_PLATFORMS.map(platform => (
                <button
                  key={platform.id}
                  onClick={() => searchOnPlatform(platform)}
                  className="flex items-center justify-between bg-white border rounded-2xl p-4 hover:border-[#2A9D8F] hover:shadow-md transition-all text-left"
                  data-testid={`jobs-platform-${platform.id}`}
                >
                  <span className="font-semibold text-[#2C221E]">{platform.name}</span>
                  <ExternalLink size={16} className="text-[#2A9D8F]" />
                </button>
              ))}
            </div>
          </div>
        )}

        {(viewMode === 'offers' || viewMode === 'seekers') && (
          <div className="space-y-3" data-testid={`jobs-${viewMode}-view`}>
            {loading ? (
              <p className="text-center text-[#8C827A] py-8">Carregando...</p>
            ) : displayData.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-2xl border" data-testid="jobs-empty-state">
                <Briefcase size={40} className="mx-auto text-[#8C827A] mb-3" />
                <p className="text-[#5C524B]">
                  {viewMode === 'offers' ? 'Nenhuma oferta de serviço publicada ainda.' : 'Ninguém procurando trabalho no momento.'}
                </p>
              </div>
            ) : (
              displayData.map(post => (
                <div key={post.id} className="bg-white rounded-2xl border p-4 shadow-sm" data-testid={`jobs-post-${post.id}`}>
                  <h3 className="font-bold text-[#2C221E]">{post.title}</h3>
                  <p className="text-sm text-[#5C524B] mt-1 line-clamp-3">{post.description}</p>
                  <div className="flex items-center justify-between mt-3 text-xs text-[#8C827A]">
                    <span className="flex items-center gap-1"><Clock size={12} />{getTimeAgo(post.created_at)}</span>
                    {post.user_id && post.user_id !== user?.id && (
                      <Button size="sm" variant="outline" className="rounded-xl" onClick={() => navigate(`/direct-chat/${post.user_id}`)} data-testid={`jobs-contact-${post.id}`}>
                        <MessageCircle size={14} className="mr-1" />
                        Conversar
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      <Dialog open={showJobDetails} onOpenChange={(open) => {
        setShowJobDetails(open);
        if (!open) setSelectedJob(null);
      }}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold flex items-center gap-2">
              {selectedJob?.title}
            </DialogTitle>
          </DialogHeader>

          {selectedJob && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-[#F7F4EE] rounded-xl">
                {selectedJob.company_logo ? (
                  <img 
                    src={selectedJob.company_logo} 
                    alt={selectedJob.company}
                    className="w-16 h-16 rounded-xl object-cover"
                  />
                ) : (
                  <div className="w-16 h-16 rounded-xl bg-[#2A9D8F] flex items-center justify-center text-white text-2xl font-bold">
                    {selectedJob.company?.charAt(0)}
                  </div>
                )}
                <div>
                  <h3 className="font-bold text-lg">{selectedJob.company}</h3>
                  <p className="text-[#5C524B] flex items-center gap-1">
                    <MapPin size={14} />
                    {selectedJob.location || regionInfo.label}
                  </p>
                </div>
              </div>

              {selectedJob.employment_type && (
                <div className="p-3 bg-[#F7F4EE] rounded-xl">
                  <p className="text-xs text-[#8C827A]">Tipo</p>
                  <p className="font-medium">{selectedJob.employment_type}</p>
                </div>
              )}

              {(selectedJob.salary_min || selectedJob.salary_max) && (
                <div className="p-3 bg-yellow-50 rounded-xl">
                  <p className="text-xs text-[#8C827A]">Salário</p>
                  <p className="font-medium text-green-600">
                    {selectedJob.salary_min?.toLocaleString()} - {selectedJob.salary_max?.toLocaleString()} {selectedJob.salary_currency}
                  </p>
                </div>
              )}

              {selectedJob.description && (
                <div>
                  <h4 className="font-bold mb-2">Descrição da Vaga</h4>
                  <div className="text-sm text-[#5C524B] whitespace-pre-line">
                    {selectedJob.description.replace(/<[^>]*>/g, '').substring(0, 2000)}
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-4 border-t">
                <Button
                  onClick={() => window.open(selectedJob.url, '_blank')}
                  className="flex-1 rounded-xl bg-[#2A9D8F] hover:bg-[#238578]"
                >
                  <ExternalLink size={16} className="mr-2" />
                  Candidatar-se Agora
                </Button>
                <Button
                  onClick={() => setShowJobDetails(false)}
                  variant="outline"
                  className="rounded-xl"
                >
                  Fechar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <BottomNav />
    </div>
  );
}
