import { Link } from 'react-router-dom';
import { Play } from 'lucide-react';

export default function LandingFooter() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="w-full bg-[#090314] border-t border-white/10 pt-16 pb-12 text-left relative overflow-hidden">
      
      {/* Background ambient lighting */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[200px] bg-[#A855F7]/10 rounded-full blur-[100px] pointer-events-none -z-10" />

      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-12">
        
        {/* Top Footer Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-14">
          
          {/* Col 1: Branding & Mission */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 bg-gradient-to-tr from-[#2E184A] to-[#1B1035] rounded-full flex items-center justify-center border border-[#A855F7]/40 shadow-[0_0_15px_rgba(168,85,247,0.35)]">
                <Play className="text-[#C084FC] w-4 h-4 ml-0.5 fill-[#C084FC]" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-heading font-extrabold text-2xl tracking-tight text-white">
                  ReelVault
                </span>
                <span className="bg-gradient-to-r from-[#A855F7] to-[#E879F9] text-white text-[10px] font-extrabold px-1.5 py-0.5 rounded-sm uppercase tracking-wider font-mono">
                  AI
                </span>
              </div>
            </div>

            <p className="text-sm text-gray-400 font-normal leading-relaxed max-w-sm">
              The AI verification engine that turns unstructured short-form reels into actionable, evidence-backed opportunities with zero missed deadlines.
            </p>

            {/* System Status Pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#1B1035] border border-[#A855F7]/30 text-xs text-gray-300 font-mono">
              <span className="w-2 h-2 rounded-full bg-[#E879F9] animate-ping" />
              <span>All AI Verification Agents Operational</span>
            </div>
          </div>

          {/* Col 2: Architecture */}
          <div>
            <h4 className="font-heading text-sm font-bold text-white uppercase tracking-wider mb-4">
              Architecture
            </h4>
            <ul className="space-y-2.5 text-xs text-gray-400 font-mono">
              <li className="flex items-center gap-1.5 text-gray-300">
                <span className="text-[#C084FC]">●</span> Gemini 2.0 Flash Extraction
              </li>
              <li className="flex items-center gap-1.5 text-gray-300">
                <span className="text-[#C084FC]">●</span> Tavily Tool-Calling Agent
              </li>
              <li className="flex items-center gap-1.5 text-gray-300">
                <span className="text-[#C084FC]">●</span> SocialKit Audio Adapter
              </li>
              <li className="flex items-center gap-1.5 text-gray-300">
                <span className="text-[#C084FC]">●</span> PostgreSQL Global Dedupe
              </li>
              <li className="flex items-center gap-1.5 text-gray-300">
                <span className="text-[#C084FC]">●</span> .ICS Calendar Engine
              </li>
            </ul>
          </div>

          {/* Col 3: Navigation */}
          <div>
            <h4 className="font-heading text-sm font-bold text-white uppercase tracking-wider mb-4">
              Explore
            </h4>
            <ul className="space-y-2.5 text-xs text-gray-400 font-medium">
              <li>
                <a href="#how-it-works" className="hover:text-[#C084FC] transition-colors">
                  Interactive Demo
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-[#C084FC] transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-[#C084FC] transition-colors">
                  Core Features
                </a>
              </li>
              <li>
                <Link to="/auth" className="hover:text-[#C084FC] transition-colors">
                  Personal Vault Login
                </Link>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom Copyright */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500 font-mono">
          <div>
            © 2026 ReelVault AI. Built for hackathon presentation excellence.
          </div>

          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={scrollToTop}
              className="text-gray-400 hover:text-[#C084FC] transition-colors cursor-pointer"
            >
              Back to Top ↑
            </button>
          </div>
        </div>

      </div>

    </footer>
  );
}
