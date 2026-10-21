import React, { useState, useEffect } from 'react';
import { Trophy, Briefcase, GraduationCap } from 'lucide-react';

export default function InteractiveHeroVisual() {
  const [isHovered, setIsHovered] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    // Check if device supports hover
    const mediaQuery = window.matchMedia('(hover: none)');
    setIsMobile(mediaQuery.matches);
    
    // Check for reduced motion
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(motionQuery.matches);

    const handleMediaChange = (e) => setIsMobile(e.matches);
    const handleMotionChange = (e) => setReducedMotion(e.matches);

    mediaQuery.addEventListener('change', handleMediaChange);
    motionQuery.addEventListener('change', handleMotionChange);
    return () => {
      mediaQuery.removeEventListener('change', handleMediaChange);
      motionQuery.removeEventListener('change', handleMotionChange);
    };
  }, []);

  const handleInteractionEnter = () => {
    if (!isMobile) setIsHovered(true);
  };

  const handleInteractionLeave = () => {
    if (!isMobile) setIsHovered(false);
  };

  const handleTap = () => {
    if (isMobile) setIsHovered(!isHovered);
  };

  return (
    <div 
      className="w-full flex flex-col items-center justify-center relative mt-12 lg:mt-0"
      onMouseEnter={handleInteractionEnter}
      onMouseLeave={handleInteractionLeave}
      onClick={handleTap}
    >
      {/* 3D Scene Container */}
      <div 
        className="relative w-full max-w-[280px] sm:max-w-[320px] md:max-w-[350px] aspect-[9/16]"
        style={{ perspective: reducedMotion ? 'none' : '1200px' }}
      >
        
        {/* The Cards Fan */}
        <div 
          className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none"
          style={{ 
            opacity: reducedMotion ? (isHovered ? 1 : 0) : 1,
            transition: 'opacity 300ms ease',
          }}
        >
          {/* LEFT CARD */}
          <OpportunityCard 
            type="HACKATHON"
            title="AI Innovation Challenge"
            detail="₹5 Lakh Prize Pool"
            status="Applications Open"
            icon={<Trophy size={14} />}
            isActive={isHovered}
            reducedMotion={reducedMotion}
            position="left"
          />
          
          {/* CENTER CARD */}
          <OpportunityCard 
            type="INTERNSHIP"
            title="Software Development Intern"
            detail="₹30K / month"
            mode="Remote"
            status="Verified"
            icon={<Briefcase size={14} />}
            isActive={isHovered}
            reducedMotion={reducedMotion}
            position="center"
          />

          {/* RIGHT CARD */}
          <OpportunityCard 
            type="SCHOLARSHIP"
            title="₹80,000 Scholarship"
            detail="For eligible students"
            deadline="Oct 31"
            status="Verified"
            icon={<GraduationCap size={14} />}
            isActive={isHovered}
            reducedMotion={reducedMotion}
            position="right"
          />
        </div>

        {/* The Flipping Phone */}
        <div 
          className="w-full h-full relative z-10"
          style={{
            transformStyle: 'preserve-3d',
            transform: reducedMotion 
              ? 'none' 
              : `rotateY(${isHovered ? 180 : 0}deg)`,
            transition: 'transform 800ms cubic-bezier(0.4, 0.0, 0.2, 1)',
            opacity: reducedMotion ? (isHovered ? 0 : 1) : 1,
            transitionProperty: reducedMotion ? 'opacity' : 'transform'
          }}
        >
          {/* FRONT (Reel) */}
          <div 
            className="absolute inset-0 w-full h-full"
            style={{ backfaceVisibility: 'hidden' }}
          >
            <PhoneFrame>
              {/* Reel Content Wrapper */}
              <div className="flex-1 flex flex-col justify-between pt-6 pb-6 px-5 relative z-10">
                {/* Header */}
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-full bg-[#d4f954] shrink-0"></div>
                  <div className="flex flex-col">
                    <span className="text-white font-bold text-[11px] md:text-xs leading-tight">@opportunity.daily</span>
                    <span className="text-white/80 text-[9px] md:text-[10px] mt-0.5">Sponsored · 0:48</span>
                  </div>
                </div>

                {/* Main Claim */}
                <div className="font-display uppercase tracking-wide w-full flex flex-col justify-center">
                  <div className="text-white text-[1.75rem] sm:text-[2rem] md:text-[2.25rem] leading-[0.9]">₹80,000 FOR</div>
                  <div className="text-[#d4f954] text-[1.75rem] sm:text-[2rem] md:text-[2.25rem] leading-[0.9] mt-1">EVERY 12TH PASS</div>
                  <div className="text-white text-[1.75rem] sm:text-[2rem] md:text-[2.25rem] leading-[0.9] mt-1">STUDENT</div>
                </div>

                {/* Caption */}
                <div className="">
                  <p className="text-white/90 text-[10px] md:text-xs leading-relaxed max-w-[180px]">
                    Apply before Oct 31. Link in bio.
                  </p>
                </div>
              </div>
            </PhoneFrame>
          </div>

          {/* BACK (Reveal State) */}
          <div 
            className="absolute inset-0 w-full h-full"
            style={{ 
              backfaceVisibility: 'hidden',
              transform: 'rotateY(180deg)'
            }}
          >
            <PhoneFrame>
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <div className="w-16 h-16 rounded-full bg-[#d4f954]/20 flex items-center justify-center mb-4">
                  <div className="w-8 h-8 rounded-full bg-[#d4f954] flex items-center justify-center">
                    <span className="text-[#114b43] text-lg font-bold">✓</span>
                  </div>
                </div>
                <h3 className="text-white font-display uppercase tracking-wide text-2xl mb-2">Analyzed</h3>
                <p className="text-white/80 text-sm">Opportunities extracted and organized.</p>
              </div>
            </PhoneFrame>
          </div>
        </div>
      </div>

      <p className="mt-8 text-sm font-semibold text-gray-500 tracking-wide uppercase">
        {isMobile ? "Tap" : "Hover"} to reveal opportunities
      </p>
    </div>
  );
}

