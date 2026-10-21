import React from 'react';

/**
 * ThorComicHero: Renders the comic-style Thor character with dynamic
 * electric arcs, glowing lightning eyes, and Mjolnir impact effects.
 */
export default function ThorComicHero({
  direction = 'right', // 'right' | 'left'
  hammerImpact = false,
  isLanded = false,
  className = ''
}) {
  const imageSrc = direction === 'left' 
    ? '/assets/thor/thor_flying_left.png' 
    : '/assets/thor/thor_flying_right.png';

  // In 'left' orientation, the hammer and eyes coordinates flip horizontally
  const eyeX = direction === 'left' ? '43.5%' : '56.5%';
  const eyeY = '41.9%';
  const hammerX = direction === 'left' ? '16.3%' : '83.7%';
  const hammerY = '21.2%';

  return (
    <div className={`relative inline-block select-none ${className}`}>
      
      {/* Dynamic Ground Shadow when landed */}
      {isLanded && (
        <div 
          className="absolute -bottom-6 left-1/2 -translate-x-1/2 w-3/4 h-10 bg-black/70 rounded-full blur-xl pointer-events-none transition-opacity duration-500"
        />
      )}

      {/* Main Thor Character Image */}
      <div className="relative z-10">
        <img
          src={imageSrc}
          alt="Thor Thunder Superhero"
          className={`w-72 sm:w-88 md:w-[420px] lg:w-[480px] h-auto object-contain transition-transform duration-300 ${
            isLanded ? 'hover:scale-[1.02]' : ''
          }`}
          style={{
            filter: hammerImpact 
              ? 'drop-shadow(0 0 35px rgba(56, 189, 248, 0.95)) drop-shadow(0 0 60px rgba(168, 85, 247, 0.8)) brightness(1.2)'
              : 'drop-shadow(0 15px 30px rgba(0,0,0,0.8)) drop-shadow(0 0 20px rgba(168, 85, 247, 0.4))',
          }}
          draggable={false}
        />

        {/* =====================================================================
            DYNAMIC LIGHTNING EYE FLARES
            ===================================================================== */}
        <div 
          className="absolute pointer-events-none -translate-x-1/2 -translate-y-1/2 z-20"
          style={{ left: eyeX, top: eyeY }}
        >
          {/* Intense electric core */}
          <div className="w-3.5 h-3.5 rounded-full bg-white shadow-[0_0_12px_#38bdf8,0_0_24px_#38bdf8,0_0_40px_#a855f7] animate-pulse" />
          {/* Eye electricity spark arcs */}
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
            MJOLNIR HAMMER CRACKLING ELECTRICITY
            ===================================================================== */}
        <div 
          className="absolute pointer-events-none -translate-x-1/2 -translate-y-1/2 z-20"
          style={{ left: hammerX, top: hammerY }}
        >
          {/* Pulsing Lightning Aura around Hammer */}
          <div 
            className={`w-24 h-24 rounded-full blur-md pointer-events-none transition-all duration-300 ${
              hammerImpact 
                ? 'bg-cyan-300/60 scale-150 animate-ping' 
                : 'bg-cyan-400/30 animate-pulse'
            }`} 
          />

          {/* Branching Lightning Bolts wrapping Hammer */}
          <svg viewBox="0 0 160 160" className="absolute -top-16 -left-16 w-32 h-32 overflow-visible">
            <defs>
              <filter id="hammerGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Lightning Arc 1 (Cyan) */}
            <path
              d="M 80 80 L 60 55 L 75 40 L 45 25"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#hammerGlow)"
              className="animate-pulse"
            />

            {/* Lightning Arc 2 (Electric Violet) */}
            <path
              d="M 80 80 L 110 65 L 100 45 L 125 30"
              fill="none"
              stroke="#e879f9"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#hammerGlow)"
            />

            {/* Lightning Arc 3 (Blinding White Core) */}
            <path
              d="M 80 80 L 95 105 L 85 120 L 115 135"
              fill="none"
              stroke="#ffffff"
              strokeWidth="2"
              strokeLinecap="round"
            />

            {/* Impact Flash Spark Bursts */}
            {hammerImpact && (
              <g className="animate-ping">
                <circle cx="80" cy="80" r="28" fill="rgba(56, 189, 248, 0.4)" />
                <circle cx="80" cy="80" r="14" fill="#ffffff" />
                <path d="M 80 80 L 20 80 M 80 80 L 140 80 M 80 80 L 80 20 M 80 80 L 80 140" stroke="#38bdf8" strokeWidth="3" />
              </g>
            )}
          </svg>
        </div>

      </div>

    </div>
  );
}
