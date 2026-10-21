import {
  mockStore,
  isStaticAdmin,
  isMockSession,
  MOCK_ADMIN_USER,
  MOCK_ADMIN_SESSION,
} from './mockStore';

export {
  mockStore,
  isStaticAdmin,
  isMockSession,
  MOCK_ADMIN_USER,
  MOCK_ADMIN_SESSION,
};

export const DEPLOYED_BACKEND_URL = 'https://reel-vault-7r89.vercel.app';
export const LOCAL_BACKEND_URLS = ['http://127.0.0.1:8000', 'http://localhost:8000'];

const PRIMARY_URL = (import.meta.env.VITE_API_BASE_URL || DEPLOYED_BACKEND_URL).replace(/\/$/, '');

export const CANDIDATE_BACKEND_URLS = Array.from(
  new Set([
    PRIMARY_URL,
    DEPLOYED_BACKEND_URL,
    ...LOCAL_BACKEND_URLS,
  ].filter(Boolean))
);

let cachedBaseUrl = null;
let resolvePromise = null;

/**
 * Checks if a backend is healthy and responding.
 * Returns true if /healthz returns HTTP 200 OK.
 */
export async function checkBackendHealth(baseUrl, timeoutMs = 2500) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const response = await fetch(`${baseUrl}/healthz`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    clearTimeout(timer);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Discovers and returns the active API base URL.
 * Checks the deployed backend first; if unreachable, falls back to local host.
 */
export async function resolveApiBaseUrl(force = false) {
  if (cachedBaseUrl && !force) {
    return cachedBaseUrl;
  }
  if (resolvePromise && !force) {
    return resolvePromise;
  }

  resolvePromise = (async () => {
    // 1. Check deployed backend first, then local host candidates
    for (const url of CANDIDATE_BACKEND_URLS) {
      const isAlive = await checkBackendHealth(url);
      if (isAlive) {
        if (url !== PRIMARY_URL) {
          console.warn(`[ReelVault API] Primary URL (${PRIMARY_URL}) unreachable. Connected to fallback: ${url}`);
        } else {
          console.info(`[ReelVault API] Connected to backend: ${url}`);
        }
        cachedBaseUrl = url;
        return url;
      }
    }

    // If all health checks fail, default to primary/deployed URL
    console.warn(`[ReelVault API] Health checks failed for all candidates. Defaulting to: ${PRIMARY_URL}`);
    cachedBaseUrl = PRIMARY_URL;
    return cachedBaseUrl;
  })();

  try {
    return await resolvePromise;
  } finally {
    resolvePromise = null;
  }
}

// Start probing backend access immediately on app load
resolveApiBaseUrl();

export function getActiveApiBaseUrl() {
  return cachedBaseUrl || PRIMARY_URL;
}

const SESSION_KEY = 'reelvault_session';

export class ApiError extends Error {
  constructor(message, { status, code } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null');
  } catch {
    return null;
  }
}

export function setSession(session) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function errorMessage(payload, fallback) {
  const fromApp = payload?.error?.message;
  if (fromApp) return fromApp;
  const detail = payload?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return fallback;
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(errorMessage(payload, 'The request could not be completed.'), {
      status: response.status,
      code: payload?.error?.code,
    });
  }
  return payload;
}

async function sendFetch(baseUrl, path, { method = 'GET', body, auth = true } = {}) {
  const session = getSession();
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && session?.access_token) headers.Authorization = `Bearer ${session.access_token}`;
  return fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