function PhoneFrame({ children }) {
  return (
    <div className="w-full h-full bg-[#1a1a1a] rounded-[2rem] md:rounded-[2.25rem] p-2 md:p-2.5 shadow-xl flex flex-col">
      <div className="bg-[#164E44] flex-1 w-full rounded-[1.5rem] md:rounded-[1.75rem] relative overflow-hidden flex flex-col border border-white/5">
        <div className="w-full h-8 flex items-center justify-between px-6 bg-[#1a1a1a] shrink-0">
          {[...Array(7)].map((_, i) => (
            <div key={`t-${i}`} className="w-1.5 h-1.5 rounded-full bg-white/30"></div>
          ))}
        </div>
        
        {children}

        <div className="w-full h-8 flex items-center justify-between px-6 bg-[#1a1a1a] shrink-0">
          {[...Array(7)].map((_, i) => (
            <div key={`b-${i}`} className="w-1.5 h-1.5 rounded-full bg-white/30"></div>
          ))}
        </div>
      </div>
    </div>
  );
}

function OpportunityCard({ type, title, detail, mode, deadline, status, icon, isActive, reducedMotion, position }) {
  let transform = 'translate(0, 0) rotate(0deg) scale(0.9)';
  let zIndex = 10;
  let delay = '0ms';

  if (isActive && !reducedMotion) {
    if (position === 'left') {
      transform = 'translate(-65%, 5%) rotate(-20deg) scale(1)';
      zIndex = 10;
      delay = '100ms'; // Left card starts moving after phone flip starts
    } else if (position === 'center') {
      transform = 'translate(0, -10%) rotate(0deg) scale(1)';
      zIndex = 20;
      delay = '50ms';
    } else if (position === 'right') {
      transform = 'translate(65%, 5%) rotate(20deg) scale(1)';
      zIndex = 10;
      delay = '150ms';
    }
  } else if (!isActive && !reducedMotion) {
    // Reverse animation stagger
    if (position === 'left') delay = '50ms';
    if (position === 'center') delay = '100ms';
    if (position === 'right') delay = '0ms';
  } else if (reducedMotion && isActive) {
     if (position === 'left') {
      transform = 'translate(-65%, 5%) rotate(-20deg) scale(1)';
      zIndex = 10;
    } else if (position === 'center') {
      transform = 'translate(0, -10%) rotate(0deg) scale(1)';
      zIndex = 20;
    } else if (position === 'right') {
      transform = 'translate(65%, 5%) rotate(20deg) scale(1)';
      zIndex = 10;
    }
  }

  return (
    <div 
      className="absolute w-[220px] bg-white rounded-2xl shadow-xl border border-gray-100 p-4"
      style={{
        transformOrigin: 'bottom center',
        transform,
        zIndex,
        transition: reducedMotion ? 'none' : `transform 600ms cubic-bezier(0.34, 1.56, 0.64, 1) ${delay}, opacity 400ms ease ${delay}`,
        opacity: isActive ? 1 : 0,
        pointerEvents: isActive ? 'auto' : 'none',
      }}
    >
      <div className="flex items-center gap-1.5 mb-2">
        <span className="text-[#114b43]">{icon}</span>
        <span className="text-[10px] font-bold tracking-[0.15em] text-[#114b43] uppercase">{type}</span>
      </div>
      
      <h4 className="text-sm font-bold text-[#1a1a1a] mb-1.5 leading-tight">{title}</h4>
      <p className="text-xs text-gray-600 font-medium mb-3">{detail}</p>
      
      <div className="flex flex-wrap gap-2 mt-auto border-t border-gray-100 pt-3">
        {mode && (
          <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-md text-[10px] font-semibold">
            {mode}
          </span>
        )}
        {deadline && (
          <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-md text-[10px] font-semibold">
            {deadline}
          </span>
        )}
        {status && (
          <span className="bg-[#d4f954]/20 text-[#114b43] px-2 py-1 rounded-md text-[10px] font-bold">
            {status}
          </span>
        )}
      </div>
    </div>
  );
}
