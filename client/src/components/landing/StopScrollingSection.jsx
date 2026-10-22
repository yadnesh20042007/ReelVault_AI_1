import { useEffect, useRef, useState, useId } from 'react';
import { 
  Sparkles, 
  RotateCcw, 
  Calendar, 
  CheckCircle2, 
  ShieldCheck, 
  ExternalLink, 
  ScanLine, 
  Clock, 
  Trophy,
  ArrowRight
} from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import useReducedMotion from './useReducedMotion';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

// Exact calibrated Infinity Stone locations on the 554x554 Thanos Gauntlet
const INFINITY_STONES = [
  { id: 'space', name: 'Space Stone', color: '#38BDF8', glow: 'rgba(56, 189, 248, 0.9)', x: 30.3, y: 27.6, size: 14 },
  { id: 'power', name: 'Power Stone', color: '#C084FC', glow: 'rgba(192, 132, 252, 0.95)', x: 23.8, y: 31.0, size: 15 },
  { id: 'reality', name: 'Reality Stone', color: '#F43F5E', glow: 'rgba(244, 63, 94, 0.9)', x: 19.0, y: 36.6, size: 14 },
  { id: 'time', name: 'Time Stone', color: '#10B981', glow: 'rgba(16, 185, 129, 0.9)', x: 15.9, y: 42.1, size: 14 },
  { id: 'soul', name: 'Soul Stone', color: '#F59E0B', glow: 'rgba(245, 158, 11, 0.9)', x: 15.0, y: 46.9, size: 13 },
  { id: 'mind', name: 'Mind Stone', color: '#FEF08A', glow: 'rgba(254, 240, 138, 1)', x: 29.4, y: 41.7, size: 24, isOval: true },
];

// Contact point where thumb and middle finger meet for the snap flash
const SNAP_CONTACT_POINT = { x: 25.5, y: 29.0 };

