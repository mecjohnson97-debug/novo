import React, { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Inbox, RefreshCw } from 'lucide-react';
import { AuthContext } from '../App';
import BottomNav from '../components/BottomNav';
import WelcomeStrip from '../components/feed/WelcomeStrip';
import FeedFilters from '../components/feed/FeedFilters';
import PostCard from '../components/feed/PostCard';
import PostSkeleton from '../components/feed/PostSkeleton';
import FeedSidebar from '../components/feed/FeedSidebar';
import CreatePostDialog from '../components/feed/CreatePostDialog';
import { API, authHeaders } from '../components/feed/feedConfig';

const PAGE = 10;

export default function HomePage() {
  const { user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState(false);
  const [category, setCategory] = useState('all');
  const [type, setType] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const reqId = useRef(0);

  const fetchPage = useCallback(async (skip) => {
    const params = new URLSearchParams({ limit: PAGE, skip });
    if (category !== 'all') params.set('category', category);
    if (type !== 'all') params.set('type', type);
    const res = await fetch(`${API}/api/posts?${params}`, { headers: authHeaders(token) });
    if (!res.ok) throw new Error(res.status);
    return res.json();
  }, [category, type, token]);

  const loadFirst = useCallback(async () => {
    const id = ++reqId.current;
    setLoading(true);
    setError(false);
    try {
      const data = await fetchPage(0);
      if (id !== reqId.current) return;
      setPosts(data.posts);
      setHasMore(data.has_more);
    } catch {
      if (id === reqId.current) setError(true);
    } finally {
      if (id === reqId.current) setLoading(false);
    }
  }, [fetchPage]);

  useEffect(() => { loadFirst(); }, [loadFirst]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const data = await fetchPage(posts.length);
      setPosts((p) => [...p, ...data.posts.filter((n) => !p.some((o) => o.id === n.id))]);
      setHasMore(data.has_more);
    } catch {
      setError(true);
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="feed-root min-h-screen pb-24" data-testid="home-page">
      <div className="mx-auto flex max-w-6xl gap-8 px-3 pt-4 sm:px-6 sm:pt-6">
        <FeedSidebar />

        <main className="min-w-0 max-w-2xl flex-1 space-y-4">
          <WelcomeStrip userName={user?.name} onNeedHelp={() => setShowCreate(true)} onWantHelp={() => navigate('/volunteers')} />

          <div className="feed-sticky">
            <FeedFilters category={category} type={type} onCategory={setCategory} onType={setType} />
          </div>

          <div className="flex items-baseline justify-between px-1">
            <h2 className="font-heading text-lg font-semibold text-[#2C221E]">Publicações recentes</h2>
            <button onClick={loadFirst} className="feed-ghost text-xs" data-testid="refresh-feed-btn"><RefreshCw size={14} /> Atualizar</button>
          </div>

          {loading ? (
            <PostSkeleton />
          ) : error && posts.length === 0 ? (
            <div className="feed-card p-8 text-center" data-testid="feed-error">
              <p className="text-sm text-[#5C524B]">Não foi possível carregar as publicações. O servidor pode estar acordando.</p>
              <button onClick={loadFirst} className="feed-cta feed-cta-sage mx-auto mt-4 px-6" data-testid="feed-retry-btn">Tentar novamente</button>
            </div>
          ) : posts.length === 0 ? (
            <div className="feed-card p-10 text-center" data-testid="feed-empty">
              <Inbox className="mx-auto text-[#D4A373]" size={36} />
              <p className="mt-3 font-heading text-lg text-[#2C221E]">Nenhuma publicação por aqui</p>
              <p className="text-sm text-[#8C827A]">Seja o primeiro a compartilhar.</p>
            </div>
          ) : (
            <div className="space-y-4" data-testid="feed-list">
              {posts.map((post, i) => (
                <PostCard key={post.id} post={post} index={i} token={token} currentUserId={user?.id} onChat={(uid) => navigate(`/direct-chat/${uid}`)} />
              ))}
              {hasMore && (
                <button onClick={loadMore} disabled={loadingMore} className="feed-cta feed-cta-outline w-full" data-testid="load-more-posts-btn">
                  {loadingMore ? <><Loader2 size={16} className="animate-spin" /> Carregando…</> : 'Carregar mais'}
                </button>
              )}
            </div>
          )}
        </main>
      </div>

      <CreatePostDialog open={showCreate} onOpenChange={setShowCreate} user={user} token={token} onCreated={loadFirst} />
      <BottomNav />
    </div>
  );
}
