import { useLayoutEffect, useRef, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import gsap from 'gsap';
import { ReelContent, PhoneFrame, OpportunityCard } from './DemoReel';
import { demoReels } from './demoReels';
import useReducedMotion from './useReducedMotion';
export default function Hero3DPhone() {
 const stage = useRef(null), timeline = useRef(null), float = useRef(null);
 const reducedMotion = useReducedMotion();
 const [paused, setPaused] = useState(false);
 useLayoutEffect(() => {
  const spread = () => Math.max(30, Math.min(114, (stage.current.clientWidth - 180) / 2 - 10));
  const ctx = gsap.context(() => {
   if (reducedMotion) { gsap.set('.rv-hero-card', { opacity: 1, scale: 1, x: (i) => [-1,1,-.25][i] * spread(), y: (i) => [-140,5,122][i] }); return; }
   const tl = gsap.timeline({ repeat: -1, repeatDelay: 0.6, repeatRefresh: true }); timeline.current = tl;
   tl.set('.rv-hero-card', { opacity: 0, scale: 0.55, x: 0, y: 0, z: -80, rotation: 0, rotationY: 0 })
    .set('.rv-hero-scan', { opacity: 0 }).set('.rv-reel-track', { yPercent: 0, opacity: 1 })
    .to('.rv-reel-track', { yPercent: -100, duration: 1.05, ease: 'power3.inOut' }, 1.8)
    .to('.rv-reel-track', { yPercent: -200, duration: 1.05, ease: 'power3.inOut' }, 4.1)
    .to('.rv-hero-scan', { opacity: 1, duration: 0.25 }, 6)
    .fromTo('.rv-hero-scan i', { y: 0 }, { y: 430, duration: 1.6, ease: 'sine.inOut' }, 6)
    .to('.rv-hero-scan', { opacity: 0, duration: 0.4 }, 7.6)
    .to('.rv-hero-card', { opacity: 1, scale: 1, z: 25, rotationY: (i) => [-6,6,-2][i], x: (i) => [-1,1,-.25][i] * spread(), y: (i) => [-145,8,122][i], rotation: (i) => [-7,7,-3][i], duration: 1.15, stagger: 0.18, ease: 'power3.out' }, 7.7)
    .to('.rv-hero-card', { opacity: 0, scale: 0.8, z: -60, rotationY: 0, x: 0, y: 0, rotation: 0, duration: 0.75, stagger: 0.08, ease: 'power2.inOut' }, 12)
    .to('.rv-reel-track', { opacity: 0, duration: 0.4 }, 12.65).set('.rv-reel-track', { yPercent: 0 }, 13.1).to('.rv-reel-track', { opacity: 1, duration: 0.55 }, 13.1);
   float.current = gsap.to('.rv-phone-float', { y: -9, rotation: 1, duration: 3.4, repeat: -1, yoyo: true, ease: 'sine.inOut' });
  }, stage);
  let width = stage.current.clientWidth;
  const observer = new ResizeObserver(() => { const next = stage.current.clientWidth; if (Math.abs(next - width) > 30) { width = next; const wasPaused = timeline.current?.paused(); timeline.current?.invalidate().restart().paused(wasPaused); } });
  observer.observe(stage.current);
  return () => { observer.disconnect(); ctx.revert(); timeline.current = null; float.current = null; };
 }, [reducedMotion]);
 useLayoutEffect(() => { timeline.current?.paused(paused); float.current?.paused(paused); }, [paused, reducedMotion]);
 return <div ref={stage} className={'rv-hero-stage ' + (paused ? 'is-paused' : '')} aria-label="Automatic demonstration of reels becoming opportunity cards"><div className="rv-stage-halo"/><span className="rv-scene-label rv-eyebrow">01 / Discover the possibility</span><div className="rv-phone-float"><PhoneFrame><div className="rv-reel-viewport"><div className="rv-reel-track">{demoReels.map(reel => <ReelContent key={reel.theme} reel={reel} paused={paused}/>)}</div></div><div className="rv-hero-scan"><i/><span>✧ AI extracting opportunity</span></div></PhoneFrame></div><div className="rv-hero-cards" aria-hidden="true">{demoReels.map((reel,i) => <div key={reel.theme} className={'rv-hero-card rv-hero-card-' + i}><OpportunityCard reel={reel} compact/></div>)}</div><div className="rv-scene-caption"><span><i/> Fictional reels. Real possibilities.</span>{!reducedMotion && <button type="button" onClick={() => setPaused(p => !p)} aria-label={paused ? 'Play hero animation' : 'Pause hero animation'}>{paused ? <Play size={14}/> : <Pause size={14}/>}</button>}</div></div>;
}
