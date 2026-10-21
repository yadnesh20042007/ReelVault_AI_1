import React from 'react';

/**
 * ThorFullBody: Complete, handcrafted full-body comic superhero thunder warrior.
 * Includes full head, hair, glowing eyes, muscular torso, flowing cape,
 * and complete legs with armored knee plates and boots in both Flight and Landing poses.
 */
export default function ThorFullBody({
  pose = 'landing', // 'flying' | 'landing'
  direction = 'right', // 'right' | 'left'
  hammerImpact = false,
  className = ''
}) {
  const isFlipped = direction === 'left';

  if (pose === 'flying') {
    return (
      <div 
        className={`relative inline-block select-none ${className}`}
        style={{ transform: isFlipped ? 'scaleX(-1)' : 'none' }}
      >
        <svg
          viewBox="0 0 520 220"
          className="w-72 sm:w-96 md:w-[480px] lg:w-[560px] h-auto overflow-visible drop-shadow-[0_10px_25px_rgba(0,0,0,0.8)]"
        >
          <defs>
            {/* Gradients */}
            <linearGradient id="flyHair" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fef08a" />
              <stop offset="50%" stopColor="#eab308" />
              <stop offset="100%" stopColor="#a16207" />
            </linearGradient>

            <linearGradient id="flySkin" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#fed7aa" />
              <stop offset="60%" stopColor="#fdba74" />
              <stop offset="100%" stopColor="#f97316" />
            </linearGradient>

            <linearGradient id="flyCape" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#dc2626" />
              <stop offset="50%" stopColor="#991b1b" />
              <stop offset="100%" stopColor="#450a0a" />
            </linearGradient>

            <linearGradient id="flyArmor" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#475569" />
              <stop offset="50%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>

            <linearGradient id="flyHammer" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f8fafc" />
              <stop offset="40%" stopColor="#94a3b8" />
              <stop offset="100%" stopColor="#334155" />
            </linearGradient>

            <filter id="flyGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* ===================================================================
              1. BILLOWING CAPE (Full trailing back layer)
              =================================================================== */}
          <path
            d="M 280 85 C 220 50, 130 30, 20 60 C 70 95, 120 120, 20 160 C 140 140, 210 130, 280 115 Z"
            fill="url(#flyCape)"
            opacity="0.9"
          />
          <path
            d="M 270 95 C 190 70, 100 65, 10 90 C 80 115, 130 135, 40 175 C 160 150, 215 135, 270 120 Z"
            fill="#b91c1c"
            opacity="0.75"
          />

          {/* ===================================================================
              2. FULL LEGS & ARMORED BOOTS (Trailing horizontally behind body)
              =================================================================== */}
          {/* Back Leg (Right Leg) */}
          <g opacity="0.85">
            <path
              d="M 220 115 L 140 128 L 90 136 L 60 138 L 85 152 L 145 142 L 210 128 Z"
              fill="url(#flyArmor)"
              stroke="#0f172a"
              strokeWidth="1.5"
            />
            {/* Back Armored Boot */}
            <path
              d="M 90 136 L 50 138 L 45 146 L 85 152 Z"
              fill="#1e293b"
              stroke="#334155"
              strokeWidth="1.2"
            />
          </g>

          {/* Front Leg (Left Leg) */}
          <g>
            {/* Thigh */}
            <path
              d="M 240 110 L 165 120 L 175 138 L 230 130 Z"
              fill="url(#flyArmor)"
              stroke="#0f172a"
              strokeWidth="1.5"
            />
            {/* Knee Armor Guard */}
            <path
              d="M 165 118 L 148 122 L 152 136 L 172 134 Z"
              fill="#64748b"
              stroke="#1e293b"
              strokeWidth="1.2"
            />
            {/* Shin Greave */}
            <path
              d="M 150 122 L 95 130 L 100 144 L 154 135 Z"
              fill="url(#flyArmor)"
              stroke="#0f172a"
              strokeWidth="1.5"
            />
            {/* Front Armored Boot with Steel Toe */}
            <path
              d="M 95 130 L 62 134 C 55 138, 55 145, 65 147 L 100 144 Z"
              fill="#0f172a"
              stroke="#475569"
              strokeWidth="1.5"
            />
            <path d="M 64 135 L 75 145" stroke="#94a3b8" strokeWidth="1.5" />
          </g>

          {/* ===================================================================
              3. ARMORED TORSO & WAIST BELT
              =================================================================== */}
          {/* Waist Belt & Gold Buckle */}
          <path
            d="M 230 102 L 260 100 L 255 118 L 225 120 Z"
            fill="#eab308"
            stroke="#713f12"
            strokeWidth="1.2"
          />
          {/* Armored Chest Cuirass */}
          <path
            d="M 255 92 L 325 82 L 315 115 L 250 120 Z"
            fill="url(#flyArmor)"
            stroke="#0f172a"
            strokeWidth="2"
          />
          {/* Glowing Asgardian Rune Disks on chest */}
          <circle cx="280" cy="94" r="5" fill="#a855f7" filter="url(#flyGlow)" />
          <circle cx="280" cy="94" r="2.5" fill="#ffffff" />
          <circle cx="305" cy="90" r="5" fill="#38bdf8" filter="url(#flyGlow)" />
          <circle cx="305" cy="90" r="2.5" fill="#ffffff" />
          <circle cx="275" cy="110" r="4.5" fill="#a855f7" filter="url(#flyGlow)" />
          <circle cx="298" cy="106" r="4.5" fill="#38bdf8" filter="url(#flyGlow)" />

          {/* ===================================================================
              4. HEAD, SHORT BLONDE HAIR, BEARD & GLOWING EYES
              =================================================================== */}
          {/* Neck */}
          <path d="M 315 85 L 335 82 L 332 98 L 312 98 Z" fill="url(#flySkin)" />
          
          {/* Head & Jaw with Beard */}
          <path
            d="M 325 75 C 330 65, 355 65, 360 76 C 365 85, 355 98, 342 98 C 330 98, 322 88, 325 75 Z"
            fill="url(#flySkin)"
          />
          {/* Beard stubble texture */}
          <path
            d="M 334 84 C 338 96, 354 96, 358 84 L 354 96 C 346 100, 338 98, 334 94 Z"
            fill="#a16207"
            opacity="0.85"
          />

          {/* Short swept-back blonde comic hair */}
          <path
            d="M 324 75 C 310 65, 335 50, 355 52 C 370 54, 372 65, 362 74 C 352 62, 332 66, 324 75 Z"
            fill="url(#flyHair)"
            stroke="#854d0e"
            strokeWidth="1.2"
          />
          <path d="M 336 62 C 348 58, 360 62, 366 68" stroke="#fef08a" strokeWidth="1.5" fill="none" />

          {/* Determined mouth */}
          <path d="M 344 90 Q 350 92 355 89" stroke="#7c2d12" strokeWidth="1.5" fill="none" />

          {/* Glowing electric eyes */}
          <ellipse cx="350" cy="78" rx="3.5" ry="4" fill="#ffffff" filter="url(#flyGlow)" />
          <circle cx="350" cy="78" r="1.8" fill="#38bdf8" />
          <ellipse cx="338" cy="79" rx="3" ry="3.5" fill="#ffffff" filter="url(#flyGlow)" />
          <circle cx="338" cy="79" r="1.5" fill="#38bdf8" />

          {/* ===================================================================
              5. MUSCULAR ARMS & WARHAMMER MJOLNIR (Thrust forward)
              =================================================================== */}
          {/* Left Arm (Tucked near chest for aerodynamics) */}
          <path
            d="M 300 100 L 325 112 L 315 125 L 290 112 Z"
            fill="url(#flySkin)"
            stroke="#c2410c"
            strokeWidth="1"
          />
          <path d="M 315 110 L 325 118" stroke="#1e293b" strokeWidth="3" />

          {/* Right Arm (Extended forward gripping Mjolnir) */}
          {/* Bicep */}
          <path
            d="M 320 85 L 365 78 L 368 95 L 322 100 Z"
            fill="url(#flySkin)"
            stroke="#c2410c"
            strokeWidth="1.2"
          />
          {/* Forearm with Leather Bracer */}
          <path
            d="M 365 78 L 410 72 L 414 88 L 368 95 Z"
            fill="url(#flySkin)"
            stroke="#c2410c"
            strokeWidth="1.2"
          />
          <rect x="380" y="74" width="22" height="18" rx="2" fill="#1e293b" stroke="#475569" strokeWidth="1" transform="rotate(-7 391 83)" />

          {/* Clenched Fist Gripping Hammer */}
          <circle cx="414" cy="80" r="7" fill="url(#flySkin)" stroke="#9a3412" strokeWidth="1" />

          {/* Mjolnir Handle */}
          <rect
            x="410"
            y="55"
            width="8"
            height="50"
            rx="3"
            fill="#78350f"
            stroke="#451a03"
            strokeWidth="1"
            transform="rotate(-20 414 80)"
          />
          {/* Handle Grip Straps */}
          <line x1="410" y1="70" x2="418" y2="72" stroke="#d97706" strokeWidth="1.5" transform="rotate(-20 414 80)" />
          <line x1="410" y1="80" x2="418" y2="82" stroke="#d97706" strokeWidth="1.5" transform="rotate(-20 414 80)" />

          {/* Mjolnir Heavy Hammer Head */}
          <g transform="rotate(-20 414 55)">
            <rect
              x="392"
              y="32"
              width="45"
              height="28"
              rx="4"
              fill="url(#flyHammer)"
              stroke="#e2e8f0"
              strokeWidth="2"
              filter="drop-shadow(0 0 15px rgba(56,189,248,0.8))"
            />
            {/* Bevel details */}
            <path d="M 392 36 L 398 32 L 398 60 L 392 56 Z" fill="#334155" />
            <path d="M 437 36 L 431 32 L 431 60 L 437 56 Z" fill="#64748b" />
            {/* Carved Runes */}
            <path
              d="M 406 46 L 424 46 M 415 38 L 415 54 M 410 42 L 420 50"
              stroke="#38bdf8"
              strokeWidth="2"
              strokeLinecap="round"
              filter="url(#flyGlow)"
            />
          </g>

          {/* Electric Arcs wrapping Mjolnir */}
          <g className="animate-pulse">
            <path
              d="M 430 45 L 455 35 L 445 52 L 475 42"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#flyGlow)"
            />
            <path
              d="M 410 25 L 425 10 L 435 28 L 450 15"
              fill="none"
              stroke="#e879f9"
              strokeWidth="2.2"
              strokeLinecap="round"
              filter="url(#flyGlow)"
            />
          </g>
        </svg>
      </div>
    );
  }

  // =========================================================================
  // POSE: LANDING & HEROIC GROUND IMPACT (FULL BODY)
  // One knee down, one leg braced wide, hammer struck into the earth!
  // =========================================================================
  return (
    <div 
      className={`relative inline-block select-none ${className}`}
      style={{ transform: isFlipped ? 'scaleX(-1)' : 'none' }}
    >
      {/* Ground Contact Shadow */}
      <div 
        className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-80 h-10 bg-black/80 rounded-full blur-xl pointer-events-none"
      />

      <svg
        viewBox="0 0 420 440"
        className="w-72 sm:w-88 md:w-[420px] lg:w-[460px] h-auto overflow-visible drop-shadow-[0_15px_35px_rgba(0,0,0,0.9)]"
      >
        <defs>
          <linearGradient id="landHair" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fef08a" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#854d0e" />
          </linearGradient>

          <linearGradient id="landSkin" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffedd5" />
            <stop offset="60%" stopColor="#fed7aa" />
            <stop offset="100%" stopColor="#f97316" />
          </linearGradient>

          <linearGradient id="landCape" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#dc2626" />
            <stop offset="50%" stopColor="#991b1b" />
            <stop offset="100%" stopColor="#450a0a" />
          </linearGradient>

          <linearGradient id="landArmorDark" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#475569" />
            <stop offset="50%" stopColor="#1e293b" />
            <stop offset="100%" stopColor="#090d16" />
          </linearGradient>

          <linearGradient id="landArmorLight" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="50%" stopColor="#cbd5e1" />
            <stop offset="100%" stopColor="#64748b" />
          </linearGradient>

          <linearGradient id="landHammer" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="35%" stopColor="#94a3b8" />
            <stop offset="80%" stopColor="#475569" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>

          <filter id="landGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <filter id="impactBurstFilter" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* ===================================================================
            LAYER 1: FLOWING CAPE (Back Layer draped over shoulders & ground)
            =================================================================== */}
        <g id="land-cape">
          {/* Main Cape Body */}
          <path
            d="M 125 150 C 70 190, 40 280, 55 380 C 110 370, 160 340, 185 270 C 160 210, 150 170, 125 150 Z"
            fill="url(#landCape)"
          />
          <path
            d="M 140 155 C 85 205, 65 295, 80 385 C 130 375, 175 345, 195 285 C 175 225, 160 175, 140 155 Z"
            fill="#b91c1c"
            opacity="0.8"
          />
          {/* Right Cape Fold behind torso */}
          <path
            d="M 230 155 C 275 210, 290 280, 275 350 C 255 330, 245 280, 235 240 Z"
            fill="#7f1d1d"
          />
        </g>

        {/* ===================================================================
            LAYER 2: FULL LEGS & ARMORED BOOTS (Three-Point Landing Stance)
            One knee dropped onto the ground, one foot planted wide!
            =================================================================== */}
        <g id="land-legs">
          {/* LEFT LEG: Braced Wide with Knee Bent at ~90 degrees */}
          {/* Left Thigh */}
          <path
            d="M 160 230 L 115 275 L 140 290 L 180 245 Z"
            fill="url(#landArmorDark)"
            stroke="#0f172a"
            strokeWidth="1.8"
          />
          {/* Left Knee Armor Guard */}
          <path
            d="M 108 270 L 138 265 L 145 295 L 115 298 Z"
            fill="url(#landArmorLight)"
            stroke="#1e293b"
            strokeWidth="1.5"
          />
          {/* Left Shin / Greave */}
          <path
            d="M 115 295 L 110 365 L 140 365 L 142 295 Z"
            fill="url(#landArmorDark)"
            stroke="#0f172a"
            strokeWidth="1.8"
          />
          {/* Left Boot: Planted Flat on Earth with Steel Toe Cap */}
          <path
            d="M 100 365 L 145 365 C 145 378, 120 382, 85 382 C 78 375, 85 368, 100 365 Z"
            fill="#0f172a"
            stroke="#475569"
            strokeWidth="2"
          />
          <path d="M 88 370 L 115 370" stroke="url(#landArmorLight)" strokeWidth="1.5" />

          {/* RIGHT LEG: Dropped Knee Contact Landing Stance */}
          {/* Right Thigh angling down to ground */}
          <path
            d="M 215 235 L 245 300 L 220 315 L 195 250 Z"
            fill="url(#landArmorDark)"
            stroke="#0f172a"
            strokeWidth="1.8"
          />
          {/* Right Knee Guard (Impacting near the floor) */}
          <path
            d="M 235 295 L 265 305 L 255 330 L 225 320 Z"
            fill="url(#landArmorLight)"
            stroke="#1e293b"
            strokeWidth="1.5"
          />
          {/* Right Shin angled backward along the ground */}
          <path
            d="M 240 320 L 275 355 L 255 370 L 220 330 Z"
            fill="url(#landArmorDark)"
            stroke="#0f172a"
            strokeWidth="1.8"
          />
          {/* Right Armored Boot tucked back on ground */}
          <path
            d="M 265 355 L 305 372 C 300 380, 275 380, 250 372 Z"
            fill="#0f172a"
            stroke="#475569"
            strokeWidth="2"
          />
        </g>

        {/* ===================================================================
            LAYER 3: ASGARDIAN ARMORED TORSO & BELT
            =================================================================== */}
        <g id="land-torso">
          {/* Armored Chest Base */}
          <path
            d="M 145 155 L 235 155 L 225 240 L 160 240 Z"
            fill="url(#landArmorDark)"
            stroke="#0f172a"
            strokeWidth="2.2"
          />
          {/* Center Rib Plate */}
          <path
            d="M 165 155 L 215 155 L 208 230 L 172 230 Z"
            fill="#1e293b"
            stroke="#475569"
            strokeWidth="1.5"
          />

          {/* 4 Asgardian Circular Rune Disks with Electric Cyan & Purple Glow */}
          {/* Top-Left */}
          <circle cx="170" cy="175" r="9" fill="url(#landArmorLight)" stroke="#1e293b" strokeWidth="1.2" />
          <circle cx="170" cy="175" r="5.5" fill="#a855f7" filter="url(#landGlow)" />
          <circle cx="170" cy="175" r="2.5" fill="#ffffff" />
          
          {/* Top-Right */}
          <circle cx="210" cy="175" r="9" fill="url(#landArmorLight)" stroke="#1e293b" strokeWidth="1.2" />
          <circle cx="210" cy="175" r="5.5" fill="#38bdf8" filter="url(#landGlow)" />
          <circle cx="210" cy="175" r="2.5" fill="#ffffff" />

          {/* Bottom-Left */}
          <circle cx="173" cy="208" r="8" fill="url(#landArmorLight)" stroke="#1e293b" strokeWidth="1.2" />
          <circle cx="173" cy="208" r="4.5" fill="#a855f7" filter="url(#landGlow)" />
          <circle cx="173" cy="208" r="2" fill="#ffffff" />

          {/* Bottom-Right */}
          <circle cx="207" cy="208" r="8" fill="url(#landArmorLight)" stroke="#1e293b" strokeWidth="1.2" />
          <circle cx="207" cy="208" r="4.5" fill="#38bdf8" filter="url(#landGlow)" />
          <circle cx="207" cy="208" r="2" fill="#ffffff" />

          {/* Heavy Warrior Belt & Gold Buckle */}
          <path
            d="M 155 235 L 230 235 L 225 252 L 160 252 Z"
            fill="#eab308"
            stroke="#854d0e"
            strokeWidth="1.5"
          />
          <rect x="183" y="233" width="18" height="21" rx="2" fill="url(#landArmorLight)" stroke="#334155" strokeWidth="1.2" />
        </g>

        {/* ===================================================================
            LAYER 4: LEFT ARM (Braced on knee for superhero landing balance)
            =================================================================== */}
        <g id="land-left-arm">
          {/* Left Shoulder Pauldron */}
          <ellipse cx="138" cy="162" rx="16" ry="12" fill="url(#landArmorLight)" stroke="#334155" strokeWidth="1.8" />
          {/* Muscular Upper Arm */}
          <path d="M 134 170 L 115 210 L 138 218 L 152 176 Z" fill="url(#landSkin)" stroke="#c2410c" strokeWidth="1.2" />
          {/* Forearm with Leather Wrap / Bracer */}
          <path d="M 115 210 L 108 248 L 132 252 L 138 218 Z" fill="url(#landSkin)" stroke="#c2410c" strokeWidth="1.2" />
          <rect x="110" y="218" width="24" height="22" rx="2" fill="#1e293b" stroke="#475569" strokeWidth="1" />
          {/* Fist Clenched firmly on Left Knee */}
          <circle cx="118" cy="260" r="10" fill="url(#landSkin)" stroke="#9a3412" strokeWidth="1.2" />
        </g>

        {/* ===================================================================
            LAYER 5: HEAD, SHORT BLONDE HAIR, BEARD & GLOWING ELECTRIC EYES
            (Exact comic warrior aesthetic: short hair, beard stubble, glowing eyes)
            =================================================================== */}
        <g id="land-head">
          {/* Neck */}
          <path d="M 175 132 L 205 132 L 202 155 L 178 155 Z" fill="url(#landSkin)" />
          {/* Chin & Jaw with Beard */}
          <ellipse cx="190" cy="115" rx="26" ry="24" fill="url(#landSkin)" />
          {/* Stubble Beard */}
          <path
            d="M 170 114 C 174 135, 206 135, 210 114 C 206 138, 174 138, 170 114 Z"
            fill="#a16207"
            opacity="0.85"
          />

          {/* Short Swept-Back Blonde Comic Hair */}
          <path
            d="M 166 102 C 158 84, 170 65, 190 64 C 210 65, 222 84, 214 102 C 208 86, 172 86, 166 102 Z"
            fill="url(#landHair)"
            stroke="#854d0e"
            strokeWidth="1.5"
          />
          <path d="M 176 80 C 188 74, 196 74, 204 80" stroke="#fef08a" strokeWidth="1.5" fill="none" />

          {/* Heroic Eyebrows */}
          <path d="M 174 102 L 186 104" stroke="#854d0e" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M 206 102 L 194 104" stroke="#854d0e" strokeWidth="2.5" strokeLinecap="round" />

          {/* Glowing Electric Comic Eyes with Cyan Core & Violet Aura */}
          {/* Left Eye */}
          <ellipse cx="180" cy="110" rx="4.5" ry="5.5" fill="#ffffff" filter="url(#landGlow)" />
          <circle cx="180" cy="110" r="2.2" fill="#38bdf8" />
          {/* Right Eye */}
          <ellipse cx="200" cy="110" rx="4.5" ry="5.5" fill="#ffffff" filter="url(#landGlow)" />
          <circle cx="200" cy="110" r="2.2" fill="#38bdf8" />

          {/* Nose & Determined Fierce Battle Smirk */}
          <path d="M 190 108 L 188 118 L 192 118" stroke="#ea580c" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          <path d="M 182 126 Q 190 131 198 126" stroke="#7c2d12" strokeWidth="2" fill="none" strokeLinecap="round" />
        </g>

        {/* ===================================================================
            LAYER 6: RIGHT ARM & MAGICAL WARHAMMER MJOLNIR
            Striking forcefully into the ground!
            =================================================================== */}
        <g id="land-hammer-arm">
          {/* Right Shoulder Pauldron */}
          <ellipse cx="242" cy="162" rx="16" ry="12" fill="url(#landArmorLight)" stroke="#334155" strokeWidth="1.8" />
          
          {/* Muscular Upper Arm angling down to strike */}
          <path d="M 244 170 L 276 215 L 258 225 L 230 180 Z" fill="url(#landSkin)" stroke="#c2410c" strokeWidth="1.2" />
          
          {/* Forearm with Armored Bracer */}
          <path d="M 276 215 L 305 265 L 285 275 L 258 225 Z" fill="url(#landSkin)" stroke="#c2410c" strokeWidth="1.2" />
          <rect x="270" y="225" width="26" height="26" rx="3" fill="url(#landArmorLight)" stroke="#334155" strokeWidth="1.2" transform="rotate(25 283 238)" />

          {/* Clenched Right Fist gripping Mjolnir handle */}
          <circle cx="304" cy="275" r="10" fill="url(#landSkin)" stroke="#9a3412" strokeWidth="1.2" />

          {/* Hammer Handle (Angled down into the earth) */}
          <rect
            x="298"
            y="240"
            width="10"
            height="85"
            rx="4"
            fill="#78350f"
            stroke="#451a03"
            strokeWidth="1.2"
            transform="rotate(18 304 275)"
          />
          {/* Leather Grip Straps */}
          <line x1="298" y1="260" x2="308" y2="263" stroke="#d97706" strokeWidth="1.8" transform="rotate(18 304 275)" />
          <line x1="298" y1="275" x2="308" y2="278" stroke="#d97706" strokeWidth="1.8" transform="rotate(18 304 275)" />
          <line x1="298" y1="290" x2="308" y2="293" stroke="#d97706" strokeWidth="1.8" transform="rotate(18 304 275)" />

          {/* =================================================================
              MJOLNIR HAMMER HEAD (Planted Firmly on the Ground)
              ================================================================= */}
          <g transform="rotate(18 304 330)">
            {/* Main Hammer Head Block */}
            <rect
              x="270"
              y="320"
              width="68"
              height="44"
              rx="6"
              fill="url(#landHammer)"
              stroke="#f8fafc"
              strokeWidth="2.5"
              filter="drop-shadow(0 0 20px rgba(56,189,248,0.9))"
            />
            {/* Beveled Chamfers */}
            <path d="M 270 326 L 278 320 L 278 364 L 270 358 Z" fill="#334155" />
            <path d="M 338 326 L 330 320 L 330 364 L 338 358 Z" fill="#64748b" />

            {/* Glowing Carved Norse Runes */}
            <path
              d="M 292 342 L 316 342 M 304 330 L 304 354 M 296 335 L 312 349 M 296 349 L 312 335"
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeLinecap="round"
              filter="url(#landGlow)"
            />
          </g>

          {/* =================================================================
              CRACKLING ELECTRIC ARCS & SPARKS AROUND HAMMER HEAD
              ================================================================= */}
          <g id="land-lightning-arcs" className="animate-pulse">
            {/* Cyan electric arc 1 */}
            <path
              d="M 275 320 L 250 305 L 260 325 L 235 330"
              fill="none"
              stroke="#38bdf8"
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#landGlow)"
            />
            {/* Purple electric arc 2 */}
            <path
              d="M 345 330 L 370 315 L 360 335 L 385 340"
              fill="none"
              stroke="#e879f9"
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#landGlow)"
            />
            {/* Upward crackle 3 */}
            <path
              d="M 310 295 L 325 275 L 318 300 L 335 285"
              fill="none"
              stroke="#c084fc"
              strokeWidth="2.5"
              strokeLinecap="round"
            />

            {/* Hammer Impact Burst Sparks */}
            {hammerImpact && (
              <g filter="url(#impactBurstFilter)">
                <circle cx="310" cy="355" r="22" fill="#e879f9" opacity="0.8" className="animate-ping" />
                <circle cx="310" cy="355" r="10" fill="#ffffff" />
                <path d="M 310 355 L 260 375 M 310 355 L 360 375 M 310 355 L 310 395" stroke="#38bdf8" strokeWidth="3" strokeLinecap="round" />
              </g>
            )}
          </g>
        </g>
      </svg>
    </div>
  );
}
