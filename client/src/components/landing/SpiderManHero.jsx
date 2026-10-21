import { forwardRef, useId } from 'react';

// Keep the source comic intact, with masked head and free-arm animation layers.
const SpiderManHero = forwardRef(function SpiderManHero(_, ref) {
  const id = useId().replace(/:/g, '');
  const bodyMask = id + '-body';
  const headClip = id + '-head';
  const armClip = id + '-arm';
  const frameClip = id + '-frame';
  const freeArm = 'M0 500 H225 L260 575 L250 700 H0 Z';
  const artwork = <image href="/assets/landing/spider-comic-reference.png" width="722" height="961" preserveAspectRatio="none"/>;
  return <g ref={ref} className="rv-spider-rig" aria-label="Comic Spider-Man with deeply folded, widely spread knees">
    <defs>
      <clipPath id={frameClip}><rect x="0" y="178" width="722" height="710"/></clipPath>
      <clipPath id={headClip}><ellipse cx="375" cy="794" rx="53" ry="74"/></clipPath>
      <clipPath id={armClip}><path d={freeArm}/></clipPath>
      <mask id={bodyMask} maskUnits="userSpaceOnUse" x="0" y="178" width="722" height="710" style={{ maskType: 'luminance' }}>
        <rect x="0" y="178" width="722" height="710" fill="white"/>
        <ellipse cx="375" cy="794" rx="53" ry="74" fill="black"/>
        <path d={freeArm} fill="black"/>
      </mask>
    </defs>
    <g data-comic-coordinates="true" transform="translate(-152 -191) scale(0.4)">
      <g clipPath={'url(#' + frameClip + ')'}>
        <g mask={'url(#' + bodyMask + ')'}>{artwork}</g>
        <g data-comic-joint="freeArm"><g clipPath={'url(#' + armClip + ')'}>{artwork}</g></g>
        <g data-comic-joint="head"><g clipPath={'url(#' + headClip + ')'}>{artwork}</g></g>
      </g>
    </g>
  </g>;
});
export default SpiderManHero;
