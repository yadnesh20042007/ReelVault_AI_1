import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth';

export function useProfile() {
  const { user, session } = useAuth();
  
  // Deterministic user ID from session. Fallback only if unauthenticated.
  const userId = user?.id || session?.user?.id || 'anonymous';
  const profileKey = `reelvault_profile_${userId}`;

  const [profile, setProfileState] = useState(() => {
    try {
      const saved = localStorage.getItem(profileKey);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Keep state in sync if the user logs out or switches accounts
  useEffect(() => {
    try {
      const saved = localStorage.getItem(profileKey);
      setProfileState(saved ? JSON.parse(saved) : null);
    } catch {
      setProfileState(null);
    }
  }, [profileKey]);

  const saveProfile = useCallback((newProfile) => {
    setProfileState(newProfile);
    try {
      localStorage.setItem(profileKey, JSON.stringify(newProfile));
      return true;
    } catch {
      return false;
    }
  }, [profileKey]);

  return { profile, saveProfile, userId };
}
