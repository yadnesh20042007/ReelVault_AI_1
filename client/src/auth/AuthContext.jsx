import { useEffect, useMemo, useState } from 'react';
import { api, clearSession, getSession, setSession, isMockSession } from '../services/api';
import { AuthContext } from './context';

export function AuthProvider({ children }) {
  const [session, setSessionState] = useState(getSession);
  const [loading, setLoading] = useState(() => {
    const s = getSession();
    return Boolean(s?.access_token && !s?.is_mock && s?.access_token !== 'mock_static_admin_token');
  });
  const accessToken = session?.access_token;
  const isMock = isMockSession(session);

  useEffect(() => {
    let active = true;
    if (!accessToken || session?.is_mock || accessToken === 'mock_static_admin_token') {
      return () => { active = false; };
    }

    api.me()
      .then((user) => active && setSessionState((current) => ({ ...current, user })))
      .catch(() => {
        clearSession();
        if (active) setSessionState(null);
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [accessToken, session?.is_mock]);

  const value = useMemo(() => ({
    session,
    user: session?.user || null,
    isMock,
    loading,
    async signIn(email, password) {
      const next = await api.signIn(email, password);
      setSession(next);
      setSessionState(next);
      return next;
    },
    async signUp(email, password) {
      const result = await api.signUp(email, password);
      if (result.session) {
        setSession(result.session);
        setSessionState(result.session);
      }
      return result;
    },
    async signOut() {
      try {
        await api.logout();
      } finally {
        clearSession();
        setSessionState(null);
      }
    },
  }), [loading, session, isMock]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
