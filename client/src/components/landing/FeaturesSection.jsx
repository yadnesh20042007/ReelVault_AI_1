import React, { useState } from 'react';
import { 
  Cpu, 
  ShieldCheck, 
  Archive, 
  Snowflake, 
  Link2, 
  CalendarDays, 
  SlidersHorizontal, 
  CheckCircle2, 
  ExternalLink, 
  Sparkles, 
  Clock, 
  ArrowUpRight, 
  FileText, 
  Search, 
  AlertTriangle,
  Building2,
  BookmarkCheck,
  ChevronRight,
  UserCheck
} from 'lucide-react';

export default function FeaturesSection() {
  const [activeFilterTag, setActiveFilterTag] = useState('2026 Batch');

  const features = [
    {
      id: 'ai-extraction',
      title: 'AI Opportunity Extraction',
      badge: 'Gemini Multimodal Neural Engine',
      icon: <Cpu className="w-6 h-6 text-[#C084FC]" />,
      summary: 'Converts fast-talking reel dialogue, captions, and text overlays into clean, structured data.',
      description: 'ReelVault parses title, organizer, eligibility, stipend, venue, and deadline. Every single field requires an exact verbatim quotation from the source transcript — preventing LLM hallucinations.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>JSON Output Schema</span>
            <span className="text-[#C084FC]">Strict Pydantic</span>
          </div>
          <div className="p-2 rounded bg-[#1B1035] border border-[#A855F7]/35">
            <div className="text-white font-bold text-xs truncate">"AI Innovation Hackathon 2026"</div>
            <div className="text-[10px] text-gray-300 mt-1 flex items-center justify-between">
              <span>Prize: ₹5,00,000</span>
              <span className="text-[#E879F9]">Quote Verified ✓</span>
            </div>
          </div>
          <div className="text-[10px] text-gray-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-[#C084FC]" /> Zero hallucination tolerance guard
          </div>
        </div>
      ),
      cols: 'lg:col-span-2'
    },
    {
      id: 'web-verification',
      title: 'Web-Based Verification',
      badge: 'LangChain + Tavily Search Agent',
      icon: <ShieldCheck className="w-6 h-6 text-emerald-400" />,
      summary: 'Autonomous agent that crawls official websites and flags lookalike scam fees.',
      description: 'The verification agent crawls official portals, verifies domain authority (.gov.in, .ac.in, .edu, official ATS), cross-checks dates, and flags fake registration fee demands.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-400">Official Domain Check</span>
            <span className="text-[9px] bg-emerald-950 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded font-bold">
              VERIFIED
            </span>
          </div>
          <div className="flex items-center gap-2 p-2 rounded bg-[#1B1035] border border-white/10">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="truncate text-white text-xs">scholarships.gov.in</div>
          </div>
          <div className="text-[10px] text-emerald-400 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Gazette circular matched • No scam fees
          </div>
        </div>
      ),
      cols: 'lg:col-span-1'
    },
    {
      id: 'personal-vault',
      title: 'Personal Vault',
      badge: 'Searchable Central Repository',
      icon: <Archive className="w-6 h-6 text-[#E879F9]" />,
      summary: 'Never lose another opportunity to screenshot clutter or saved reel graveyards.',
      description: 'Every verified hackathon, scholarship, and internship lands in your centralized vault with custom tags, status tracking (Applied, Shortlisted, Bookmarked), and instant search.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>Vault Status</span>
            <span className="text-[#C084FC]">12 Opportunities</span>
          </div>
          <div className="flex items-center justify-between p-2 rounded bg-[#1B1035] border border-white/10">
            <div className="truncate">
              <div className="text-white font-bold text-xs">AI Innovation Hackathon</div>
              <div className="text-[10px] text-[#C084FC]">Deadline in 11 days</div>
            </div>
            <span className="text-[9px] bg-[#A855F7]/25 text-[#E879F9] px-1.5 py-0.5 rounded">Saved</span>
          </div>
        </div>
      ),
      cols: 'lg:col-span-1'
    },
    {
      id: 'deep-fridge',
      title: 'Deep Fridge',
      badge: 'In-Depth Research Dossiers',
      icon: <Snowflake className="w-6 h-6 text-[#C084FC]" />,
      summary: 'Deep-dive AI research dossiers covering hidden eligibility, past winning projects, and red flags.',
      description: 'Tap "Research deeper" to launch an autonomous deep search. ReelVault inspects past competition winners, detailed application rubrics, eligibility nuances, and organizational credibility.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="flex items-center justify-between text-[10px] text-[#C084FC]">
            <span>Deep Research Dossier</span>
            <span>6 Sections</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-[10px]">
            <div className="p-1.5 rounded bg-[#150A2A] border border-[#A855F7]/25 text-gray-300">
              ✓ Past Winners
            </div>
            <div className="p-1.5 rounded bg-[#150A2A] border border-[#A855F7]/25 text-gray-300">
              ✓ Rubrics Check
            </div>
            <div className="p-1.5 rounded bg-[#150A2A] border border-[#A855F7]/25 text-gray-300">
              ✓ Eligibility
            </div>
            <div className="p-1.5 rounded bg-[#150A2A] border border-[#A855F7]/25 text-[#E879F9] font-bold">
              ✓ 0 Red Flags
            </div>
          </div>
        </div>
      ),
      cols: 'lg:col-span-2'
    },
    {
      id: 'link-shelf',
      title: 'Link Shelf',
      badge: 'Curated Direct Portals',
      icon: <Link2 className="w-6 h-6 text-[#A855F7]" />,
      summary: 'Direct repository of extracted registration portals, syllabus docs, and official guides.',
      description: 'No more clicking through 4 link-in-bio redirect hops. ReelVault extracts and resolves the true destination portal, storing it neatly on your shelf with one-click access.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>Direct Resource Portal</span>
            <span className="text-[#C084FC]">1-Click Jump</span>
          </div>
          <div className="p-2 rounded bg-[#1B1035] border border-white/10 flex items-center justify-between">
            <div className="truncate text-gray-300 text-xs">hackathon.ai/register_portal</div>
            <ExternalLink className="w-3.5 h-3.5 text-[#C084FC] shrink-0" />
          </div>
        </div>
      ),
      cols: 'lg:col-span-1'
    },
    {
      id: 'calendar-tracking',
      title: 'Calendar and Deadline Tracking',
      badge: 'Zero Missed Deadlines (.ICS)',
      icon: <CalendarDays className="w-6 h-6 text-[#E879F9]" />,
      summary: 'Automated ISO deadline resolution with Google Calendar and Apple Calendar sync.',
      description: 'ReelVault automatically converts ambiguous dates like "this Sunday" or "31st Oct" into ISO timestamps, offers 1-click .ics export, and runs automated expiry cleanup after the deadline.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="flex items-center justify-between text-[10px] text-gray-400">
            <span>Google / Apple Calendar Sync</span>
            <span className="text-[#C084FC]">Auto-Sync</span>
          </div>
          <div className="flex items-center justify-between p-2 rounded bg-[#1B1035] border border-[#A855F7]/35">
            <div>
              <div className="text-white font-bold text-xs">Deadline: Oct 31, 23:59 IST</div>
              <div className="text-[10px] text-[#C084FC]">Reminder: 48h & 2h prior</div>
            </div>
            <span className="text-[10px] bg-[#A855F7] text-white px-2 py-1 rounded font-bold">
              .ICS Export
            </span>
          </div>
        </div>
      ),
      cols: 'lg:col-span-1'
    },
    {
      id: 'personalized-recommendations',
      title: 'Personalized Recommendations',
      badge: 'Tailored to Degree & Skills',
      icon: <SlidersHorizontal className="w-6 h-6 text-[#C084FC]" />,
      summary: 'Filter verified opportunities tailored strictly to your graduation year, branch, and domain.',
      description: 'Set your profile preferences once. ReelVault automatically matches incoming reels against your engineering branch, graduation batch, and tech interests — recommending only high-fit opportunities.',
      visual: (
        <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2 text-left">
          <div className="text-[10px] text-gray-400">Interactive Match Filter:</div>
          <div className="flex flex-wrap gap-1.5">
            {['2026 Batch', 'Computer Science', 'GenAI', 'Remote', 'Scholarship'].map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => setActiveFilterTag(tag)}
                className={`px-2 py-1 rounded-md text-[10px] font-bold transition-all cursor-pointer ${
                  activeFilterTag === tag
                    ? 'bg-[#A855F7] text-white shadow-[0_0_10px_rgba(168,85,247,0.5)]'
                    : 'bg-white/10 text-gray-300 hover:bg-white/15'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
          <div className="text-[10px] text-[#C084FC] pt-1">
            ✓ 14 high-compatibility opportunities found for {activeFilterTag}
          </div>
        </div>
      ),
      cols: 'lg:col-span-1'
    }
  ];

  return (
    <section id="features" className="relative w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-12 py-20 lg:py-32">
      
      {/* Background glow */}
      <div className="absolute top-1/3 right-10 w-[500px] h-[500px] bg-[#A855F7]/10 rounded-full blur-[140px] pointer-events-none -z-10" />
      <div className="absolute bottom-10 left-10 w-[450px] h-[450px] bg-[#E879F9]/10 rounded-full blur-[120px] pointer-events-none -z-10" />

      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-16 sm:mb-20">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1B1035] border border-[#A855F7]/35 shadow-xs mb-4">
          <Sparkles className="w-3.5 h-3.5 text-[#E879F9]" />
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#C084FC] font-mono">
            CORE CAPABILITIES
          </span>
        </div>

        <h2 className="font-heading text-3xl sm:text-5xl lg:text-[3.5rem] font-extrabold text-white leading-tight tracking-tight mb-5">
          Engineered for Accuracy.{' '}
          <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
            Built for Action.
          </span>
        </h2>

        <p className="text-base sm:text-lg text-[#EDE9FE]/80 font-normal leading-relaxed">
          Seven powerful features working together to ensure you never miss a real opportunity or waste time on a scam.
        </p>
      </div>

      {/* 7 Feature Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
        {features.map((feature) => (
          <div
            key={feature.id}
            className={`rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-[#1B1035]/85 via-[#14082B]/90 to-[#0B0416]/95 backdrop-blur-xl border border-[#A855F7]/25 hover:border-[#E879F9]/50 transition-all duration-300 shadow-[0_15px_35px_-10px_rgba(0,0,0,0.6)] hover:shadow-[0_20px_45px_-10px_rgba(0,0,0,0.8),0_0_25px_-5px_rgba(168,85,247,0.3)] hover:-translate-y-1.5 group flex flex-col justify-between ${feature.cols}`}
          >
            <div>
              {/* Top Row */}
              <div className="flex items-center justify-between mb-6">
                <div className="w-12 h-12 rounded-2xl bg-[#261348] border border-[#A855F7]/40 flex items-center justify-center shadow-inner group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <span className="text-[11px] font-mono font-bold text-[#C084FC] bg-[#A855F7]/15 border border-[#A855F7]/30 px-3 py-1 rounded-full uppercase tracking-wider">
                  {feature.badge}
                </span>
              </div>

              {/* Title & Summary */}
              <h3 className="font-heading text-xl sm:text-2xl font-bold text-white group-hover:text-[#C084FC] transition-colors mb-2 text-left">
                {feature.title}
              </h3>

              <p className="text-xs sm:text-sm font-medium text-gray-300 mb-3 text-left">
                {feature.summary}
              </p>

              <p className="text-xs text-gray-400 font-normal leading-relaxed mb-6 text-left">
                {feature.description}
              </p>
            </div>

            {/* Embedded Micro Visual */}
            <div className="mt-auto pt-4 border-t border-white/10">
              {feature.visual}
            </div>
          </div>
        ))}
      </div>

    </section>
  );
}
