import { createContext, useContext, useMemo, useState } from 'react';

const STORAGE_KEY = 'reelvault_content_language';
const LanguageContext = createContext({ language: 'english', setLanguage: () => {} });

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem(STORAGE_KEY) === 'native' ? 'native' : 'english');
  const value = useMemo(() => ({
    language,
    setLanguage: (next) => {
      const safe = next === 'native' ? 'native' : 'english';
      localStorage.setItem(STORAGE_KEY, safe);
      setLanguage(safe);
    },
  }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

// Context hooks are intentionally exported alongside their provider.
// eslint-disable-next-line react-refresh/only-export-components
export const useLanguage = () => useContext(LanguageContext);
