import React from 'react';

export default function ThorMascot({ 
  isSwinging = false, 
  showSpeech = true, 
  className = '' 
}) {
  return (
    <div className={`relative flex items-center select-none ${className}`}>
      {/* Speech bubble */}
      {showSpeech && (
        <div className="absolute -top-14 sm:-top-16 left-1/2 -translate-x-1/2 sm:-left-6 sm:translate-x-0 z-30 transition-all duration-300">
          <div className="relative bg-[#1B1035] text-white font-extrabold text-[11px] sm:text-xs px-3.5 py-1.5 rounded-2xl shadow-[0_4px_20px_rgba(168,85,247,0.5)] border-2 border-[#C084FC] whitespace-nowrap animate-bounce flex items-center gap-1.5">
            <span>Bro, you're scrolling past your future! ⚡</span>
            {/* Bubble tail */}
            <div className="absolute -bottom-1.5 left-6 w-3 h-3 bg-[#1B1035] border-r-2 border-b-2 border-[#C084FC] transform rotate-45" />
          </div>
        </div>
      )}

      {/* Chibi Thunder Superhero Mascot (Original SVG Artwork) */}
      <div className={`relative w-28 h-28 sm:w-36 sm:h-36 flex items-center justify-center transition-transform duration-500 ${
        isSwinging ? 'scale-110' : 'animate-spider-idle'
      }`}>
        {/* Soft magical lightning aura underneath */}
        <div className="absolute bottom-2 w-20 h-5 bg-[#A855F7]/30 rounded-full blur-md pointer-events-none" />

        <svg
          viewBox="0 0 140 140"
          className="w-full h-full drop-shadow-[0_10px_25px_rgba(168,85,247,0.4)] overflow-visible"
        >
          <defs>
            {/* Gradients */}
            <radialGradient id="thorFace" cx="50%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#fed7aa" />
              <stop offset="100%" stopColor="#fba973" />
            </radialGradient>
            <linearGradient id="thorHelmet" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#e2e8f0" />
              <stop offset="50%" stopColor="#94a3b8" />
              <stop offset="100%" stopColor="#475569" />
            </linearGradient>
            <linearGradient id="thorArmor" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#334155" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>
            <linearGradient id="thorCape" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#a855f7" />
              <stop offset="100%" stopColor="#6b21a8" />
            </linearGradient>
            <linearGradient id="hammerHead" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#cbd5e1" />
              <stop offset="50%" stopColor="#64748b" />
              <stop offset="100%" stopColor="#334155" />
            </linearGradient>
            <filter id="hammerGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Flowing Superhero Cape (Back) */}
          <path
            d="M48 70 C30 85, 25 110, 38 122 C55 120, 60 95, 54 75 Z"
            fill="url(#thorCape)"
            className="animate-pulse"
          />

          {/* Armored Torso */}
          <ellipse cx="68" cy="85" rx="19" ry="22" fill="url(#thorArmor)" />
          
          {/* Asgardian Circular Armor Rune Discs */}
          <circle cx="61" cy="78" r="4.5" fill="#C084FC" stroke="#e2e8f0" strokeWidth="1" />
          <circle cx="75" cy="78" r="4.5" fill="#C084FC" stroke="#e2e8f0" strokeWidth="1" />
          <circle cx="61" cy="90" r="4.5" fill="#A855F7" stroke="#e2e8f0" strokeWidth="1" />
          <circle cx="75" cy="90" r="4.5" fill="#A855F7" stroke="#e2e8f0" strokeWidth="1" />

          {/* Blonde Chibi Hair Tufts (Behind Helmet) */}
          <path d="M42 45 C40 60, 48 70, 50 72 M88 45 C90 60, 82 70, 80 72" stroke="#facc15" strokeWidth="4.5" strokeLinecap="round" />

          {/* Round Chibi Head */}
          <circle cx="68" cy="48" r="23" fill="url(#thorFace)" />

          {/* Cute Big Chibi Eyes */}
          {/* Left Eye */}
          <ellipse cx="60" cy="48" rx="3.5" ry="5.5" fill="#0f172a" />
          <circle cx="59" cy="46" r="1.5" fill="#ffffff" />
          <circle cx="61" cy="51" r="0.75" fill="#ffffff" />

          {/* Right Eye */}
          <ellipse cx="76" cy="48" rx="3.5" ry="5.5" fill="#0f172a" />
          <circle cx="75" cy="46" r="1.5" fill="#ffffff" />
          <circle cx="77" cy="51" r="0.75" fill="#ffffff" />

          {/* Determined Smile / Expression */}
          <path d="M64 58 Q68 62 72 58" fill="none" stroke="#b45309" strokeWidth="1.5" strokeLinecap="round" />

          {/* Winged Metallic Helmet */}
          <path
            d="M45 42 C45 25, 91 25, 91 42 C85 36, 51 36, 45 42 Z"
            fill="url(#thorHelmet)"
            stroke="#334155"
            strokeWidth="1.5"
          />
          {/* Helmet Brow Band */}
          <path d="M45 40 L91 40" stroke="#cbd5e1" strokeWidth="3" strokeLinecap="round" />

          {/* Left Wing on Helmet */}
          <path
            d="M46 38 C35 30, 32 15, 30 10 C36 18, 44 26, 46 38 Z"
            fill="#f8fafc"
            stroke="#94a3b8"
            strokeWidth="1"
          />
          {/* Right Wing on Helmet */}
          <path
            d="M90 38 C101 30, 104 15, 106 10 C100 18, 92 26, 90 38 Z"
            fill="#f8fafc"
            stroke="#94a3b8"
            strokeWidth="1"
          />

          {/* Left Arm / Hand */}
          <ellipse cx="48" cy="84" rx="4" ry="4" fill="#fba973" />
          <rect x="46" y="80" width="4" height="4" rx="1" fill="#64748b" />

          {/* Right Arm & Magical Hammer (Swinging or Pointing) */}
          <g 
            className="transition-transform duration-300"
            style={{
              transformOrigin: '78px 80px',
              transform: isSwinging ? 'rotate(35deg)' : 'rotate(-12deg)',
            }}
          >
            {/* Arm with bracer */}
            <path d="M78 80 L96 74" stroke="#fba973" strokeWidth="7" strokeLinecap="round" />
            <path d="M85 78 L93 75" stroke="#94a3b8" strokeWidth="6" strokeLinecap="round" />

            {/* Hammer Handle */}
            <rect x="94" y="55" width="4" height="30" rx="1.5" fill="#78350f" transform="rotate(15 96 70)" />
            {/* Handle wrap strips */}
            <line x1="94" y1="62" x2="98" y2="63" stroke="#d97706" strokeWidth="1" />
            <line x1="94" y1="68" x2="98" y2="69" stroke="#d97706" strokeWidth="1" />
            <line x1="94" y1="74" x2="98" y2="75" stroke="#d97706" strokeWidth="1" />

            {/* Hammer Head (Mjolnir Chibi Head) */}
            <rect
              x="84"
              y="42"
              width="26"
              height="16"
              rx="3"
              fill="url(#hammerHead)"
              stroke="#e2e8f0"
              strokeWidth="1.2"
              filter="url(#hammerGlow)"
              transform="rotate(15 97 50)"
            />

            {/* Magical Glowing Runes on Hammer */}
            <circle cx="97" cy="50" r="3" fill="#E879F9" className="animate-ping" />
            <path d="M93 50 L101 50 M97 46 L97 54" stroke="#ffffff" strokeWidth="1.2" strokeLinecap="round" />

            {/* Electric Lightning Sparks around Hammer */}
            <path
              d="M102 38 L108 32 L105 40 L112 36"
              fill="none"
              stroke="#C084FC"
              strokeWidth="1.8"
              strokeLinecap="round"
              className="animate-pulse"
            />
            <path
              d="M82 46 L76 42 L80 50 L74 48"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="1.6"
              strokeLinecap="round"
              className="animate-pulse"
            />
          </g>

          {/* Cute Little Boots */}
          <ellipse cx="61" cy="110" rx="5" ry="3.5" fill="#1e293b" />
          <ellipse cx="75" cy="110" rx="5" ry="3.5" fill="#1e293b" />
        </svg>
      </div>
    </div>
  );
}
