import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ArrowRight, Sparkles, CheckCircle2, ShieldCheck, Calendar, Play } from 'lucide-react';

import '../components/landing/cinematic.css';
import useReducedMotion from '../components/landing/useReducedMotion';
import LandingNavbar from '../components/landing/LandingNavbar';
import HeroSection from '../components/landing/HeroSection';
import InteractiveAnalysisDemo from '../components/landing/InteractiveAnalysisDemo';
import ComparisonSection from '../components/landing/ComparisonSection';
import StopScrollingSection from '../components/landing/StopScrollingSection';
import FeaturesSection from '../components/landing/FeaturesSection';
import LandingFooter from '../components/landing/LandingFooter';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function Landing() {
  const mainRef = useRef(null);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    // Respect reduced motion
    if (prefersReducedMotion) return;

    const ctx = gsap.context(() => {
      // Smooth fade-in entrance for sections
      const revealElements = gsap.utils.toArray('.gsap-fade-section');
      revealElements.forEach((el) => {
        gsap.fromTo(
          el,
          { opacity: 0, y: 35 },
          {
            opacity: 1,
            y: 0,
            duration: 0.85,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: el,
              start: 'top 82%',
              toggleActions: 'play none none none',
            },
          }
        );
      });
    }, mainRef);

    return () => ctx.revert();
  }, [prefersReducedMotion]);

  const handleSeeHowItWorks = () => {
    const el = document.getElementById('how-it-works');
    if (el) el.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  };

  return (
    <div 
      ref={mainRef}
      className="rv-landing min-h-screen bg-[#10071F] text-[#F3E8FF] font-sans selection:bg-[#A855F7] selection:text-white overflow-x-hidden relative"
    >
      {/* Global Ambient Purple Mesh Background */}
      <div 
        className="fixed inset-0 pointer-events-none -z-20 opacity-80"
        style={{
          background: `
            radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.18) 0%, transparent 55%),
            radial-gradient(circle at 85% 25%, rgba(232, 121, 249, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 15% 65%, rgba(192, 132, 252, 0.12) 0%, transparent 50%),
            radial-gradient(circle at 50% 100%, rgba(99, 102, 241, 0.18) 0%, transparent 65%),
            #10071F
          `
        }}
      />

      {/* Subtle Grid Backdrop */}
      <div 
        className="fixed inset-0 pointer-events-none -z-20 opacity-[0.06]"
        style={{
          backgroundImage: 'radial-gradient(rgba(192, 132, 252, 0.6) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Floating Glass Navbar */}
      <LandingNavbar />

      {/* Main Content Sections: Exact 6-Stage Structure */}
      <main className="pt-24 sm:pt-28 flex flex-col items-center">
        
        {/* SECTION 1: HERO — Animated reels scrolling inside smartphone */}
        <HeroSection onSeeHowItWorks={handleSeeHowItWorks} />

        {/* SECTION 2: HOW IT WORKS — Interactive Analyse Reel demonstration */}
        <div className="w-full gsap-fade-section">
          <InteractiveAnalysisDemo />
        </div>

        {/* SECTION 3: WHY REELVAULT? — Problem and solution comparison */}
        <div className="w-full gsap-fade-section">
          <ComparisonSection />
        </div>

        {/* SECTION 4: ONE SNAP. COUNTLESS OPPORTUNITIES. — Cinematic Thanos Snap experience */}
        <div className="w-full gsap-fade-section">
          <StopScrollingSection />
        </div>

        {/* SECTION 5: FEATURES — Vault, Deep Fridge, Link Shelf, Calendar, AI Verification */}
        <div className="w-full gsap-fade-section">
          <FeaturesSection />
        </div>

        {/* SECTION 6: FINAL CTA — "Your Next Opportunity Is One Reel Away" */}
        <section className="w-full max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-12 py-16 lg:py-24 gsap-fade-section">
          <div className="rv-final-cta relative rounded-3xl p-8 sm:p-14 lg:p-16 bg-gradient-to-br from-[#1B1035] via-[#14082B] to-[#0A0216] border border-[#A855F7]/40 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9),0_0_40px_-5px_rgba(168,85,247,0.3)] text-center overflow-hidden">
            
            {/* Ambient inner purple glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[550px] h-52 bg-[#A855F7]/25 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 right-1/4 w-80 h-32 bg-[#E879F9]/15 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10 max-w-3xl mx-auto flex flex-col items-center">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#2E184A] border border-[#A855F7]/40 shadow-xs mb-6">
                <Sparkles className="w-3.5 h-3.5 text-[#E879F9]" />
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#C084FC] font-mono">
                  READY FOR HACKATHONS & CAREER BREAKTHROUGHS
                </span>
              </div>

              {/* Headline */}
              <h2 className="font-heading text-3xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight mb-5">
                Your Next Opportunity Is{' '}
                <span className="bg-gradient-to-r from-[#C084FC] via-[#E879F9] to-white bg-clip-text text-transparent">
                  One Reel Away.
                </span>
              </h2>

              <p className="text-base sm:text-lg text-[#EDE9FE]/90 font-normal leading-relaxed mb-9 max-w-xl">
                Paste any internship, hackathon, or scholarship reel and get an evidence-backed card with automated calendar alerts today.
              </p>

              {/* Final CTA Button */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
                <Link 
                  to="/auth" 
                  className="px-8 py-4 rounded-full bg-gradient-to-r from-[#A855F7] via-[#C084FC] to-[#E879F9] hover:from-[#9333EA] hover:to-[#A855F7] text-white font-bold text-base transition-all duration-300 shadow-[0_0_30px_-3px_rgba(168,85,247,0.7)] hover:shadow-[0_0_40px_0_rgba(232,121,249,0.85)] hover:scale-105 flex items-center justify-center gap-2.5 cursor-pointer"
                >
                  <span>Get Started Free</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <Link 
                  to="/home" 
                  className="px-8 py-4 rounded-full bg-white/10 hover:bg-white/15 text-white border border-white/15 hover:border-white/25 font-semibold text-base transition-all duration-200 flex items-center justify-center gap-2"
                >
                  <Play className="w-4 h-4 text-[#C084FC] fill-current" />
                  <span>Go to App Dashboard</span>
                </Link>
              </div>

              {/* Badges */}
              <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-gray-400 font-mono">
                <span className="flex items-center gap-1.5 text-gray-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#C084FC]" /> Free during public preview
                </span>
                <span className="flex items-center gap-1.5 text-gray-300">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#C084FC]" /> Zero hallucination guarantee
                </span>
                <span className="flex items-center gap-1.5 text-gray-300">
                  <Calendar className="w-3.5 h-3.5 text-[#C084FC]" /> Google & Apple Calendar export
                </span>
              </div>
            </div>

          </div>
        </section>

      </main>

      {/* Footer */}
      <LandingFooter />

    </div>
  );
}
