import React from 'react';

/**
 * CinematicThor: High-detail 2.5D cartoon thunder-warrior superhero mascot
 * Features metallic armor textures, winged helmet, glowing rune disks,
 * flowing cape, and magical hammer with crackling electric arcs.
 */
export default function CinematicThor({ 
  pose = 'landing', // 'flying' | 'landing' | 'idle'
  hammerImpact = false,
  className = '' 
}) {
  return (
    <div className={`relative select-none ${className}`}>
      
      {/* Ground shadow beneath hero */}
      <div 
        className={`absolute -bottom-4 left-1/2 -translate-x-1/2 w-48 h-8 bg-black/60 rounded-full blur-md transition-all duration-500 pointer-events-none ${
          pose === 'flying' ? 'opacity-20 scale-50' : 'opacity-80 scale-100'
        }`} 
      />

      {/* Main Vector Character Canvas */}
      <svg
        viewBox="0 0 280 280"
        className="w-56 h-56 sm:w-72 sm:h-72 md:w-80 md:h-80 overflow-visible drop-shadow-[0_15px_30px_rgba(0,0,0,0.8)]"
      >
        <defs>
          {/* Metallic Gradients */}
          <linearGradient id="chromeLight" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="35%" stopColor="#e2e8f0" />
            <stop offset="70%" stopColor="#94a3b8" />
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>

          <linearGradient id="chromeDark" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#64748b" />
            <stop offset="50%" stopColor="#334155" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>

          <linearGradient id="goldTrim" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fef08a" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#854d0e" />
          </linearGradient>

          {/* Skin Tones */}
          <radialGradient id="thorSkin" cx="45%" cy="40%" r="65%">
            <stop offset="0%" stopColor="#ffedd5" />
            <stop offset="75%" stopColor="#fed7aa" />
            <stop offset="100%" stopColor="#fb923c" />
          </radialGradient>

          {/* Flowing Crimson-Purple Cape Gradients */}
          <linearGradient id="capeGradient" x1="20%" y1="0%" x2="80%" y2="100%">
            <stop offset="0%" stopColor="#c026d3" />
            <stop offset="30%" stopColor="#9333ea" />
            <stop offset="70%" stopColor="#6b21a8" />
            <stop offset="100%" stopColor="#3b0764" />
          </linearGradient>

          <linearGradient id="capeShadow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#581c87" />
            <stop offset="100%" stopColor="#2e1065" />
          </linearGradient>

          {/* Hammer Metallic Stone & Glow */}
          <linearGradient id="hammerMetal" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f1f5f9" />
            <stop offset="30%" stopColor="#94a3b8" />
            <stop offset="70%" stopColor="#475569" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>

          <linearGradient id="hammerRuneGlow" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#38bdf8" />
            <stop offset="50%" stopColor="#c084fc" />
            <stop offset="100%" stopColor="#e879f9" />
          </linearGradient>

          {/* Hair Gradient */}
          <linearGradient id="blondeHair" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fef08a" />
            <stop offset="50%" stopColor="#facc15" />
            <stop offset="100%" stopColor="#ca8a04" />
          </linearGradient>

          {/* Glow Filters */}
          <filter id="electricGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="impactBurstFilter" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* =========================================================================
            LAYER 1: FLOWING CAPE (Back Layer)
            ========================================================================= */}
        <g id="thor-cape" className="transition-all duration-700">
          {/* Main Cape Back Body with deep rich folds */}
          <path
            d="M80 120 C50 150, 25 210, 40 245 C75 235, 95 210, 105 180 C95 160, 90 135, 80 120 Z"
            fill="url(#capeShadow)"
          />
          <path
            d="M95 125 C65 160, 45 220, 65 255 C100 245, 125 215, 130 175 C120 155, 110 135, 95 125 Z"
            fill="url(#capeGradient)"
          />
          {/* Cape Wing Edge Flares */}
          <path
            d="M65 255 C50 250, 30 230, 25 215 C45 210, 60 235, 65 255 Z"
            fill="#a21caf"
          />
        </g>

        {/* =========================================================================
            LAYER 2: LEGS & HEROIC LANDING POSTURE
            One knee bent, one foot braced firmly on the ground
            ========================================================================= */}
        <g id="thor-legs">
          {/* Left Braced Leg */}
          <path
            d="M100 175 L85 215 L70 240 L105 240 L115 215 L120 180 Z"
            fill="url(#chromeDark)"
            stroke="#1e293b"
            strokeWidth="1.5"
          />
          {/* Left Knee Guard */}
          <path
            d="M82 210 L105 205 L110 225 L88 230 Z"
            fill="url(#chromeLight)"
            stroke="#334155"
            strokeWidth="1.5"
          />
          {/* Left Armored Boot */}
          <path
            d="M68 238 L105 238 C105 248, 85 252, 60 252 C55 245, 60 240, 68 238 Z"
            fill="url(#chromeDark)"
            stroke="#0f172a"
            strokeWidth="1.5"
          />

          {/* Right Leg (Dropped in impact stance) */}
          <path
            d="M140 175 L155 210 L175 245 L150 248 L135 220 L130 180 Z"
            fill="url(#chromeDark)"
            stroke="#1e293b"
            strokeWidth="1.5"
          />
          {/* Right Knee Guard */}
          <path
            d="M148 205 L172 210 L165 230 L142 225 Z"
            fill="url(#chromeLight)"
            stroke="#334155"
            strokeWidth="1.5"
          />
          {/* Right Armored Boot */}
          <path
            d="M145 245 L180 245 C185 252, 160 254, 140 252 Z"
            fill="url(#chromeDark)"
            stroke="#0f172a"
            strokeWidth="1.5"
          />
        </g>

        {/* =========================================================================
            LAYER 3: ASGARDIAN ARMORED TORSO
            Cuirass with silver and dark plates + 4 glowing rune disks
            ========================================================================= */}
        <g id="thor-torso">
          {/* Armored Chest Base */}
          <path
            d="M95 125 L160 125 L150 185 L105 185 Z"
            fill="url(#chromeDark)"
            stroke="#0f172a"
            strokeWidth="2"
          />
          {/* Chest Center Plate with Bevel */}
          <path
            d="M108 125 L148 125 L142 178 L114 178 Z"
            fill="#1e293b"
            stroke="#475569"
            strokeWidth="1.5"
          />

          {/* 4 Asgardian Circular Rune Disks with Electric Purple Inlays */}
          {/* Top Left Disk */}
          <circle cx="114" cy="142" r="8" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1" />
          <circle cx="114" cy="142" r="5" fill="#a855f7" filter="url(#electricGlow)" />
          <circle cx="114" cy="142" r="2.5" fill="#f5d0fe" />

          {/* Top Right Disk */}
          <circle cx="142" cy="142" r="8" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1" />
          <circle cx="142" cy="142" r="5" fill="#a855f7" filter="url(#electricGlow)" />
          <circle cx="142" cy="142" r="2.5" fill="#f5d0fe" />

          {/* Bottom Left Disk */}
          <circle cx="116" cy="164" r="7.5" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1" />
          <circle cx="116" cy="164" r="4.5" fill="#c084fc" filter="url(#electricGlow)" />
          <circle cx="116" cy="164" r="2" fill="#ffffff" />

          {/* Bottom Right Disk */}
          <circle cx="140" cy="164" r="7.5" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1" />
          <circle cx="140" cy="164" r="4.5" fill="#c084fc" filter="url(#electricGlow)" />
          <circle cx="140" cy="164" r="2" fill="#ffffff" />

          {/* Armored Belt */}
          <path
            d="M102 180 L153 180 L150 192 L105 192 Z"
            fill="url(#goldTrim)"
            stroke="#713f12"
            strokeWidth="1.2"
          />
          {/* Belt Buckle */}
          <rect x="122" y="178" width="12" height="16" rx="2" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1" />
        </g>

        {/* =========================================================================
            LAYER 4: LEFT ARM (Braced on knee or holding pose)
            ========================================================================= */}
        <g id="thor-left-arm">
          {/* Shoulder Pauldron */}
          <ellipse cx="88" cy="132" rx="12" ry="10" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1.5" />
          {/* Arm Sleeve */}
          <path d="M85 138 L75 165 L90 172 L96 142 Z" fill="#334155" stroke="#1e293b" strokeWidth="1" />
          {/* Forearm Bracer */}
          <path d="M75 165 L68 188 L85 192 L90 172 Z" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1.5" />
          {/* Clenched Fist resting on knee */}
          <circle cx="76" cy="195" r="7.5" fill="url(#thorSkin)" stroke="#ea580c" strokeWidth="1" />
        </g>

        {/* =========================================================================
            LAYER 5: CHIBI HEAD, HAIR & METALLIC WINGED HELMET
            ========================================================================= */}
        <g id="thor-head">
          {/* Golden Locks Behind Helmet */}
          <path
            d="M92 78 C70 95, 78 125, 88 135 C95 125, 94 95, 98 85 Z"
            fill="url(#blondeHair)"
            stroke="#ca8a04"
            strokeWidth="1"
          />
          <path
            d="M162 78 C184 95, 176 125, 166 135 C159 125, 160 95, 156 85 Z"
            fill="url(#blondeHair)"
            stroke="#ca8a04"
            strokeWidth="1"
          />

          {/* Face Base */}
          <ellipse cx="127" cy="85" rx="30" ry="28" fill="url(#thorSkin)" />

          {/* Heroic Eyebrows */}
          <path d="M108 72 L122 75" stroke="#a16207" strokeWidth="3" strokeLinecap="round" />
          <path d="M146 75 L132 75" stroke="#a16207" strokeWidth="3" strokeLinecap="round" />

          {/* Determined Comic Eyes */}
          {/* Left Eye */}
          <ellipse cx="116" cy="82" rx="5" ry="7.5" fill="#0f172a" />
          <circle cx="114.5" cy="79.5" r="2.2" fill="#ffffff" />
          <circle cx="117.5" cy="85.5" r="1.1" fill="#93c5fd" />

          {/* Right Eye */}
          <ellipse cx="138" cy="82" rx="5" ry="7.5" fill="#0f172a" />
          <circle cx="136.5" cy="79.5" r="2.2" fill="#ffffff" />
          <circle cx="139.5" cy="85.5" r="1.1" fill="#93c5fd" />

          {/* Nose & Determined Hero Smirk */}
          <path d="M127 82 L125 90 L129 90" stroke="#f97316" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <path d="M120 98 Q127 103 134 98" fill="none" stroke="#9a3412" strokeWidth="2.2" strokeLinecap="round" />

          {/* Metallic Winged Helmet Dome */}
          <path
            d="M97 74 C97 45, 157 45, 157 74 C148 66, 106 66, 97 74 Z"
            fill="url(#chromeLight)"
            stroke="#334155"
            strokeWidth="2"
          />
          {/* Helmet Nose/Brow Guard */}
          <path
            d="M96 72 L158 72 L150 78 L131 78 L127 84 L123 78 L104 78 Z"
            fill="url(#chromeDark)"
            stroke="#1e293b"
            strokeWidth="1.2"
          />

          {/* Left Wing on Helmet */}
          <path
            d="M98 68 C80 50, 72 20, 68 10 C80 25, 92 45, 96 68 Z"
            fill="url(#chromeLight)"
            stroke="#475569"
            strokeWidth="1.5"
            filter="drop-shadow(-2px 4px 6px rgba(0,0,0,0.5))"
          />
          <path d="M78 28 C85 40, 90 52, 94 65" stroke="#ffffff" strokeWidth="1" fill="none" />

          {/* Right Wing on Helmet */}
          <path
            d="M156 68 C174 50, 182 20, 186 10 C174 25, 162 45, 158 68 Z"
            fill="url(#chromeLight)"
            stroke="#475569"
            strokeWidth="1.5"
            filter="drop-shadow(2px 4px 6px rgba(0,0,0,0.5))"
          />
          <path d="M176 28 C169 40, 164 52, 160 65" stroke="#ffffff" strokeWidth="1" fill="none" />
        </g>

        {/* =========================================================================
            LAYER 6: RIGHT ARM & THE MAGICAL MJOLNIR HAMMER
            Striking down onto the ground with crackling lightning!
            ========================================================================= */}
        <g id="thor-hammer-arm">
          {/* Right Shoulder Pauldron */}
          <ellipse cx="166" cy="132" rx="12" ry="10" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1.5" />
          
          {/* Arm extending downward toward the ground impact */}
          <path d="M168 138 L195 185 L182 192 L158 145 Z" fill="#334155" stroke="#1e293b" strokeWidth="1" />
          {/* Forearm Bracer */}
          <path d="M190 178 L208 215 L192 222 L178 185 Z" fill="url(#chromeLight)" stroke="#334155" strokeWidth="1.5" />
          
          {/* Right Clenched Fist gripping hammer */}
          <circle cx="204" cy="220" r="8" fill="url(#thorSkin)" stroke="#ea580c" strokeWidth="1" />

          {/* Hammer Handle */}
          <rect
            x="200"
            y="190"
            width="8"
            height="55"
            rx="3"
            fill="#78350f"
            stroke="#451a03"
            strokeWidth="1"
            transform="rotate(18 204 220)"
          />
          {/* Handle Grip Leather Straps */}
          <line x1="200" y1="205" x2="208" y2="207" stroke="#d97706" strokeWidth="1.5" transform="rotate(18 204 220)" />
          <line x1="200" y1="215" x2="208" y2="217" stroke="#d97706" strokeWidth="1.5" transform="rotate(18 204 220)" />
          <line x1="200" y1="225" x2="208" y2="227" stroke="#d97706" strokeWidth="1.5" transform="rotate(18 204 220)" />

          {/* MAGICAL HAMMER HEAD (Impacting the ground) */}
          <g transform="rotate(18 204 245)">
            {/* Main Hammer Beveled Block */}
            <rect
              x="180"
              y="232"
              width="50"
              height="30"
              rx="5"
              fill="url(#hammerMetal)"
              stroke="#e2e8f0"
              strokeWidth="2"
              filter="drop-shadow(0 0 15px rgba(168,85,247,0.7))"
            />
            {/* Hammer Side Bevel Chamfers */}
            <path d="M180 236 L187 232 L187 262 L180 258 Z" fill="#334155" />
            <path d="M230 236 L223 232 L223 262 L230 258 Z" fill="#64748b" />
            
            {/* Glowing Runes on Hammer Face */}
            <path
              d="M196 247 L214 247 M205 238 L205 256 M199 242 L211 252 M199 252 L211 242"
              stroke="url(#hammerRuneGlow)"
              strokeWidth="2"
              strokeLinecap="round"
              filter="url(#electricGlow)"
            />
          </g>

          {/* =========================================================================
              CRACKLING ELECTRIC ARCS & SPARKS AROUND HAMMER HEAD
              ========================================================================= */}
          <g id="hammer-lightning-arcs" className="animate-pulse">
            {/* Bright Electric Arcs wrapping the hammer */}
            <path
              d="M185 240 L170 230 L178 245 L160 250"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#electricGlow)"
            />
            <path
              d="M235 245 L252 235 L244 250 L260 255"
              fill="none"
              stroke="#e879f9"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#electricGlow)"
            />
            <path
              d="M210 220 L220 205 L215 225 L230 215"
              fill="none"
              stroke="#c084fc"
              strokeWidth="2"
              strokeLinecap="round"
            />

            {/* Intense Ground Sparks on Hammer Impact */}
            {hammerImpact && (
              <g filter="url(#impactBurstFilter)">
                <circle cx="212" cy="256" r="16" fill="#e879f9" opacity="0.8" className="animate-ping" />
                <circle cx="212" cy="256" r="8" fill="#ffffff" />
                <path d="M212 256 L180 270 M212 256 L245 270 M212 256 L212 278" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" />
              </g>
            )}
          </g>
        </g>
      </svg>
    </div>
  );
}
