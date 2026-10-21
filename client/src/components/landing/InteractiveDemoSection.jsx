import React, { useState } from 'react';
import { 
  Play, 
  Search, 
  Sparkles, 
  ShieldCheck, 
  CheckCircle2, 
  ExternalLink, 
  Calendar, 
  Trophy, 
  Briefcase, 
  GraduationCap, 
  Clock, 
  Building2, 
  ArrowRight,
  Terminal,
  Loader2,
  AlertCircle
} from 'lucide-react';

export default function InteractiveDemoSection() {
  const [inputUrl, setInputUrl] = useState('https://instagram.com/reel/DF89_stem_scholarship');
  const [isVerifying, setIsVerifying] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0); // 0 = idle, 1 = socialkit, 2 = gemini, 3 = tavily, 4 = complete
  const [activePreset, setActivePreset] = useState(0);

  const presets = [
    {
      title: '₹80,000 STEM Scholarship Reel',
      url: 'https://instagram.com/reel/DF89_stem_scholarship',
      category: 'SCHOLARSHIP',
      cardTitle: 'National Science & Tech Fellowship',
      organizer: 'Dept of Science & Technology',
      benefit: '₹80,000 / year Tuition Grant',
      deadline: 'Oct 31, 2026',
      officialUrl: 'scholarships.gov.in/scheme_2026',
      verdict: 'OFFICIAL_CONFIRMED',
      verdictColor: 'text-[#d4f954] bg-[#d4f954]/20 border-[#d4f954]/40',
      icon: <GraduationCap className="w-5 h-5 text-[#d4f954]" />,
      quote: '"₹80,000 for every 12th pass & degree student... apply before Oct 31"',
      evidenceText: 'Matched official gazette publication on scholarships.gov.in. Zero application fee.'
    },
    {
      title: '$50,000 AI Hackathon Short',
      url: 'https://youtube.com/shorts/genai_aws_buildathon',
      category: 'HACKATHON',
      cardTitle: 'Global GenAI Buildathon 2026',
      organizer: 'AWS & Anthropic',
      benefit: '$50,000 Global Prize Pool',
      deadline: 'Nov 15, 2026',
      officialUrl: 'genai.aws.dev/register',
      verdict: 'OFFICIAL_CONFIRMED',
      verdictColor: 'text-[#d4f954] bg-[#d4f954]/20 border-[#d4f954]/40',
      icon: <Trophy className="w-5 h-5 text-[#d4f954]" />,
      quote: '"Fifty thousand dollar prize pool for builders worldwide... registration closes mid Nov"',
      evidenceText: 'AWS Developer Hub domain verified with HTTPS. Team registration link confirmed.'
    },
    {
      title: 'DeepMind ML Research Intern',
      url: 'https://instagram.com/reel/deepmind_fellowship_2026',
      category: 'INTERNSHIP',
      cardTitle: 'Summer ML Research Fellowship',
      organizer: 'Google DeepMind Labs',
      benefit: '₹45,000 / month • Hybrid',
      deadline: 'Dec 01, 2026',
      officialUrl: 'deepmind.google/careers/ml-fellow',
      verdict: 'OFFICIAL_CONFIRMED',
      verdictColor: 'text-emerald-400 bg-emerald-950/80 border-emerald-400/40',
      icon: <Briefcase className="w-5 h-5 text-emerald-400" />,
      quote: '"Applications open for 2026 batches... monthly stipend with mentorship"',
      evidenceText: 'Direct ATS job requisition verified. B.Tech / M.Tech 2026 students eligible.'
    }
  ];

  const handleSelectPreset = (index) => {
    setActivePreset(index);
    setInputUrl(presets[index].url);
    setPipelineStep(0);
    setIsVerifying(false);
  };

  const handleRunVerify = () => {
    setIsVerifying(true);
    setPipelineStep(1);

    setTimeout(() => {
      setPipelineStep(2);
    }, 600);

    setTimeout(() => {
      setPipelineStep(3);
    }, 1200);

    setTimeout(() => {
      setPipelineStep(4);
      setIsVerifying(false);
    }, 1800);
  };

  const current = presets[activePreset];

  return (
    <section id="demo" className="relative w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-12 py-20 lg:py-32">
      
      {/* Background glow orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[650px] h-[400px] bg-gradient-to-r from-[#d4f954]/10 via-emerald-600/10 to-teal-900/10 rounded-full blur-[130px] pointer-events-none -z-10" />

      {/* Header */}
      <div className="text-center max-w-3xl mx-auto mb-14">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#0a2717] border border-[#d4f954]/30 shadow-xs mb-4">
          <Terminal className="w-3.5 h-3.5 text-[#d4f954]" />
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#d4f954] font-mono">
            LIVE REEL INSPECTOR
          </span>
        </div>

        <h2 className="font-heading text-3xl sm:text-5xl font-extrabold text-[#FBFBF7] leading-tight tracking-tight mb-4">
          Test Reel Fact-Checking{' '}
          <span className="text-[#d4f954] text-glow-lime">In Real Time.</span>
        </h2>

        <p className="text-base sm:text-lg text-[#EDE8DF]/80 font-normal leading-relaxed">
          Select a sample opportunity reel or paste any link to see how SocialKit, Gemini, and Tavily verify claims before they reach your vault.
        </p>

        {/* Preset Selector Chips */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-2.5">
          {presets.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectPreset(idx)}
              className={`px-4 py-2 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer flex items-center gap-2 ${
                activePreset === idx
                  ? 'bg-[#d4f954] text-[#041009] shadow-[0_0_15px_rgba(212,249,84,0.4)] font-bold'
                  : 'bg-[#092215] text-gray-300 border border-white/10 hover:border-[#d4f954]/40 hover:text-white'
              }`}
            >
              <Play className={`w-3 h-3 ${activePreset === idx ? 'fill-[#041009]' : 'text-[#d4f954]'}`} />
              <span>{preset.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Interactive Terminal Bar */}
      <div className="w-full max-w-4xl mx-auto mb-10">
        <div className="p-3 sm:p-4 rounded-2xl bg-[#06180d] border border-[#d4f954]/30 shadow-xl flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="flex-1 flex items-center gap-2.5 px-3 py-2 rounded-xl bg-black/60 border border-white/10 font-mono text-xs">
            <span className="text-[#d4f954] font-bold">REEL_URL</span>
            <input 
              type="text" 
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              className="flex-1 bg-transparent text-gray-200 focus:outline-none truncate"
              placeholder="Paste Instagram Reel or YouTube Short..."
            />
          </div>

          <button
            type="button"
            onClick={handleRunVerify}
            disabled={isVerifying}
            className="px-6 py-3 rounded-xl bg-[#d4f954] hover:bg-[#bef264] text-[#041009] font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_-3px_rgba(212,249,84,0.4)] disabled:opacity-60 cursor-pointer"
          >
            {isVerifying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-[#041009]" />
                <span>Fact-Checking...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-[#041009]" />
                <span>Run Fact-Check</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Inspection Live Results Display */}
      <div className="w-full max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
        
        {/* Left: Live Pipeline Stages */}
        <div className="p-6 rounded-2xl bg-[#092215]/80 backdrop-blur-xl border border-white/10 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-gray-400 mb-4 pb-3 border-b border-white/10">
              <span className="flex items-center gap-1.5 text-white font-bold">
                <Terminal className="w-3.5 h-3.5 text-[#d4f954]" /> Verification Trace
              </span>
              <span className="text-[#d4f954]">
                {pipelineStep === 4 ? "Pipeline Finished" : isVerifying ? "Processing..." : "Ready"}
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* Step 1: SocialKit */}
              <div className={`p-3 rounded-xl border transition-all ${
                pipelineStep >= 1 ? 'bg-black/60 border-emerald-500/40 text-gray-200' : 'bg-black/20 border-white/5 text-gray-500'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">1. SocialKit Audio Ingestion</span>
                  {pipelineStep >= 1 && <span className="text-emerald-400 text-[10px]">VERBATIM (0:48) ✓</span>}
                </div>
                {pipelineStep >= 1 && (
                  <div className="text-[10px] text-gray-400 mt-1 truncate">
                    Captured audio spectrum & on-screen text overlays without summary loss.
                  </div>
                )}
              </div>

              {/* Step 2: Gemini Extraction */}
              <div className={`p-3 rounded-xl border transition-all ${
                pipelineStep >= 2 ? 'bg-black/60 border-[#d4f954]/40 text-gray-200' : 'bg-black/20 border-white/5 text-gray-500'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">2. Gemini 2.0 Pydantic Schema</span>
                  {pipelineStep >= 2 && <span className="text-[#d4f954] text-[10px]">QUOTE GROUNDED ✓</span>}
                </div>
                {pipelineStep >= 2 && (
                  <div className="text-[10px] text-gray-400 mt-1 truncate">
                    Found exact quote: {current.quote.slice(0, 45)}...
                  </div>
                )}
              </div>

              {/* Step 3: Tavily Fact-Check */}
              <div className={`p-3 rounded-xl border transition-all ${
                pipelineStep >= 3 ? 'bg-black/60 border-emerald-500/40 text-gray-200' : 'bg-black/20 border-white/5 text-gray-500'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">3. Tavily Web Authority Check</span>
                  {pipelineStep >= 3 && <span className="text-emerald-400 text-[10px]">OFFICIAL DOMAIN ✓</span>}
                </div>
                {pipelineStep >= 3 && (
                  <div className="text-[10px] text-gray-400 mt-1 truncate">
                    Verified {current.officialUrl} • Zero scam fee flags.
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs text-gray-400 font-mono">
            <span>Deterministic Guard: Active</span>
            <span className="text-emerald-400 font-bold">100% Provenance</span>
          </div>
        </div>

        {/* Right: The Resulting Verified Opportunity Card */}
        <div className="p-6 rounded-2xl bg-gradient-to-br from-[#0c2e1d] to-[#04140b] border border-[#d4f954]/40 shadow-[0_15px_35px_-10px_rgba(0,0,0,0.8),0_0_25px_-5px_rgba(212,249,84,0.2)] flex flex-col justify-between">
          <div>
            {/* Top Card Badge */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg bg-black/40 border border-white/10">
                  {current.icon}
                </span>
                <span className="text-xs font-mono font-bold text-white/90 uppercase tracking-wider">
                  {current.category}
                </span>
              </div>

              <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border flex items-center gap-1 ${current.verdictColor}`}>
                <CheckCircle2 className="w-3 h-3" /> {current.verdict}
              </span>
            </div>

            {/* Title & Organization */}
            <h3 className="font-heading text-xl font-bold text-white mb-1">
              {current.cardTitle}
            </h3>
            <div className="text-xs text-gray-300 flex items-center gap-1.5 mb-4 font-medium">
              <Building2 className="w-3.5 h-3.5 text-gray-400" />
              <span>{current.organizer}</span>
            </div>

            {/* Core Specs */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-black/40 border border-white/10 text-xs mb-4">
              <div>
                <span className="text-[10px] uppercase font-mono text-gray-400 block">Benefit / Reward</span>
                <span className="font-bold text-[#d4f954]">{current.benefit}</span>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-mono text-gray-400 block">Deadline</span>
                <span className="font-semibold text-white flex items-center justify-end gap-1">
                  <Clock className="w-3 h-3 text-[#d4f954]" /> {current.deadline}
                </span>
              </div>
            </div>

            {/* Evidence Citation */}
            <div className="p-3 rounded-xl bg-[#05170d] border border-[#d4f954]/20 text-[11px] text-gray-300 space-y-1">
              <div className="text-[10px] text-[#d4f954] font-mono font-bold uppercase">
                Citation & Evidence Trail
              </div>
              <div>{current.evidenceText}</div>
              <div className="text-[10px] text-gray-400 truncate pt-1 font-mono">
                Source: {current.officialUrl}
              </div>
            </div>
          </div>

          {/* Action CTAs */}
          <div className="mt-6 pt-4 border-t border-white/10 flex items-center gap-3">
            <button
              type="button"
              className="flex-1 py-2.5 px-3 rounded-xl bg-[#d4f954] text-[#041009] font-bold text-xs uppercase tracking-wider hover:bg-[#bef264] transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span>Add to Vault & Calendar</span>
            </button>

            <a
              href={`https://${current.officialUrl}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white border border-white/10 transition-colors"
              title="Open Official Portal"
            >
              <ExternalLink className="w-4 h-4 text-[#d4f954]" />
            </a>
          </div>
        </div>

      </div>

    </section>
  );
}
