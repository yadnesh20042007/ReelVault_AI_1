import { Link, useLocation } from 'react-router-dom';
import { Home, Bookmark, User, Play, CalendarDays, Sparkles, Link2 } from 'lucide-react';
import { useLanguage } from '../../preferences/LanguageContext';
import { useAuth } from '../../auth/useAuth';
import NotificationsBell from './NotificationsBell';

export default function TopNav() {
  const location = useLocation();
  const { language, setLanguage } = useLanguage();
  const { isMock } = useAuth();
  const navItems = [
    { name: 'Home', path: '/home', icon: Home },
    { name: 'Vault', path: '/vault', icon: Bookmark },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-[#E3D4F8] shadow-[0_2px_12px_-4px_rgba(139,92,246,0.06)]">
      <div className="max-w-5xl mx-auto px-4 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Logo Section */}
        <div className="flex items-center gap-2.5">
          <Link to="/home" className="flex items-center gap-2.5 group text-left bg-transparent border-none p-1.5 -ml-1.5 rounded-2xl transition-all">
            <div className="relative w-8 h-8 md:w-9 md:h-9 bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] rounded-xl flex items-center justify-center transition-all group-hover:scale-105 shadow-sm shadow-[#8B5CF6]/30">
              <Play className="text-white w-4 h-4 ml-0.5" fill="currentColor" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-[#E9A8D4] rounded-full ring-2 ring-white flex items-center justify-center">
                <span className="w-1.5 h-1.5 bg-[#6D28D9] rounded-full animate-pulse" />
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="font-display text-xl tracking-wide uppercase mt-0.5 text-[#261B33] group-hover:text-[#8B5CF6] transition-colors">
                ReelVault
              </span>
              <span className="bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8] text-[10px] font-black px-1.5 py-0.5 rounded-md uppercase tracking-wider">
                AI
              </span>
            </div>
          </Link>

          {isMock && (
            <span
              className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8] text-[10px] font-bold uppercase tracking-wider"
              title="Running in static offline prototyping mode without backend"
            >
              <Sparkles size={11} className="text-[#8B5CF6]" />
              <span>Offline Prototyping</span>
            </span>
          )}
        </div>

        <nav className="hidden md:flex items-center gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all text-sm font-bold ${
                  isActive 
                    ? 'bg-[#8B5CF6] text-white shadow-sm shadow-[#8B5CF6]/25' 
                    : 'text-[#776A83] hover:bg-[#F0E8FF]/60 hover:text-[#261B33]'
                }`}
              >
                <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
                {item.name}
              </Link>
            );
          })}
          
          <div className="mx-2 h-6 w-px bg-[#E3D4F8]/80"></div>
          
          <NotificationsBell />
          
          <label className="ml-2 flex items-center gap-2 rounded-xl border border-[#E3D4F8] bg-white px-3 py-2 text-xs font-bold text-[#776A83] hover:border-[#8B5CF6]/50 transition-colors shadow-2xs">
            <span>Content</span>
            <select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label="Content language preference" className="cursor-pointer bg-transparent text-[#6D28D9] font-bold outline-none">
              <option value="english">English</option>
              <option value="native">Native</option>
            </select>
          </label>
        </nav>
        <div className="md:hidden flex items-center gap-2">
          {isMock && (
            <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-full bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8]">
              Mock
            </span>
          )}
          <NotificationsBell />
          <label className="flex items-center rounded-lg border border-[#E3D4F8] bg-white px-2 py-1.5 text-[10px] font-bold text-[#6D28D9]">
            <select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label="Content language preference" className="max-w-20 cursor-pointer bg-transparent outline-none">
              <option value="english">English</option>
              <option value="native">Native</option>
            </select>
          </label>
        </div>
      </div>
    </header>
  );
}
