import { Heart, Bookmark, Music2, ScanLine, ShieldCheck } from 'lucide-react';
export function ReelContent({ reel, paused = false }) {
 return <div className={'rv-reel rv-reel-' + reel.theme + (paused ? ' is-paused' : '')}>
  <div className="rv-reel-art" aria-hidden="true"><div className="rv-orb"/><div className="rv-orbit rv-orbit-one"/><div className="rv-orbit rv-orbit-two"/><div className="rv-art-grid"/><span className="rv-art-type">{reel.theme === 'nova' ? 'CREATE' : reel.theme === 'orbit' ? 'EXPLORE' : 'BECOME'}</span></div>
  <div className="rv-reel-top"><span className="rv-avatar">{reel.theme.slice(0,1).toUpperCase()}</span><span>{reel.handle}<small>Fictional creator</small></span><span className="rv-demo-tag">DEMO</span></div>
  <div className="rv-reel-story"><span className="rv-eyebrow">{reel.category} / 2026</span><h3>{reel.title}</h3><span className="rv-reel-reward">{reel.reward}</span></div>
  <div className="rv-reel-bottom"><p>{reel.detail}</p><small><Music2 size={12}/> Original audio · Demo reel</small></div>
  <div className="rv-reel-rail" aria-hidden="true"><Heart size={19}/><small>12.8k</small><Bookmark size={19}/></div><div className="rv-playback"><i/></div>
 </div>;
}
export function PhoneFrame({ children, scanning = false, className = '' }) {
 return <div className={'rv-phone ' + className}><div className="rv-phone-buttons"/><div className="rv-phone-screen"><div className="rv-island"/><div className="rv-statusbar"><span>9:41</span><span>▥ &nbsp; 5G ▰</span></div>{children}{scanning && <div className="rv-scan" aria-hidden="true"><i/><span><ScanLine size={13}/> Analysing reel...</span></div>}<div className="rv-home-indicator"/></div></div>;
}
export function OpportunityCard({ reel, compact = false }) {
 return <article className={'rv-opportunity ' + (compact ? 'rv-compact' : '')}><div className="rv-card-top"><span className="rv-eyebrow">{reel.category}</span><span className="rv-demo-tag">DEMO</span></div><div className="rv-card-symbol" aria-hidden="true">✧</div><h3>{reel.name}</h3><p className="rv-card-benefit">{reel.reward}</p><dl><div><dt>Deadline</dt><dd>{reel.deadline}</dd></div>{!compact && <><div><dt>Who can apply</dt><dd>{reel.eligibility}</dd></div><div><dt>What you get</dt><dd>{reel.benefit}</dd></div></>}</dl><div className="rv-verification"><ShieldCheck size={15}/><span>Demo verification<small>Simulated check · No real opportunity verified</small></span></div></article>;
}
