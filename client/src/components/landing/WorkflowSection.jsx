import React, { useState, useEffect } from 'react';
import { 
  Link2, 
  Headphones, 
  Cpu, 
  ShieldCheck, 
  Archive, 
  ArrowRight, 
  CheckCircle2, 
  Sparkles, 
  Play, 
  Terminal,
  Activity,
  Calendar
} from 'lucide-react';

export default function WorkflowSection() {
  const [activeStep, setActiveStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const steps = [
    {
      id: 'reel-link',
      number: '01',
      name: 'Reel Ingestion',
      tagline: 'URL Normalization & Dedupe',
      icon: <Link2 className="w-5 h-5 text-[#C084FC]" />,
      summary: 'Paste any Instagram Reel or YouTube Short URL without friction.',
      description: 'ReelVault normalizes platform shortcodes, strips tracking tokens (igsh, utm_*), and queries the global cache. If an opportunity has already been verified for another user, it returns instantly with zero latency.',
      techBadge: 'FastAPI + Redis Cache',
      terminal: [
        { label: 'INPUT', text: 'https://instagram.com/reel/DF92_kx8M/?igsh=MWx...' },
        { label: 'CLEAN', text: 'platform:instagram:DF92_kx8M' },
        { label: 'CACHE', text: 'Cache miss → enqueuing shallow cook worker #4812' }
      ],
      previewNode: (
        <div className="space-y-3">
          <div className="flex items-center gap-2 p-3 rounded-xl bg-black/60 border border-white/10 font-mono text-xs">
            <span className="text-[#A855F7] font-bold">POST</span>
            <span className="text-gray-300 truncate">/v1/submissions</span>
            <span className="ml-auto text-[10px] text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">200 OK</span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#1B1035] border border-[#A855F7]/30 flex items-center gap-3">
            <div className="w-12 h-14 rounded-lg bg-black/50 border border-white/10 flex items-center justify-center shrink-0 relative overflow-hidden">
              <Play className="w-5 h-5 text-[#C084FC] fill-current" />
              <div className="absolute bottom-0 inset-x-0 h-1 bg-[#A855F7]" />
            </div>
            <div className="text-left overflow-hidden">
              <div className="text-[10px] text-gray-400 font-mono">Instagram Reel Detected</div>
              <div className="text-xs font-bold text-white truncate">@opportunity.pulse • 48s runtime</div>
              <div className="text-[10px] text-[#C084FC] mt-0.5">Payload passed to SocialKit worker</div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'socialkit',
      number: '02',
      name: 'SocialKit Transcription',
      tagline: 'Lossless Audio & OCR Diarization',
      icon: <Headphones className="w-5 h-5 text-[#E879F9]" />,
      summary: 'High-fidelity audio transcript & caption extraction without summary loss.',
      description: 'Unlike lossy summary APIs that drop dates and URLs, ReelVault utilizes a dedicated vendor adapter to capture verbatim Hindi, Hinglish, and English audio, synchronized timestamps, and on-screen text overlays.',
      techBadge: 'SocialKit Adapter + Audio Diarization',
      terminal: [
        { label: 'AUDIO', text: 'Downloaded stereo 128kbps audio stream (0:48)' },
        { label: 'TRANSCRIBE', text: '"Attention students! ₹5 Lakh prize pool hackathon announced..."' },
        { label: 'TIMESTAMPS', text: '[00:14] "Last date to apply is October 31st on portal"' }
      ],
      previewNode: (
        <div className="space-y-3">
          <div className="p-3 rounded-xl bg-black/60 border border-white/10">
            <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 mb-2">
              <span className="flex items-center gap-1.5"><Activity className="w-3.5 h-3.5 text-[#C084FC]" /> Audio Spectrogram</span>
              <span className="text-[#E879F9]">100% Fidelity</span>
            </div>
            {/* Visualizer bars in purple neon */}
            <div className="flex items-end justify-between h-10 px-2 gap-1 bg-[#0F071D] rounded-lg p-2 border border-white/5">
              {[40, 75, 95, 60, 110, 85, 45, 90, 120, 65, 80, 100, 50, 70, 90, 40].map((h, i) => (
                <div 
                  key={i} 
                  className="w-1.5 bg-gradient-to-t from-[#A855F7] to-[#E879F9] rounded-t-sm animate-pulse"
                  style={{ height: `${h * 0.28}px`, animationDelay: `${i * 70}ms` }}
                />
              ))}
            </div>
          </div>
          <div className="p-2.5 rounded-lg bg-[#1B1035] border border-white/10 text-left font-mono text-[11px] text-gray-300">
            <span className="text-[#C084FC] font-bold">Verbatim Buffer: </span>
            "...fellowship for 2026 passouts. Monthly stipend 30000. Apply before deadline..."
          </div>
        </div>
      )
    },
    {
      id: 'gemini',
      number: '03',
      name: 'Gemini AI Extraction',
      tagline: 'Evidence-Grounded Neural Parsing',
      icon: <Cpu className="w-5 h-5 text-[#C084FC]" />,
      summary: 'Strict Pydantic schema extraction with mandatory verbatim quotes.',
      description: 'Gemini 2.0 Flash extracts title, organizer, eligibility, deadline, and URLs. Crucially, ReelVault enforces a zero-guess policy: every extracted claim must provide an exact matching substring quote from the transcript.',
      techBadge: 'Gemini 2.0 Flash + Pydantic v2',
      terminal: [
        { label: 'CLASSIFIER', text: 'is_opportunity = true (category: HACKATHON)' },
        { label: 'EXTRACT', text: 'organizer: "AI Innovation Council"' },
        { label: 'EVIDENCE', text: 'quote_matched: "₹5 Lakh prize pool for all college teams"' }
      ],
      previewNode: (
        <div className="space-y-2 text-left font-mono text-xs">
          <div className="p-3 rounded-xl bg-black/60 border border-white/10 space-y-2">
            <div className="text-[10px] text-gray-400 uppercase tracking-wider">Pydantic Evidenced Schema</div>
            <div className="p-2 rounded bg-[#1B1035] border border-[#A855F7]/30">
              <span className="text-gray-400">deadline: </span>
              <span className="text-white font-bold">"2026-10-31"</span>
              <div className="text-[10px] text-[#C084FC] mt-0.5">
                ↳ quote: <span className="underline">"apply before Oct 31"</span> (Found ✓)
              </div>
            </div>
            <div className="p-2 rounded bg-[#1B1035] border border-[#A855F7]/30">
              <span className="text-gray-400">benefit: </span>
              <span className="text-white font-bold">"₹5,00,000 Prize Pool"</span>
              <div className="text-[10px] text-[#C084FC] mt-0.5">
                ↳ quote: <span className="underline">"5 Lakhs for winners"</span> (Found ✓)
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'tavily',
      number: '04',
      name: 'Tavily Verification',
      tagline: 'Autonomous Web Fact-Checking Agent',
      icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />,
      summary: 'LangChain tool-calling agent cross-checking official domains.',
      description: 'A bounded agent issues targeted web queries to Tavily, crawls candidate websites, validates official TLDs (.gov.in, .ac.in, .edu), checks application fees, and assigns an evidence-backed verdict (OFFICIAL_CONFIRMED vs SUSPICIOUS).',
      techBadge: 'LangChain Tool-Calling + Tavily API',
      terminal: [
        { label: 'QUERY', text: 'tavily_search("AI Innovation Hackathon 2026 official")' },
        { label: 'CRAWL', text: 'fetch_page("https://ai-hackathon.org/register")' },
        { label: 'VERDICT', text: 'OFFICIAL_CONFIRMED (TLD authority check: PASS, Fee: ₹0)' }
      ],
      previewNode: (
        <div className="space-y-2.5 text-left font-mono text-xs">
          <div className="p-3 rounded-xl bg-black/60 border border-white/10 space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-gray-400">Domain Authority Check</span>
              <span className="text-emerald-400 font-bold">AUTHENTIC</span>
            </div>
            <div className="flex items-center gap-2 p-2 rounded-lg bg-[#1B1035] border border-emerald-500/30">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <div className="overflow-hidden">
                <div className="text-xs text-white font-bold truncate">ai-hackathon.org/register</div>
                <div className="text-[10px] text-emerald-400">Official registration portal • Zero fee verified</div>
              </div>
            </div>
            <div className="flex items-center justify-between px-2 py-1 text-[10px] bg-black/40 rounded border border-white/5">
              <span className="text-gray-400">Verdict Guard:</span>
              <span className="text-[#C084FC] font-bold">OFFICIAL_CONFIRMED</span>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'vault',
      number: '05',
      name: 'ReelVault Storage',
      tagline: 'Personalized Storage, Calendar & Shelf',
      icon: <Archive className="w-5 h-5 text-[#A855F7]" />,
      summary: 'Deduplicated card saved with instant calendar export & cleanup.',
      description: 'The verified opportunity card is permanently added to your personal vault, synced with your Google/Apple Calendar (.ics), pinned to your Link Shelf, and scheduled for Deep Fridge archival after its deadline expires.',
      techBadge: 'PostgreSQL + iCalendar + Celery Scheduler',
      terminal: [
        { label: 'DATABASE', text: 'Stored Opportunity in PostgreSQL with JSONB evidence citations' },
        { label: 'CALENDAR', text: 'Generated ics file with reminder (Oct 31, 23:59 IST)' },
        { label: 'CLEANUP', text: 'Scheduled automated expiry check at deadline + 48h grace' }
      ],
      previewNode: (
        <div className="p-3.5 rounded-xl bg-gradient-to-br from-[#241348] to-[#120724] border border-[#A855F7]/40 shadow-lg text-left">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-mono font-bold text-[#E879F9] uppercase tracking-wider bg-[#A855F7]/20 px-2 py-0.5 rounded border border-[#A855F7]/40">
              Saved to Vault
            </span>
            <span className="text-[10px] text-white/80 font-mono flex items-center gap-1">
              <Calendar className="w-3 h-3 text-[#C084FC]" /> Synced
            </span>
          </div>
          <div className="text-sm font-bold text-white mb-1">
            AI Innovation Hackathon 2026
          </div>
          <div className="text-xs text-[#C084FC] font-semibold mb-3">
            ₹5 Lakhs Benefit • Deadline Oct 31
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-bold">
            <div className="p-1.5 rounded bg-black/40 text-center text-gray-300 border border-white/10">
              Export .ICS
            </div>
            <div className="p-1.5 rounded bg-gradient-to-r from-[#A855F7] to-[#C084FC] text-center text-white">
              Apply Official
            </div>
          </div>
        </div>
      )
    }
  ];

  // Auto-advance loop every 4.5s
  useEffect(() => {
    if (!isAutoPlaying) return;
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length);
    }, 4500);
    return () => clearInterval(interval);
  }, [isAutoPlaying, steps.length]);

  return (
    <section id="workflow" className="relative w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-12 py-20 lg:py-32">
      
      {/* Background radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[450px] bg-[#A855F7]/12 rounded-full blur-[130px] pointer-events-none -z-10" />

      {/* Section Header */}
      <div className="text-center max-w-3xl mx-auto mb-16 sm:mb-20">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1B1035] border border-[#A855F7]/35 shadow-xs mb-4">
          <Sparkles className="w-3.5 h-3.5 text-[#E879F9]" />
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#C084FC] font-mono">
            END-TO-END PIPELINE
          </span>
        </div>

        <h2 className="font-heading text-3xl sm:text-5xl lg:text-[3.5rem] font-extrabold text-white leading-tight tracking-tight mb-5">
          From Chaotic Reel to{' '}
          <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
            Verified Opportunity.
          </span>
        </h2>

        <p className="text-base sm:text-lg text-[#EDE9FE]/80 font-normal leading-relaxed">
          How ReelVault AI turns unstructured 45-second reels into trustworthy, deadline-tracked opportunities with a bulletproof citation trail.
        </p>

        {/* Auto-play toggle */}
        <div className="mt-5 flex items-center justify-center gap-2">
          <button 
            type="button"
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className="text-xs font-mono px-3.5 py-1 rounded-full bg-[#1B1035] border border-white/10 text-gray-400 hover:text-[#C084FC] transition-colors cursor-pointer"
          >
            {isAutoPlaying ? "⏸ Pause Walkthrough" : "▶ Resume Walkthrough"}
          </button>
        </div>
      </div>

      {/* Pipeline Navigation / Stage Badges with Glowing Connector */}
      <div className="w-full max-w-5xl mx-auto mb-12 relative">
        {/* Animated glowing connection line behind badges */}
        <div className="hidden sm:block absolute top-1/2 left-8 right-8 h-0.5 bg-gradient-to-r from-[#A855F7]/20 via-[#E879F9]/50 to-[#A855F7]/20 -translate-y-1/2 z-0" />

        <div className="relative z-10 flex items-center justify-between p-2 rounded-2xl bg-[#1B1035]/80 backdrop-blur-xl border border-[#A855F7]/25 overflow-x-auto scrollbar-none shadow-xl">
          {steps.map((step, idx) => {
            const isActive = idx === activeStep;
            return (
              <button
                key={step.id}
                type="button"
                onClick={() => {
                  setActiveStep(idx);
                  setIsAutoPlaying(false);
                }}
                className={`flex-1 min-w-[130px] sm:min-w-0 py-3 px-3 rounded-xl transition-all duration-300 flex flex-col items-center gap-1 text-center cursor-pointer relative ${
                  isActive 
                    ? 'bg-gradient-to-b from-[#2E184A] to-[#1E0D36] text-white shadow-[0_0_20px_-3px_rgba(168,85,247,0.4)] border border-[#C084FC]/40' 
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`}
              >
                {/* Active indicator dot */}
                {isActive && (
                  <span className="absolute -top-1 w-2 h-2 rounded-full bg-[#E879F9] shadow-[0_0_8px_#E879F9]" />
                )}

                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-[10px] text-[#C084FC] font-bold">{step.number}</span>
                  <span className="text-xs font-bold truncate">{step.name}</span>
                </div>

                <span className="text-[10px] text-gray-400 font-mono hidden sm:block truncate">
                  {step.tagline.split(' ')[0]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Stage Detailed Spotlight Card */}
      <div className="w-full max-w-5xl mx-auto rounded-3xl bg-gradient-to-br from-[#1B1035]/95 via-[#14082B]/95 to-[#0B0416]/95 backdrop-blur-2xl border border-[#A855F7]/30 p-6 sm:p-10 shadow-[0_20px_50px_-15px_rgba(0,0,0,0.85),0_0_30px_-10px_rgba(168,85,247,0.25)] relative overflow-hidden">
        
        {/* Ambient glow inside card */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-[#E879F9]/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12 relative z-10">
          
          {/* Left Details */}
          <div className="flex-1 text-left">
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-1 rounded-md bg-[#A855F7]/20 border border-[#A855F7]/40 text-[#C084FC] font-mono text-xs font-bold">
                STAGE {steps[activeStep].number}
              </span>
              <span className="text-xs font-mono text-gray-400">
                {steps[activeStep].techBadge}
              </span>
            </div>

            <h3 className="font-heading text-2xl sm:text-3xl font-extrabold text-white mb-2">
              {steps[activeStep].name}
            </h3>

            <p className="text-sm font-semibold text-[#C084FC] mb-4 font-mono">
              {steps[activeStep].tagline}
            </p>

            <p className="text-sm sm:text-base text-[#EDE9FE]/90 font-normal leading-relaxed mb-6">
              {steps[activeStep].description}
            </p>

            {/* Terminal logs snippet */}
            <div className="rounded-xl bg-black/70 border border-white/10 p-3.5 font-mono text-[11px] space-y-1.5 shadow-inner">
              <div className="flex items-center gap-1.5 text-gray-500 pb-1 border-b border-white/5 text-[10px]">
                <Terminal className="w-3 h-3 text-[#C084FC]" />
                <span>ReelVault Execution Log</span>
              </div>
              {steps[activeStep].terminal.map((row, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-[#C084FC] font-bold text-[10px] shrink-0">[{row.label}]</span>
                  <span className="text-gray-300 break-all">{row.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right Interactive Mockup Node */}
          <div className="w-full lg:w-[380px] shrink-0 p-5 rounded-2xl bg-[#120724] border border-white/10 shadow-xl">
            <div className="flex items-center justify-between text-xs text-gray-400 font-mono pb-3 border-b border-white/10 mb-4">
              <span>Interactive Telemetry</span>
              <span className="flex items-center gap-1 text-[#E879F9]">
                <span className="w-2 h-2 rounded-full bg-[#E879F9] animate-ping" />
                Live Node
              </span>
            </div>

            {steps[activeStep].previewNode}

            <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-gray-400 font-mono">
              <button
                type="button"
                onClick={() => {
                  setActiveStep((prev) => (prev > 0 ? prev - 1 : steps.length - 1));
                  setIsAutoPlaying(false);
                }}
                className="hover:text-white transition-colors cursor-pointer"
              >
                ← Previous Stage
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveStep((prev) => (prev + 1) % steps.length);
                  setIsAutoPlaying(false);
                }}
                className="text-[#C084FC] font-bold hover:underline cursor-pointer flex items-center gap-1"
              >
                <span>Next Stage</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

        </div>

      </div>

    </section>
  );
}