export default function StopScrollingSection() {
  const sectionRef = useRef(null);
  const thanosWrapperRef = useRef(null);
  const thanosImgRef = useRef(null);
  const rightColRef = useRef(null);
  const shockwaveRef = useRef(null);
  const flashRef = useRef(null);
  const reduced = useReducedMotion();
  const rawId = useId();
  const idPrefix = rawId.replace(/[^a-zA-Z0-9_-]/g, '');

  // Animation states: 'idle' | 'preparing' | 'snapping' | 'analyzing' | 'result'
  const [snapState, setSnapState] = useState('idle');
  const [activeStoneIndex, setActiveStoneIndex] = useState(-1);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [hasScrolledIn, setHasScrolledIn] = useState(false);

  const timersRef = useRef([]);
  const clearAllTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  useEffect(() => {
    return () => clearAllTimers();
  }, []);

  // Web Audio API synthesized cosmic snap sound (pure sine drop + white noise burst)
  const playSynthesizedSnapSound = () => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      const now = ctx.currentTime;

      // 1. Snapping transient (punchy pitch drop)
      const osc = ctx.createOscillator();
      const oscGain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(380, now);
      osc.frequency.exponentialRampToValueAtTime(45, now + 0.18);
      oscGain.gain.setValueAtTime(0.35, now);
      oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.connect(oscGain);
      oscGain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.25);

      // 2. Cosmic energy shimmer (noise burst with bandpass filter)
      const bufferSize = ctx.sampleRate * 0.45;
      const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const output = noiseBuffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) {
        output[i] = Math.random() * 2 - 1;
      }
      const whiteNoise = ctx.createBufferSource();
      whiteNoise.buffer = noiseBuffer;

      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.setValueAtTime(1400, now);
      filter.frequency.exponentialRampToValueAtTime(3200, now + 0.2);
      filter.Q.setValueAtTime(3.5, now);

      const noiseGain = ctx.createGain();
      noiseGain.gain.setValueAtTime(0.2, now);
      noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);

      whiteNoise.connect(filter);
      filter.connect(noiseGain);
      noiseGain.connect(ctx.destination);
      whiteNoise.start(now);
      whiteNoise.stop(now + 0.45);
    } catch {
      // Audio autoplay or web audio restriction fallback - completely safe
    }
  };

  // Initial scroll-in entrance animation (Requirement 3)
  useEffect(() => {
    if (reduced || !sectionRef.current) {
      setHasScrolledIn(true);
      return;
    }

    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top 75%',
        once: true,
        onEnter: () => {
          setHasScrolledIn(true);
          // Smooth entrance for section content
          if (thanosWrapperRef.current) {
            gsap.fromTo(
              thanosWrapperRef.current,
              { x: -70, opacity: 0, scale: 0.96 },
              {
                x: 0,
                opacity: 1,
                scale: 1,
                duration: 1.25,
                ease: 'power2.out',
              }
            );
          }
          // Right column content fades in smoothly
          gsap.fromTo(
            rightColRef.current,
            { opacity: 0, y: 30 },
            { opacity: 1, y: 0, duration: 1.0, delay: 0.2, ease: 'power2.out' }
          );
        },
      });
    }, sectionRef);

    return () => ctx.revert();
  }, [reduced]);

  // Main Snap Animation Execution (Requirements 4 & 5)
  const handleSnapClick = () => {
    if (snapState !== 'idle') return;
    clearAllTimers();

    setSnapState('preparing');

    // Stage A: Sequential Infinity Stones Ignition (0ms to 750ms)
    // Stones light up in sequence: Power -> Space -> Reality -> Soul -> Time -> Mind
    const stoneOrder = [1, 0, 2, 4, 3, 5];
    stoneOrder.forEach((stoneIdx, stepIdx) => {
      const t = setTimeout(() => {
        setActiveStoneIndex(stoneIdx);
      }, stepIdx * 110);
      timersRef.current.push(t);
    });

    // Thanos hand tension movement
    if (!reduced && thanosImgRef.current) {
      gsap.to(thanosImgRef.current, {
        y: -14,
        rotate: -2.5,
        scale: 1.025,
        duration: 0.75,
        ease: 'power1.inOut',
      });
    }

    // Stage B: The Snap Moment (t = 820ms)
    const snapTimer = setTimeout(() => {
      setSnapState('snapping');
      playSynthesizedSnapSound();

      // Recoil on snap
      if (!reduced && thanosImgRef.current) {
        gsap.to(thanosImgRef.current, {
          y: -8,
          rotate: 0.5,
          scale: 1.01,
          duration: 0.35,
          ease: 'elastic.out(1.2, 0.4)',
        });
      }

      // Camera shake on the entire section
      if (sectionRef.current && !reduced) {
        sectionRef.current.classList.add('rv-snap-shake');
        setTimeout(() => {
          sectionRef.current?.classList.remove('rv-snap-shake');
        }, 400);
      }
    }, 820);
    timersRef.current.push(snapTimer);

    // Stage C: Reel Analysis Demonstration (t = 1250ms)
    const analysisTimer = setTimeout(() => {
      setSnapState('analyzing');
      setAnalysisStep(1);

      // Staged data point extraction
      const s2 = setTimeout(() => setAnalysisStep(2), 700);
      const s3 = setTimeout(() => setAnalysisStep(3), 1400);
      const s4 = setTimeout(() => setAnalysisStep(4), 2100);

      // Stage D: Polished Result Assembly (t = 3000ms after analysis start)
      const resultTimer = setTimeout(() => {
        setSnapState('result');
      }, 2900);

      timersRef.current.push(s2, s3, s4, resultTimer);
    }, 1250);
    timersRef.current.push(analysisTimer);
  };

  // Reset function ("Snap Again")
  const handleReset = () => {
    clearAllTimers();
    setSnapState('idle');
    setActiveStoneIndex(-1);
    setAnalysisStep(0);

    if (thanosImgRef.current) {
      gsap.to(thanosImgRef.current, {
        y: 0,
        rotate: 0,
        scale: 1,
        duration: 0.5,
        ease: 'power2.out',
      });
    }
  };

  return (
    <section 
      ref={sectionRef} 
      id="make-it-count" 
      className="rv-thanos-section relative w-full px-4 sm:px-6 lg:px-12 py-16 lg:py-24 overflow-hidden select-none"
      aria-label="Infinite Snap Experience"
    >
      {/* Background Cosmic Particle Field */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10" aria-hidden="true">
        {/* Deep Cosmic Radial Backdrop */}
        <div 
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(circle at 30% 50%, rgba(109, 40, 217, 0.22) 0%, rgba(16, 7, 31, 0.95) 75%)'
          }}
        />

        {/* Ambient Nebula Light Pulses */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#8B5CF6]/15 rounded-full blur-[110px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[480px] h-[480px] bg-[#E879F9]/10 rounded-full blur-[140px]" />

        {/* Floating Cosmic Dust Stars */}
        {[
          { top: '15%', left: '10%', size: 3, delay: '0s' },
          { top: '25%', left: '85%', size: 4, delay: '1.5s' },
          { top: '65%', left: '20%', size: 3, delay: '2.5s' },
          { top: '75%', left: '75%', size: 5, delay: '0.8s' },
          { top: '45%', left: '92%', size: 3, delay: '3.2s' },
          { top: '85%', left: '40%', size: 4, delay: '4.1s' },
          { top: '12%', left: '60%', size: 3, delay: '1.9s' },
        ].map((p, i) => (
          <div
            key={i}
            className="rv-cosmic-dust-particle bg-white/70 shadow-[0_0_8px_#ffffff]"
            style={{
              top: p.top,
              left: p.left,
              width: `${p.size}px`,
              height: `${p.size}px`,
              animationDelay: p.delay,
            }}
          />
        ))}
      </div>

      {/* Section Top Eyebrow Banner */}
      <div className="max-w-[1360px] mx-auto text-center mb-10 sm:mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#1F103A] border border-[#A855F7]/40 shadow-[0_0_20px_rgba(168,85,247,0.25)]">
          <Sparkles className="w-3.5 h-3.5 text-[#E879F9] animate-pulse" />
          <span className="text-xs font-bold uppercase tracking-[0.22em] text-[#C084FC] font-mono">
            04 / INFINITE POTENTIAL
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-[1360px] mx-auto flex justify-center items-center">
        
        {/* =========================================================================
            HEADLINE, INTERACTIVE SNAP BUTTON & REEL ANALYSIS DEMO
            ========================================================================= */}
        <div ref={rightColRef} className="w-full max-w-3xl flex flex-col justify-center text-left">
          
          {/* Main Stage Switcher */}
          {snapState === 'idle' || snapState === 'preparing' || snapState === 'snapping' ? (
            
            /* STAGE 1: IDLE / PRE-SNAP HEADLINE & INTERACTIVE BUTTON */
            <div className="space-y-6">
              
              {/* Headline (Requirement 4) */}
              <h2 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight leading-[1.08]">
                ONE SNAP. <br />
                <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
                  COUNTLESS OPPORTUNITIES.
                </span>
              </h2>

              {/* Subtitle (Requirement 4) */}
              <p className="text-lg sm:text-xl text-[#EDE9FE]/90 font-normal leading-relaxed max-w-xl">
                Turn that reel into something worth saving.
              </p>

              {/* Unprocessed Reel Teaser Card */}
              <div className="rounded-2xl bg-[#1B1035]/70 border border-[#A855F7]/30 p-4 sm:p-5 backdrop-blur-md max-w-lg shadow-xl">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-14 rounded-xl bg-gradient-to-br from-[#2E184A] to-[#14082B] border border-[#A855F7]/40 flex items-center justify-center shrink-0 shadow-inner">
                    <Trophy className="w-5 h-5 text-[#E879F9]" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#A855F7]/25 text-[#E9D5FF] font-bold">
                        Unprocessed Video Reel
                      </span>
                      <span className="text-xs text-gray-400">@tech_creator · Instagram</span>
                    </div>
                    <p className="text-sm font-semibold text-white truncate">
                      “National Innovation Hackathon 2026 announced! $30k prizes, free registration...”
                    </p>
                  </div>
                </div>
              </div>

              {/* Interactive Snap Button (Requirement 4) */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={handleSnapClick}
                  disabled={snapState !== 'idle'}
                  className={`group relative px-8 sm:px-10 py-5 rounded-2xl font-heading font-extrabold text-lg sm:text-xl tracking-wide uppercase text-white transition-all duration-300 cursor-pointer flex items-center justify-center gap-3.5 shadow-[0_0_35px_rgba(168,85,247,0.5)] ${
                    snapState === 'idle'
                      ? 'bg-gradient-to-r from-[#8B5CF6] via-[#A855F7] to-[#E9A8D4] hover:from-[#7C3AED] hover:to-[#A855F7] hover:scale-105 hover:shadow-[0_0_55px_rgba(232,121,249,0.85)] border border-[#E9A8D4]/60'
                      : 'bg-[#4C1D95] opacity-90 scale-95 border border-[#A855F7]/40'
                  }`}
                  aria-label="Snap to analyse demonstration reel"
                >
                  <Sparkles className="w-6 h-6 text-[#FEF08A] group-hover:rotate-12 transition-transform drop-shadow-[0_0_8px_#fef08a]" />
                  <span>
                    {snapState === 'idle' 
                      ? 'SNAP TO ANALYSE ✨' 
                      : snapState === 'preparing'
                      ? 'GATHERING POWER…' 
                      : 'SNAPPING REALITY…'}
                  </span>
                </button>
              </div>

              {/* Helper Micro-copy */}
              <p className="text-xs font-mono text-[#C084FC]/70">
                Click to activate the snap and transform the reel into verified data.
              </p>

            </div>

          ) : snapState === 'analyzing' ? (

            /* STAGE 2: LIVE REEL ANALYSIS SCANNING BEAM (Stage C) */
            <div className="space-y-5 animate-fadeIn">
              
              <div className="flex items-center gap-2">
                <ScanLine className="w-5 h-5 text-[#E879F9] animate-spin" />
                <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#C084FC] font-bold">
                  STAGE C · QUANTUM ANALYSIS IN PROGRESS
                </span>
              </div>

              <h3 className="font-heading text-2xl sm:text-3xl font-bold text-white">
                Deconstructing Spoken Reel Audio & Visual Signals…
              </h3>

              {/* Scanning Reel Frame */}
              <div className="relative rounded-2xl bg-[#14082B] border border-[#A855F7]/50 p-5 overflow-hidden shadow-2xl">
                
                {/* Vertical Laser Scanning Beam Sweep */}
                <div className="rv-laser-scan-bar" aria-hidden="true" />

                {/* Cyber Scanline Grid Overlay */}
                <div 
                  className="absolute inset-0 pointer-events-none opacity-20"
                  style={{
                    backgroundImage: 'linear-gradient(rgba(192, 132, 252, 0.4) 1px, transparent 1px)',
                    backgroundSize: '100% 4px',
                  }}
                />

                <div className="relative z-10 space-y-3.5">
                  <div className="flex items-center justify-between border-b border-[#A855F7]/30 pb-3">
                    <span className="text-xs font-mono text-[#E9D5FF] font-semibold">
                      INPUT STREAM: https://instagram.com/reel/DF89_hackathon
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" /> SCANNING
                    </span>
                  </div>

                  {/* Progressive Extracted Attributes */}
                  <div className="space-y-2.5">
                    <div className={`p-2.5 rounded-xl border transition-all duration-300 ${
                      analysisStep >= 1 
                        ? 'bg-[#2E184A]/80 border-[#C084FC]/50 text-white' 
                        : 'bg-white/5 border-white/10 text-gray-500'
                    }`}>
                      <span className="text-[10px] font-mono uppercase text-[#C084FC] block">
                        01. Spoken Transcript Captured
                      </span>
                      <p className="text-xs font-medium">
                        “National Innovation Hackathon 2026. $30,000 global prize pool, application deadline is November 30...”
                      </p>
                    </div>

                    <div className={`p-2.5 rounded-xl border transition-all duration-300 ${
                      analysisStep >= 2 
                        ? 'bg-[#2E184A]/80 border-[#C084FC]/50 text-white' 
                        : 'bg-white/5 border-white/10 text-gray-500'
                    }`}>
                      <span className="text-[10px] font-mono uppercase text-[#C084FC] block">
                        02. Opportunity Classification
                      </span>
                      <p className="text-xs font-bold text-[#E879F9]">
                        HACKATHON · GLOBAL TECH CHALLENGE
                      </p>
                    </div>

                    <div className={`p-2.5 rounded-xl border transition-all duration-300 ${
                      analysisStep >= 3 
                        ? 'bg-[#2E184A]/80 border-[#C084FC]/50 text-white' 
                        : 'bg-white/5 border-white/10 text-gray-500'
                    }`}>
                      <span className="text-[10px] font-mono uppercase text-[#C084FC] block">
                        03. Hard Deadline Extracted
                      </span>
                      <p className="text-xs font-semibold text-amber-300 flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5" /> 30 November 2026
                      </p>
                    </div>

                    <div className={`p-2.5 rounded-xl border transition-all duration-300 ${
                      analysisStep >= 4 
                        ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300' 
                        : 'bg-white/5 border-white/10 text-gray-500'
                    }`}>
                      <span className="text-[10px] font-mono uppercase text-emerald-400 block">
                        04. Tavily Real-Time Domain Cross-Check
                      </span>
                      <p className="text-xs font-bold flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> TLD Authority Verified: innovation-hackathon.gov
                      </p>
                    </div>
                  </div>
                </div>

              </div>

            </div>

          ) : (

            /* STAGE 3: FINAL STATE — ASSEMBLED OPPORTUNITY CARD (Stage D) */
            <div className="space-y-6 animate-fadeIn">
              
              {/* Final State Banner Headline (Requirement 5 Stage D) */}
              <div>
                <span className="text-xs font-mono uppercase tracking-[0.25em] text-[#C084FC] font-bold block mb-1">
                  REALITY ASSEMBLED
                </span>
                <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight">
                  REAL OPPORTUNITIES. <br />
                  <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
                    ZERO MISSED CHANCES.
                  </span>
                </h2>
              </div>

              {/* Polished Opportunity Card Result */}
              <article 
                className="rounded-3xl bg-[#1B1035] border-2 border-[#A855F7]/60 p-6 sm:p-7 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.9),0_0_35px_rgba(168,85,247,0.35)] relative overflow-hidden"
              >
                {/* Subtle cosmic energy ring around card */}
                <div 
                  className="absolute -top-24 -right-24 w-52 h-52 bg-[#E879F9]/15 rounded-full blur-2xl pointer-events-none"
                  aria-hidden="true" 
                />

                {/* Card Header: Category & Demo Verification Label */}
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-full bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-white text-xs font-extrabold uppercase tracking-wider font-mono shadow-xs">
                      Hackathon
                    </span>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/70 border border-emerald-500/50 text-emerald-300 text-xs font-bold">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Demo verification
                    </span>
                  </div>
                  <span className="text-xs font-mono text-gray-400">
                    ID: RV-DEMO-2026
                  </span>
                </div>

                {/* Title (Requirement 5 Stage C/D) */}
                <h3 className="font-heading text-2xl sm:text-3xl font-extrabold text-white leading-snug mb-2">
                  National Innovation Hackathon
                </h3>

                {/* Organizer & Benefits */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-4 py-3 border-y border-white/10">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400 block mb-0.5">
                      Prize Pool & Grant
                    </span>
                    <p className="text-sm font-bold text-emerald-400 flex items-center gap-1">
                      <Trophy className="w-4 h-4 text-emerald-400 shrink-0" />
                      ₹25,00,000 ($30,000) + Cloud Credits
                    </p>
                  </div>
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400 block mb-0.5">
                      Deadline
                    </span>
                    <p className="text-sm font-bold text-amber-300 flex items-center gap-1">
                      <Clock className="w-4 h-4 text-amber-300 shrink-0" />
                      Demo deadline — 30 November
                    </p>
                  </div>
                </div>

                {/* Card Action Controls */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <button
                      type="button"
                      className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-white text-xs font-bold hover:opacity-90 transition-opacity flex items-center gap-1.5 shadow-sm cursor-pointer"
                      onClick={() => alert('Demo simulated: Event added to your Google/Apple Calendar.')}
                    >
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Add to Calendar (Demo)</span>
                    </button>

                    <a
                      href="#make-it-count"
                      className="px-3.5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-gray-200 text-xs font-semibold transition-colors flex items-center gap-1"
                      onClick={(e) => { e.preventDefault(); alert('Demo simulated: Verified official registration portal link.'); }}
                    >
                      <span>Official Portal</span>
                      <ExternalLink className="w-3 h-3 text-gray-400" />
                    </a>
                  </div>

                  <span className="text-[11px] font-mono text-gray-400 italic">
                    Simulated card
                  </span>
                </div>

                {/* Mandatory Disclaimer (Requirement 5 Stage C) */}
                <div className="mt-4 pt-3 border-t border-white/5 text-[11px] font-mono text-gray-400">
                  <p>
                    ⚠️ <strong>Notice:</strong> This is fictional demo data for frontend landing demonstration. Not an active opportunity.
                  </p>
                </div>
              </article>

              {/* Snap Again Interactive Replay Button (Requirement 5 Stage D) */}
              <div className="flex items-center gap-4 pt-2">
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-6 py-3.5 rounded-xl bg-white/10 hover:bg-white/15 border border-white/20 text-white font-bold text-sm transition-all hover:scale-105 flex items-center gap-2 cursor-pointer shadow-sm"
                  aria-label="Replay the snap interaction"
                >
                  <RotateCcw className="w-4 h-4 text-[#C084FC]" />
                  <span>Snap Again</span>
                </button>

                <p className="text-xs text-gray-400 font-mono">
                  Replays the cinematic snap sequence cleanly without page refresh.
                </p>
              </div>

            </div>

          )}

        </div>

      </div>

    </section>
  );
}
