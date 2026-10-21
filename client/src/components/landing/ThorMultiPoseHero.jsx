import React from 'react';

/**
 * ThorMultiPoseHero: Renders the 6 distinct anatomical poses for the cinematic sequence:
 * 1. 'peeking'    - Winged helmet, face, glowing eyes, and hammer peeking past the screen edge
 * 2. 'preparing'  - Leaning back, coiled tension, charging hammer with blue electricity
 * 3. 'flying'     - Supersonic horizontal flight facing left, hammer thrust forward
 * 4. 'descending' - 45-degree downward dive toward landing zone
 * 5. 'crouch'     - Authentic 3-point superhero knee landing with hammer touching earth
 * 6. 'standing'   - Pristine full-body standing hero pose on the left
 */
export default function ThorMultiPoseHero({
  pose = 'peeking',
  hammerCharging = false,
  hammerImpact = false,
  className = ''
}) {
  const getPoseSrc = () => {
    switch (pose) {
      case 'peeking':
        return '/assets/thor/thor_pose_peeking.png';
      case 'preparing':
        return '/assets/thor/thor_pose_preparing.png';
      case 'flying':
        return '/assets/thor/thor_pose_flying.png';
      case 'descending':
        return '/assets/thor/thor_pose_descending.png';
      case 'crouch':
        return '/assets/thor/thor_pose_crouch.png';
      case 'standing':
      default:
        return '/assets/thor/thor_hero_clean.png';
    }
  };

  const isFlight = pose === 'flying' || pose === 'descending';
  const isGrounded = pose === 'crouch' || pose === 'standing';

  return (
    <div className={`relative inline-block select-none ${className}`}>
      
      {/* Ground Contact Shadow beneath boots/crouch */}
      {isGrounded && (
        <div 
          className={`absolute -bottom-3 left-1/2 -translate-x-1/2 bg-black/80 rounded-full blur-xl pointer-events-none transition-all duration-300 ${
            pose === 'crouch' ? 'w-88 h-10' : 'w-72 h-8'
          }`} 
        />
      )}

      {/* Main Pose Image */}
      <div className="relative z-10 flex items-center justify-center">
        <img
          src={getPoseSrc()}
          alt={`Thor Superhero ${pose}`}
          className={`h-auto object-contain transition-all duration-150 ${
            pose === 'peeking' 
              ? 'w-56 sm:w-64 max-h-[320px]' 
              : pose === 'flying' 
              ? 'w-72 sm:w-96 md:w-[460px] max-h-[320px]' 
              : pose === 'descending'
              ? 'w-64 sm:w-80 md:w-[380px] max-h-[400px]'
              : pose === 'crouch'
              ? 'w-64 sm:w-76 md:w-[360px] max-h-[380px]'
              : 'w-60 sm:w-72 md:w-80 lg:w-[340px] max-h-[440px]' // Exactly ~60-65% section height
          }`}
          style={{
            filter: hammerImpact
              ? 'drop-shadow(0 0 35px rgba(56, 189, 248, 0.95)) drop-shadow(0 0 60px rgba(168, 85, 247, 0.8)) brightness(1.2)'
              : hammerCharging || isFlight
              ? 'drop-shadow(0 0 25px rgba(56, 189, 248, 0.7)) drop-shadow(0 15px 30px rgba(0,0,0,0.8))'
              : 'drop-shadow(0 15px 35px rgba(0,0,0,0.85)) drop-shadow(0 0 20px rgba(168, 85, 247, 0.3))',
          }}
          draggable={false}
        />

        {/* =====================================================================
            GLOWING ELECTRIC COMIC EYES (Rendered during active phases)
            ===================================================================== */}
        {pose === 'standing' && (
          <div 
            className="absolute pointer-events-none -translate-x-1/2 -translate-y-1/2 z-20"
            style={{ left: '54.5%', top: '10.5%' }}
          >
            <div className="w-3.5 h-3.5 rounded-full bg-white shadow-[0_0_12px_#38bdf8,0_0_24px_#38bdf8,0_0_35px_#c084fc] animate-pulse" />
          </div>
        )}

        {pose === 'peeking' && (
          <div 
            className="absolute pointer-events-none -translate-x-1/2 -translate-y-1/2 z-20"
            style={{ left: '58%', top: '24%' }}
          >
            <div className="w-3 h-3 rounded-full bg-white shadow-[0_0_10px_#38bdf8,0_0_20px_#38bdf8] animate-pulse" />
          </div>
        )}

        {/* =====================================================================
            ELECTRIC BLUE CHARGE AURA & ARCS (During preparation & flight)
            ===================================================================== */}
        {(hammerCharging || hammerImpact || isFlight) && (
          <div className="absolute inset-0 pointer-events-none z-30">
            <svg className="w-full h-full overflow-visible">
              <defs>
                <filter id="lightningGlow" x="-30%" y="-30%" width="160%" height="160%">
                  <feGaussianBlur stdDeviation="3" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Crackling cyan lightning bolts */}
              <path
                d="M 30% 25% L 20% 15% L 26% 10% L 15% 5%"
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2.5"
                strokeLinecap="round"
                filter="url(#lightningGlow)"
                className="animate-pulse"
              />
              <path
                d="M 40% 30% L 50% 20% L 45% 12% L 55% 5%"
                fill="none"
                stroke="#c084fc"
                strokeWidth="2.2"
                strokeLinecap="round"
                filter="url(#lightningGlow)"
              />
              
              {/* Impact Spark Flash on landing */}
              {hammerImpact && (
                <g className="animate-ping">
                  <circle cx="50%" cy="85%" r="28" fill="rgba(56, 189, 248, 0.45)" />
                  <circle cx="50%" cy="85%" r="14" fill="#ffffff" />
                </g>
              )}
            </svg>
          </div>
        )}

      </div>

    </div>
  );
}
