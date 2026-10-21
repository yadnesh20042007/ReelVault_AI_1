import React from 'react';

/**
 * ThorOfficialHero: Renders the full-body Thor from the user's reference image
 * with animated lightning, glowing electric eyes, and Mjolnir energy arcs.
 */
export default function ThorOfficialHero({
  pose = 'standing', // 'standing' | 'flying-right' | 'flying-left'
  hammerImpact = false,
  className = ''
}) {
  if (pose === 'flying-right') {
    return (
      <div className={`relative inline-block select-none pointer-events-none ${className}`}>
        <img
          src="/assets/thor/thor_flight_right.png"
          alt="Thor Flying Right"
          className="w-80 sm:w-[460px] md:w-[560px] lg:w-[640px] h-auto object-contain drop-shadow-[0_10px_30px_rgba(0,0,0,0.85)]"
          draggable={false}
        />
        {/* Blazing Electric Aura during flight */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-400/20 to-purple-500/20 blur-xl pointer-events-none" />
      </div>
    );
  }

  if (pose === 'flying-left') {
    return (
      <div className={`relative inline-block select-none pointer-events-none ${className}`}>
        <img
          src="/assets/thor/thor_flight_left.png"
          alt="Thor Flying Left"
          className="w-80 sm:w-[460px] md:w-[560px] lg:w-[640px] h-auto object-contain drop-shadow-[0_10px_30px_rgba(0,0,0,0.85)]"
          draggable={false}
        />
        {/* Blazing Electric Aura during flight */}
        <div className="absolute inset-0 bg-gradient-to-l from-transparent via-cyan-400/20 to-purple-500/20 blur-xl pointer-events-none" />
      </div>
    );
  }

  // =========================================================================
  // STANDING / LANDED FULL-BODY THOR HERO
  // Full body from winged helmet down to boots, holding Mjolnir forward!
  // =========================================================================
  return (
    <div className={`relative inline-block select-none ${className}`}>
      
      {/* Ground Contact Shadow beneath boots */}
      <div 
        className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-72 sm:w-80 h-9 bg-black/80 rounded-full blur-xl pointer-events-none" 
      />

      {/* Main Full-Body Thor Image */}
      <div className="relative z-10">
        <img
          src="/assets/thor/thor_hero_clean.png"
          alt="Thor Thunder Superhero"
          className="w-64 sm:w-76 md:w-84 lg:w-[380px] h-auto object-contain transition-transform duration-300"
          style={{
            filter: hammerImpact 
              ? 'drop-shadow(0 0 40px rgba(56, 189, 248, 0.95)) drop-shadow(0 0 65px rgba(168, 85, 247, 0.8)) brightness(1.15)'
              : 'drop-shadow(0 15px 35px rgba(0,0,0,0.85)) drop-shadow(0 0 25px rgba(168, 85, 247, 0.35))',
          }}
          draggable={false}
        />

        {/* =====================================================================
            GLOWING ELECTRIC COMIC EYES (Positioned at eye coordinates: ~54% x, ~10.5% y)
            ===================================================================== */}
        <div 
          className="absolute pointer-events-none -translate-x-1/2 -translate-y-1/2 z-20"
          style={{ left: '54.5%', top: '10.5%' }}
        >
          {/* Intense electric core */}
          <div className="w-3.5 h-3.5 rounded-full bg-white shadow-[0_0_12px_#38bdf8,0_0_24px_#38bdf8,0_0_35px_#c084fc] animate-pulse" />
          {/* Electric Eye Spark Arcs */}
          <svg className="absolute -top-3 -left-3 w-10 h-10 overflow-visible opacity-90 animate-ping pointer-events-none">
            <path
              d="M 20 20 L 12 12 M 20 20 L 28 15 M 20 20 L 16 26"
              stroke="#38bdf8"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          </svg>
        </div>

        {/* =====================================================================
            MJOLNIR HAMMER CRACKLING ELECTRICITY (Hammer center: 37.2% x, 20.6% y)
            ===================================================================== */}
        <div 
          className="absolute pointer-events-none -translate-x-1/2 -translate-y-1/2 z-20"
          style={{ left: '37.2%', top: '20.6%' }}
        >
          {/* Pulsing Lightning Aura around Hammer */}
          <div 
            className={`w-28 h-28 rounded-full blur-md pointer-events-none transition-all duration-300 ${
              hammerImpact 
                ? 'bg-cyan-300/60 scale-150 animate-ping' 
                : 'bg-cyan-400/30 animate-pulse'
            }`} 
          />

          {/* Branching Lightning Bolts wrapping Hammer */}
          <svg viewBox="0 0 160 160" className="absolute -top-16 -left-16 w-36 h-36 overflow-visible">
            <defs>
              <filter id="hammerGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="3.5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Lightning Arc 1 (Cyan) */}
            <path
              d="M 80 80 L 55 50 L 72 35 L 40 20"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#hammerGlow)"
              className="animate-pulse"
            />

            {/* Lightning Arc 2 (Electric Violet) */}
            <path
              d="M 80 80 L 115 60 L 102 40 L 130 25"
              fill="none"
              stroke="#e879f9"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#hammerGlow)"
            />

            {/* Lightning Arc 3 (Blinding White Core) */}
            <path
              d="M 80 80 L 95 110 L 85 125 L 120 140"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2"
              strokeLinecap="round"
            />

            {/* Impact Flash Spark Bursts */}
            {hammerImpact && (
              <g className="animate-ping">
                <circle cx="80" cy="80" r="32" fill="rgba(56, 189, 248, 0.45)" />
                <circle cx="80" cy="80" r="16" fill="#ffffff" />
                <path d="M 80 80 L 15 80 M 80 80 L 145 80 M 80 80 L 80 15 M 80 80 L 80 145" stroke="#38bdf8" strokeWidth="3" />
              </g>
            )}
          </svg>
        </div>

      </div>

    </div>
  );
}
