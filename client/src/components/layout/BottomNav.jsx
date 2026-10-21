import { Link, useLocation } from 'react-router-dom';
import { Home, Bookmark, User, Link2 } from 'lucide-react';

export default function BottomNav() {
  const location = useLocation();
  const navItems = [
    { name: 'Home', path: '/home', icon: Home },
    { name: 'Vault', path: '/vault', icon: Bookmark },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-[#E3D4F8] shadow-[0_-5px_20px_-5px_rgba(139,92,246,0.08)] safe-area-pb">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname.startsWith(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex flex-col items-center justify-center w-full h-full gap-1 transition-all ${
                isActive ? 'text-[#8B5CF6]' : 'text-[#776A83] hover:text-[#261B33]'
              }`}
            >
              <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-[10px] font-bold ${isActive ? 'text-[#8B5CF6] font-extrabold' : 'text-[#776A83]'}`}>{item.name}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
