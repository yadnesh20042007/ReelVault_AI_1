import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowRight, 
  Sparkles, 
  ShieldCheck, 
  Calendar, 
  CheckCircle2, 
  Compass, 
  Play
} from 'lucide-react';
import Hero3DPhone from './Hero3DPhone';

export default function HeroSection({ onSeeHowItWorks }) {
  return (
    <section className="relative w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-12 pt-8 sm:pt-14 pb-16 md:pb-24 overflow-hidden">
      
      {/* Background Lighting Accents */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[650px] h-[360px] bg-gradient-to-b from-[#A855F7]/15 via-[#C084FC]/8 to-transparent rounded-full blur-3xl pointer-events-none -z-10" />
      <div className="absolute top-44 left-10 w-72 h-72 bg-[#E879F9]/10 rounded-full blur-[110px] pointer-events-none -z-10" />

      {/* Grid overlay */}
      <div 
        className="absolute inset-0 opacity-[0.08] pointer-events-none -z-10"
        style={{
          backgroundImage: 'linear-gradient(to right, rgba(168, 85, 247, 0.25) 1px, transparent 1px), linear-gradient(to bottom, rgba(168, 85, 247, 0.25) 1px, transparent 1px)',
          backgroundSize: '3.5rem 3.5rem',
          maskImage: 'radial-gradient(ellipse at center, black 40%, transparent 75%)',
          WebkitMaskImage: 'radial-gradient(ellipse at center, black 40%, transparent 75%)'
        }}
      />

      <div className="flex flex-col lg:flex-row items-center justify-between gap-12 lg:gap-8">
        
        {/* LEFT COLUMN: Headline & CTAs */}
        <div className="flex-1 w-full max-w-2xl text-left flex flex-col items-start z-10">
          
          {/* Top Pill / Badge */}
          <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-[#1B1035] border border-[#A855F7]/35 shadow-[0_0_20px_-3px_rgba(168,85,247,0.4)] mb-6 animate-pulse-glow">
            <span className="w-2 h-2 rounded-full bg-[#E879F9] animate-ping" />
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-[#C084FC] font-mono">
              NEXT-GEN AI OPPORTUNITY RADAR
            </span>
            <span className="text-[10px] bg-[#A855F7] text-white px-2 py-0.5 rounded-full font-extrabold uppercase">
              2026
            </span>
          </div>

          {/* Main Headline */}
          <h1 className="font-heading text-4xl sm:text-6xl lg:text-[4.25rem] xl:text-[4.75rem] font-extrabold text-white leading-[1.04] tracking-tight mb-6">
            Your Next Opportunity Is{' '}
            <span className="relative inline-block">
              <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
                Just a Reel Away.
              </span>
              {/* Subtle underline glow */}
              <span className="absolute -bottom-1 left-0 right-0 h-1 bg-gradient-to-r from-[#A855F7] via-[#E879F9] to-transparent rounded-full blur-xs opacity-75" />
            </span>
          </h1>

          {/* Subheading */}
          <p className="text-base sm:text-lg lg:text-xl text-[#EDE9FE]/90 font-normal leading-relaxed max-w-xl mb-9">
            Turn short-form videos into verified hackathons, internships, scholarships, and more — powered by AI.
          </p>

          {/* Functional Navigation Buttons */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 w-full sm:w-auto mb-10">
            <Link 
              to="/auth" 
              className="group relative px-8 py-4 rounded-full bg-gradient-to-r from-[#A855F7] to-[#C084FC] hover:from-[#9333EA] hover:to-[#A855F7] text-white font-bold text-base transition-all duration-300 flex items-center justify-center gap-2.5 shadow-[0_0_25px_-5px_rgba(168,85,247,0.6)] hover:shadow-[0_0_35px_0_rgba(232,121,249,0.7)] hover:scale-[1.02] cursor-pointer"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <button 
              type="button"
              onClick={onSeeHowItWorks} 
              className="px-7 py-4 rounded-full bg-[#1B1035]/90 hover:bg-[#251545] text-white border border-[#A855F7]/35 hover:border-[#C084FC]/60 font-semibold text-base transition-all duration-300 flex items-center justify-center gap-2 backdrop-blur-md cursor-pointer hover:shadow-[0_0_20px_-5px_rgba(168,85,247,0.35)]"
            >
              <Compass className="w-4 h-4 text-[#C084FC]" />
              <span>See How It Works</span>
            </button>
          </div>

          {/* Trust Guarantees */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 w-full max-w-xl pt-4 border-t border-white/10">
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-full bg-[#A855F7]/20 border border-[#A855F7]/40 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#C084FC]" />
              </div>
              <span className="text-xs text-[#EDE9FE]/85 font-medium leading-tight">
                Official Sources Only (.gov, .edu, .ac.in)
              </span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-full bg-[#A855F7]/20 border border-[#A855F7]/40 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-3.5 h-3.5 text-[#C084FC]" />
              </div>
              <span className="text-xs text-[#EDE9FE]/85 font-medium leading-tight">
                Zero Hallucinations (Exact Quotes Required)
              </span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded-full bg-[#A855F7]/20 border border-[#A855F7]/40 flex items-center justify-center shrink-0">
                <Calendar className="w-3.5 h-3.5 text-[#C084FC]" />
              </div>
              <span className="text-xs text-[#EDE9FE]/85 font-medium leading-tight">
                Auto-Synced Deadlines (.ics Calendar Export)
              </span>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Realistic 3D Phone with Scrolling Reels */}
        <div className="flex-1 w-full flex justify-center items-center relative lg:pl-4">
          <Hero3DPhone />
        </div>

      </div>

    </section>
  );
}
