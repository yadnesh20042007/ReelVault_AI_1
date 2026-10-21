import React from 'react';

export default function SpiderMascot({ className = '' }) {
  return (
    <div className={`relative flex items-center select-none ${className}`}>
      {/* Speech bubble */}
      <div className="absolute -top-10 left-1/2 -translate-x-1/2 sm:-top-11 sm:-left-3 sm:translate-x-0 z-30">
        <div className="relative bg-white text-[#10071F] font-bold text-[11px] sm:text-xs px-3 py-1 rounded-full shadow-[0_4px_15px_rgba(232,121,249,0.3)] border-2 border-[#E879F9] whitespace-nowrap animate-bounce">
          <span>Click here! ✨</span>
          {/* Speech bubble tail pointer */}
          <div className="absolute -bottom-1.5 left-4 w-3 h-3 bg-white border-r-2 border-b-2 border-[#E879F9] transform rotate-45" />
        </div>
      </div>

      {/* Spider-themed cartoon mascot character (Original SVG artwork) */}
      <div className="relative animate-spider-idle w-24 h-24 sm:w-28 sm:h-28 flex items-center justify-center">
        
        {/* Ambient shadow underneath */}
        <div className="absolute bottom-1 w-14 h-3 bg-black/40 rounded-full blur-xs pointer-events-none" />

        <svg
          viewBox="0 0 120 120"
          className="w-full h-full drop-shadow-[0_8px_16px_rgba(168,85,247,0.35)] overflow-visible"
        >
          <defs>
            <radialGradient id="spiderHeadGlow" cx="50%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#ff4d4d" />
              <stop offset="85%" stopColor="#d11a2a" />
              <stop offset="100%" stopColor="#990012" />
            </radialGradient>
            <linearGradient id="spiderBlueSuit" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#2563eb" />
              <stop offset="100%" stopColor="#1e3a8a" />
            </linearGradient>
            <linearGradient id="spiderGlove" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ef4444" />
              <stop offset="100%" stopColor="#b91c1c" />
            </linearGradient>
          </defs>

          {/* Body / Torso (Blue with Red Chest Webbing) */}
          <ellipse cx="60" cy="80" rx="18" ry="19" fill="url(#spiderBlueSuit)" />
          {/* Red Chest Vest */}
          <path
            d="M52 68 C55 64, 65 64, 68 68 L67 86 C64 89, 56 89, 53 86 Z"
            fill="#d11a2a"
          />
          {/* Chest Spider Emblem */}
          <circle cx="60" cy="76" r="2.5" fill="#111827" />
          <path d="M57 74 L54 71 M63 74 L66 71 M57 77 L53 79 M63 77 L67 79" stroke="#111827" strokeWidth="1.2" strokeLinecap="round" />

          {/* Left Hand (resting playfully on hip) */}
          <path
            d="M44 76 C40 78, 38 84, 43 86 C47 88, 50 82, 48 78"
            fill="url(#spiderGlove)"
            stroke="#7f1d1d"
            strokeWidth="0.8"
          />

          {/* Right Arm & Hand Pointing enthusiastically */}
          <g className="animate-point-nudge">
            {/* Blue Arm extending */}
            <path
              d="M74 74 C82 72, 88 74, 95 72"
              fill="none"
              stroke="url(#spiderBlueSuit)"
              strokeWidth="7"
              strokeLinecap="round"
            />
            {/* Red Glove sleeve */}
            <path
              d="M92 72 L102 70"
              stroke="url(#spiderGlove)"
              strokeWidth="6"
              strokeLinecap="round"
            />
            {/* Pointing Index Finger */}
            <path
              d="M100 70 L110 68"
              stroke="url(#spiderGlove)"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
            {/* Thumb */}
            <path
              d="M99 68 C100 65, 102 65, 102 68"
              stroke="url(#spiderGlove)"
              strokeWidth="3"
              strokeLinecap="round"
            />
            {/* Little energy sparkles near pointing finger */}
            <circle cx="114" cy="67" r="1.5" fill="#E879F9" className="animate-ping" />
            <circle cx="112" cy="64" r="1" fill="#C084FC" />
          </g>

          {/* Spider Head (Round Cute Mask) */}
          <circle cx="60" cy="46" r="25" fill="url(#spiderHeadGlow)" stroke="#7f1d1d" strokeWidth="1" />

          {/* Head Webbing Lines */}
          <path
            d="M60 21 L60 71 M35 46 L85 46 M42 28 L78 64 M42 64 L78 28"
            stroke="#500707"
            strokeWidth="0.75"
            opacity="0.6"
          />
          {/* Concentric Web Loops */}
          <circle cx="60" cy="46" r="10" fill="none" stroke="#500707" strokeWidth="0.7" opacity="0.5" />
          <circle cx="60" cy="46" r="18" fill="none" stroke="#500707" strokeWidth="0.7" opacity="0.5" />

          {/* Left Big Comic Eye */}
          <path
            d="M44 42 C44 32, 54 36, 56 46 C56 50, 48 52, 44 42 Z"
            fill="#ffffff"
            stroke="#111827"
            strokeWidth="2.5"
          />
          {/* Left Eye Pupil Shine */}
          <ellipse cx="50" cy="42" rx="2" ry="3" fill="#e0e7ff" />

          {/* Right Big Comic Eye */}
          <path
            d="M76 42 C76 32, 66 36, 64 46 C64 50, 72 52, 76 42 Z"
            fill="#ffffff"
            stroke="#111827"
            strokeWidth="2.5"
          />
          {/* Right Eye Pupil Shine */}
          <ellipse cx="70" cy="42" rx="2" ry="3" fill="#e0e7ff" />

          {/* Cute Little Legs */}
          <path d="M52 97 C52 104, 50 106, 45 106" stroke="url(#spiderBlueSuit)" strokeWidth="6" strokeLinecap="round" />
          <path d="M68 97 C68 104, 70 106, 75 106" stroke="url(#spiderBlueSuit)" strokeWidth="6" strokeLinecap="round" />
          {/* Red Booties */}
          <ellipse cx="44" cy="106" rx="4" ry="2.5" fill="url(#spiderGlove)" />
          <ellipse cx="76" cy="106" rx="4" ry="2.5" fill="url(#spiderGlove)" />
        </svg>
      </div>
    </div>
  );
}
