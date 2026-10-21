import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Play, ArrowRight, Menu, X } from 'lucide-react';

export default function LandingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (e, id) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }
  };

  return (
    <div className="fixed top-0 inset-x-0 z-50 p-4 sm:p-6 transition-all duration-300">
      <header 
        className={`max-w-[1360px] mx-auto rounded-full px-5 sm:px-7 py-3 sm:py-3.5 flex items-center justify-between transition-all duration-300 ${
          isScrolled 
            ? 'bg-[#10071F]/90 backdrop-blur-xl border border-[#A855F7]/30 shadow-[0_10px_35px_-10px_rgba(0,0,0,0.85),0_0_20px_-5px_rgba(168,85,247,0.25)]' 
            : 'bg-[#1B1035]/65 backdrop-blur-md border border-white/10 shadow-lg'
        }`}
      >
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 sm:w-9 sm:h-9 bg-gradient-to-tr from-[#2E184A] to-[#1B1035] rounded-full flex items-center justify-center border border-[#A855F7]/50 shadow-[0_0_15px_rgba(168,85,247,0.4)] group-hover:scale-105 transition-transform">
            <Play className="text-[#C084FC] w-4 h-4 ml-0.5 fill-[#C084FC]" />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-heading font-extrabold text-lg sm:text-xl tracking-tight text-white">
              ReelVault
            </span>
            <span className="bg-gradient-to-r from-[#A855F7] to-[#E879F9] text-white text-[10px] font-extrabold px-1.5 py-0.5 rounded-sm uppercase tracking-wider font-mono shadow-xs">
              AI
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links matching Task 3 structure */}
        <nav className="hidden md:flex items-center gap-7">
          <a 
            href="#how-it-works" 
            onClick={(e) => scrollToSection(e, 'how-it-works')} 
            className="text-xs sm:text-sm font-semibold text-gray-300 hover:text-[#C084FC] transition-colors flex items-center gap-1.5"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#E879F9] animate-pulse" />
            How It Works
          </a>
          <a 
            href="#why-reelvault" 
            onClick={(e) => scrollToSection(e, 'why-reelvault')} 
            className="text-xs sm:text-sm font-semibold text-gray-300 hover:text-[#C084FC] transition-colors"
          >
            Why ReelVault?
          </a>
          <a 
            href="#make-it-count" 
            onClick={(e) => scrollToSection(e, 'make-it-count')} 
            className="text-xs sm:text-sm font-semibold text-gray-300 hover:text-[#C084FC] transition-colors flex items-center gap-1"
          >
            <span>Make It Count</span>
            <span className="text-[10px] px-1.5 py-0.5 bg-[#A855F7]/30 text-[#E879F9] rounded-full border border-[#A855F7]/40 font-mono">⚡</span>
          </a>
          <a 
            href="#features" 
            onClick={(e) => scrollToSection(e, 'features')} 
            className="text-xs sm:text-sm font-semibold text-gray-300 hover:text-[#C084FC] transition-colors"
          >
            Features
          </a>
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3 sm:gap-4">
          <Link 
            to="/auth" 
            className="hidden sm:block text-xs sm:text-sm font-semibold text-gray-300 hover:text-white transition-colors px-3 py-1.5"
          >
            Log in
          </Link>

          <Link 
            to="/auth" 
            className="px-4 sm:px-5 py-2 sm:py-2.5 rounded-full bg-gradient-to-r from-[#A855F7] to-[#C084FC] hover:from-[#9333EA] hover:to-[#A855F7] text-white font-bold text-xs sm:text-sm transition-all shadow-[0_0_20px_-3px_rgba(168,85,247,0.5)] hover:shadow-[0_0_25px_0_rgba(232,121,249,0.7)] hover:scale-105 flex items-center gap-1.5 cursor-pointer"
          >
            <span>Get Started</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>

          {/* Mobile hamburger */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-300 hover:text-white focus:outline-none"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-2 p-5 rounded-2xl bg-[#10071F]/95 backdrop-blur-2xl border border-[#A855F7]/30 shadow-2xl flex flex-col gap-4 text-left">
          <a 
            href="#how-it-works" 
            onClick={(e) => scrollToSection(e, 'how-it-works')} 
            className="text-sm font-semibold text-gray-200 hover:text-[#C084FC] py-1 border-b border-white/5 flex items-center gap-2"
          >
            <span className="w-2 h-2 rounded-full bg-[#E879F9] animate-pulse" />
            How It Works (Demo)
          </a>
          <a 
            href="#why-reelvault" 
            onClick={(e) => scrollToSection(e, 'why-reelvault')} 
            className="text-sm font-semibold text-gray-200 hover:text-[#C084FC] py-1 border-b border-white/5"
          >
            Why ReelVault?
          </a>
          <a 
            href="#make-it-count" 
            onClick={(e) => scrollToSection(e, 'make-it-count')} 
            className="text-sm font-semibold text-gray-200 hover:text-[#C084FC] py-1 border-b border-white/5 flex items-center justify-between"
          >
            <span>Make It Count</span>
            <span className="text-[10px] px-1.5 py-0.5 bg-[#A855F7]/30 text-[#E879F9] rounded-full border border-[#A855F7]/40 font-mono">⚡</span>
          </a>
          <a 
            href="#features" 
            onClick={(e) => scrollToSection(e, 'features')} 
            className="text-sm font-semibold text-gray-200 hover:text-[#C084FC] py-1 border-b border-white/5"
          >
            Features
          </a>
          <Link 
            to="/auth" 
            onClick={() => setMobileMenuOpen(false)}
            className="text-sm font-semibold text-gray-200 hover:text-[#C084FC] py-1"
          >
            Log in to Dashboard
          </Link>
        </div>
      )}
    </div>
  );
}
