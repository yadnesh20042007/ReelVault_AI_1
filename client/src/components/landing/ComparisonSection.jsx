import React from 'react';
import { 
  XCircle, 
  CheckCircle2, 
  Sparkles, 
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  Clock,
  Layers
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function ComparisonSection() {
  const withoutReelVault = [
    { text: 'Save random reels', sub: 'Buried in social bookmark archives and lost in camera rolls' },
    { text: 'Forget deadlines', sub: 'Dates spoken quickly in audio are never added to your calendar' },
    { text: 'Search manually', sub: 'Wasting hours looking for official links and real registration portals' },
    { text: 'Miss opportunities', sub: 'Discovering applications closed yesterday or falling for scam fees' },
  ];

  const withReelVault = [
    { text: 'Extract opportunities', sub: 'Gemini AI automatically parses title, prize, and eligibility' },
    { text: 'Verify information', sub: 'Tavily agent cross-checks official domains (.gov, .edu, .ac.in)' },
    { text: 'Organize everything', sub: 'Centralized searchable vault with dedicated Link Shelf and Deep Fridge' },
    { text: 'Track deadlines', sub: 'Automated 1-click Google & Apple Calendar export (.ics) with alerts' },
  ];

  return (
    <section id="why-reelvault" className="relative w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-12 py-20 lg:py-28">
      
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[360px] bg-[#A855F7]/12 rounded-full blur-[130px] pointer-events-none -z-10" />

      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-16">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1B1035] border border-[#A855F7]/35 shadow-xs mb-4">
          <Sparkles className="w-3.5 h-3.5 text-[#E879F9]" />
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#C084FC] font-mono">
            WHY REELVAULT?
          </span>
        </div>

        <h2 className="font-heading text-3xl sm:text-5xl font-extrabold text-white leading-tight tracking-tight mb-4">
          The Difference Between{' '}
          <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
            Saving & Winning.
          </span>
        </h2>

        <p className="text-base sm:text-lg text-[#EDE9FE]/80 font-normal leading-relaxed">
          See why thousands of students and developers switch from chaotic bookmarking to ReelVault's verified AI pipeline.
        </p>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
        
        {/* LEFT: WITHOUT REELVAULT */}
        <div className="p-8 rounded-3xl bg-[#180A1F]/70 backdrop-blur-xl border border-rose-500/25 shadow-xl flex flex-col justify-between text-left relative overflow-hidden">
          <div className="absolute top-0 right-0 w-44 h-44 bg-rose-500/10 rounded-full blur-2xl pointer-events-none" />

          <div>
            <div className="flex items-center gap-2 mb-6">
              <span className="w-8 h-8 rounded-xl bg-rose-950/80 border border-rose-500/40 flex items-center justify-center text-rose-400">
                <XCircle className="w-5 h-5" />
              </span>
              <span className="text-sm font-mono font-bold text-rose-400 uppercase tracking-widest">
                WITHOUT REELVAULT
              </span>
            </div>

            <h3 className="font-heading text-xl sm:text-2xl font-bold text-white mb-6">
              The Frustrating Cycle
            </h3>

            <div className="space-y-4">
              {withoutReelVault.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3.5 rounded-xl bg-black/40 border border-rose-500/15">
                  <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs sm:text-sm font-bold text-gray-200">{item.text}</div>
                    <div className="text-[11px] text-gray-400 mt-0.5">{item.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-rose-500/20 text-xs font-mono text-rose-300/80">
            Result: 85% of saved reels are forgotten and never acted upon.
          </div>
        </div>

        {/* RIGHT: WITH REELVAULT */}
        <div className="p-8 rounded-3xl bg-gradient-to-br from-[#241348]/90 to-[#120724]/95 backdrop-blur-xl border border-[#A855F7]/45 shadow-[0_15px_45px_-10px_rgba(0,0,0,0.8),0_0_30px_-5px_rgba(168,85,247,0.3)] flex flex-col justify-between text-left relative overflow-hidden">
          <div className="absolute top-0 right-0 w-44 h-44 bg-[#E879F9]/15 rounded-full blur-2xl pointer-events-none" />

          <div>
            <div className="flex items-center gap-2 mb-6">
              <span className="w-8 h-8 rounded-xl bg-[#2E184A] border border-[#A855F7]/40 flex items-center justify-center text-[#C084FC]">
                <CheckCircle2 className="w-5 h-5 text-[#E879F9]" />
              </span>
              <span className="text-sm font-mono font-bold text-[#C084FC] uppercase tracking-widest">
                WITH REELVAULT
              </span>
            </div>

            <h3 className="font-heading text-xl sm:text-2xl font-bold text-white mb-6">
              The AI Opportunity Advantage
            </h3>

            <div className="space-y-4">
              {withReelVault.map((item, idx) => (
                <div key={idx} className="flex items-start gap-3 p-3.5 rounded-xl bg-black/40 border border-[#A855F7]/30">
                  <CheckCircle2 className="w-4 h-4 text-[#C084FC] shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs sm:text-sm font-bold text-white">{item.text}</div>
                    <div className="text-[11px] text-[#DDD6FE] mt-0.5">{item.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between">
            <span className="text-xs font-mono text-[#C084FC] font-bold">
              Result: Zero missed deadlines. 100% official sources.
            </span>
            <Link 
              to="/auth" 
              className="text-xs font-bold text-white bg-gradient-to-r from-[#A855F7] to-[#C084FC] hover:opacity-90 px-4 py-2 rounded-full transition-opacity flex items-center gap-1.5 shadow-md"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3 h-3 text-white" />
            </Link>
          </div>
        </div>

      </div>

    </section>
  );
}