async function refreshSession(session) {
  const baseUrl = await resolveApiBaseUrl();
  const response = await fetch(`${baseUrl}/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: session.refresh_token }),
  });
  const next = await parseResponse(response);
  setSession(next);
  return next;
}

async function request(path, { method = 'GET', body, auth = true, retry = true } = {}) {
  let session = getSession();
  let baseUrl = await resolveApiBaseUrl();

  const doSend = (targetUrl) => sendFetch(targetUrl, path, { method, body, auth });

  try {
    let response;
    try {
      response = await doSend(baseUrl);
    } catch (networkErr) {
      // Network error (e.g. server offline or CORS failure): attempt fallback candidates
      let fallbackSuccess = false;
      for (const candidate of CANDIDATE_BACKEND_URLS) {
        if (candidate !== baseUrl) {
          try {
            response = await doSend(candidate);
            console.warn(`[ReelVault API] Failover from ${baseUrl} to ${candidate}`);
            cachedBaseUrl = candidate;
            baseUrl = candidate;
            fallbackSuccess = true;
            break;
          } catch {
            // Keep looking
          }
        }
      }
      if (!fallbackSuccess) {
        throw networkErr;
      }
    }

    // If primary/deployed server crashed (5xx like FUNCTION_INVOCATION_FAILED), try local fallbacks
    if (response.status >= 500 && (baseUrl === DEPLOYED_BACKEND_URL || baseUrl === PRIMARY_URL)) {
      for (const localCandidate of LOCAL_BACKEND_URLS) {
        if (localCandidate !== baseUrl) {
          try {
            const fallbackResp = await doSend(localCandidate);
            if (fallbackResp.status < 500) {
              console.warn(`[ReelVault API] 5xx on ${baseUrl}, failover to healthy local host: ${localCandidate}`);
              cachedBaseUrl = localCandidate;
              baseUrl = localCandidate;
              response = fallbackResp;
              break;
            }
          } catch {
            // Local server not running
          }
        }
      }
    }

    if (auth && retry && response.status === 401 && session?.refresh_token) {
      try {
        session = await refreshSession(session);
        response = await doSend(baseUrl);
      } catch {
        clearSession();
      }
    }
    return parseResponse(response);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      'Unable to connect to ReelVault API server. You can also log in as admin / admin for offline prototyping.',
      { status: 503 }
    );
  }
}

export const api = {
  signUp: (email, password) => {
    return request('/v1/auth/signup', { method: 'POST', body: { email, password }, auth: false });
  },

  signIn: async (email, password) => {
    if (isStaticAdmin(email, password)) {
      return MOCK_ADMIN_SESSION;
    }
    return request('/v1/auth/login', { method: 'POST', body: { email, password }, auth: false });
  },

  me: async () => {
    if (isMockSession()) {
      return MOCK_ADMIN_USER;
    }
    return request('/v1/auth/me');
  },

  logout: async () => {
    if (isMockSession()) {
      clearSession();
      return;
    }
    return request('/v1/auth/logout', { method: 'POST', body: { all_devices: false } });
  },

  saveReel: async (url) => {
    if (isMockSession()) {
      return mockStore.saveReel(url);
    }
    return request('/v1/reels', { method: 'POST', body: { url } });
  },

  listReels: async () => {
    if (isMockSession()) {
      return mockStore.getReels();
    }
    return request('/v1/reels');
  },

  getReel: async (reelId) => {
    if (isMockSession()) {
      const reel = mockStore.getReel(reelId);
      if (!reel) throw new ApiError('Reel not found', { status: 404 });
      return reel;
    }
    return request(`/v1/reels/${reelId}`);
  },

  deleteReel: async (reelId) => {
    if (isMockSession()) {
      return mockStore.deleteReel(reelId);
    }
    return request(`/v1/reels/${reelId}`, { method: 'DELETE' });
  },

  updateReelTitle: async (reelId, title) => {
    if (isMockSession()) {
      return mockStore.updateReelTitle(reelId, title);
    }
    return request(`/v1/reels/${reelId}`, { method: 'PATCH', body: { title } });
  },

  startResearch: async (reelId, body = {}) => {
    if (isMockSession()) {
      return mockStore.startResearch(reelId, body);
    }
    return request(`/v1/reels/${reelId}/deep-cook`, { method: 'POST', body });
  },

  getResearch: async (reelId) => {
    if (isMockSession()) {
      return mockStore.getResearch(reelId);
    }
    return request(`/v1/reels/${reelId}/deep-cook`);
  },

  verifyWithTavily: async (reelId, { query, title, summary, transcript, keywords } = {}) => {
    if (isMockSession()) {
      return mockStore.verifyWithTavily(reelId, { query, title, summary, transcript, keywords });
    }
    try {
      return await request(`/v1/reels/${reelId}/verify-tavily`, {
        method: 'POST',
        body: { query, title, summary, transcript, keywords },
      });
    } catch {
      return mockStore.verifyWithTavily(reelId, { query, title, summary, transcript, keywords });
    }
  },

  listSavedLinks: async () => {
    if (isMockSession()) {
      return mockStore.getSavedLinks();
    }
    return request('/v1/reels/saved-links');
  },

  saveLink: async (reelId, body) => {
    if (isMockSession()) {
      return mockStore.saveLink(reelId, body);
    }
    return request(`/v1/reels/${reelId}/saved-links`, { method: 'POST', body });
  },

  deleteSavedLink: async (linkId) => {
    if (isMockSession()) {
      return mockStore.deleteSavedLink(linkId);
    }
    return request(`/v1/reels/saved-links/${linkId}`, { method: 'DELETE' });
  },

  listSavedDates: async () => {
    if (isMockSession()) {
      return mockStore.getSavedDates();
    }
    return request('/v1/reels/saved-dates');
  },

  saveDate: async (reelId, body) => {
    if (isMockSession()) {
      return mockStore.saveDate(reelId, body);
    }
    return request(`/v1/reels/${reelId}/saved-dates`, { method: 'POST', body });
  },

  deleteSavedDate: async (dateId) => {
    if (isMockSession()) {
      return mockStore.deleteSavedDate(dateId);
    }
    return request(`/v1/reels/saved-dates/${dateId}`, { method: 'DELETE' });
  },

  listLinkVault: async () => {
    if (isMockSession()) return mockStore.getLinkVaultEntries();
    return request('/v1/reels/link-vault');
  },

  saveLinkVault: async (reelId, body) => {
    if (isMockSession()) return mockStore.saveLinkVaultEntry(reelId, body);
    return request(`/v1/reels/${reelId}/link-vault`, { method: 'POST', body });
  },

  deleteLinkVault: async (entryId) => {
    if (isMockSession()) return mockStore.deleteLinkVaultEntry(entryId);
    return request(`/v1/reels/link-vault/${entryId}`, { method: 'DELETE' });
  },
};
