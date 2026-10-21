import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  EyeOff,
  FileSearch,
  Link as LinkIcon,
  LoaderCircle,
  ScanText,
  SearchCheck,
  Sparkles,
  XCircle,
} from 'lucide-react';
import Button from '../components/ui/Button';
import { api, ApiError } from '../services/api';
import { useLanguage } from '../preferences/LanguageContext';
const ANALYSIS_STEPS = [
  { label: 'Extracting reel content', detail: 'Reading the public post and caption.', Icon: FileSearch },
  { label: 'Transcribing the reel', detail: 'Turning spoken content into searchable text.', Icon: ScanText },
  { label: 'Analysing key details', detail: 'Finding dates, links and useful topics.', Icon: Sparkles },
  { label: 'Verifying sources', detail: 'Checking related sources and official links.', Icon: SearchCheck },
];

function AnalysisProgress({ step, complete }) {
  return (
    <div className="rounded-2xl border border-[#E3D4F8] bg-gradient-to-br from-[#F9ECF5]/70 to-[#F0E8FF]/80 p-5 sm:p-6 shadow-sm" role="status" aria-live="polite">
      <div className="flex items-start gap-3.5">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] text-white shadow-sm shadow-[#8B5CF6]/25">
          {complete ? <CheckCircle2 size={21} /> : <LoaderCircle size={21} className="animate-spin text-white" />}
        </div>
        <div>
          <p className="text-sm font-bold text-[#6D28D9]">{complete ? 'Your reel is ready' : 'Preparing your reel vault entry'}</p>
          <p className="mt-1 text-sm text-[#776A83]">{complete ? 'Opening your saved reel…' : 'This can take a moment for longer videos.'}</p>
        </div>
      </div>
      <ol className="mt-5 space-y-3">
        {ANALYSIS_STEPS.map(({ label, detail, Icon }, index) => {
          const isDone = complete || index < step;
          const isActive = !complete && index === step;
          return <li key={label} className={`flex items-center gap-3 rounded-xl px-3.5 py-2.5 transition-all ${isActive ? 'bg-white shadow-xs border border-[#E3D4F8]/80' : ''}`}>
            <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-all ${isDone ? 'bg-[#8B5CF6] text-white' : isActive ? 'bg-[#F0E8FF] text-[#6D28D9] ring-2 ring-[#8B5CF6]/40' : 'bg-white/80 text-[#776A83]/40'}`}>
              {isDone ? <CheckCircle2 size={15} /> : isActive ? <LoaderCircle size={15} className="animate-spin text-[#8B5CF6]" /> : <Icon size={15} />}
            </span>
            <span><span className={`block text-sm font-bold ${isActive || isDone ? 'text-[#261B33]' : 'text-[#776A83]/50'}`}>{label}</span>{isActive && <span className="block text-xs text-[#776A83]">{detail}</span>}</span>
          </li>;
        })}
      </ol>
    </div>
  );
}

export default function Home() {
  const [inputValue, setInputValue] = useState('');
  const [urlError, setUrlError] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [recentReels, setRecentReels] = useState([]);
  const [sortOrder, setSortOrder] = useState('newest');
  const [dateFilter, setDateFilter] = useState('all');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [hiddenRecentIds, setHiddenRecentIds] = useState(() => new Set());
  const navigate = useNavigate();
  const { language } = useLanguage();

  const loadRecent = () => {
    api.listReels()
      .then((reels) => setRecentReels(reels.slice(0, 5)))
      .catch(() => setRecentReels([]));
  };

  useEffect(() => {
    loadRecent();
  }, []);

  useEffect(() => {
    if (!isSubmitting) return undefined;
    const progressTimer = window.setInterval(() => {
      setAnalysisStep((current) => Math.min(current + 1, 2));
    }, 1500);
    return () => window.clearInterval(progressTimer);
  }, [isSubmitting]);

  const validateUrl = (url) => {
    if (!url.trim()) return 'empty';
    if (!/^https?:\/\//i.test(url)) return 'invalid';
    if (!/instagram\.com|youtube\.com|youtu\.be|tiktok\.com/i.test(url)) return 'unsupported';
    return '';
  };

  const visibleRecentReels = recentReels
    .filter((reel) => !hiddenRecentIds.has(reel.reel_id))
    .filter((reel) => {
      if (dateFilter === 'all') return true;
      const createdAt = new Date(reel.created_at);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (dateFilter === 'today') return createdAt >= today;
      if (dateFilter === '7days') return createdAt >= new Date(today.getTime() - 6 * 86400000);
      if (dateFilter === '30days') return createdAt >= new Date(today.getTime() - 29 * 86400000);
      if (dateFilter === 'custom-start' && customStart) return createdAt >= new Date(`${customStart}T00:00:00`);
      if (dateFilter === 'custom-end' && customEnd) return createdAt <= new Date(`${customEnd}T23:59:59`);
      if (dateFilter === 'custom-range' && customStart && customEnd) {
        return createdAt >= new Date(`${customStart}T00:00:00`) && createdAt <= new Date(`${customEnd}T23:59:59`);
      }
      return true;
    })
    .sort((a, b) => {
      const difference = new Date(a.created_at) - new Date(b.created_at);
      return sortOrder === 'oldest' ? difference : -difference;
    });

  const hideFromRecent = (reelId) => {
    setHiddenRecentIds((current) => new Set([...current, reelId]));
  };

  const transcriptionState = (reel) => {
    const status = reel.transcript_status || (reel.transcript ? 'verified' : reel.caption ? 'ambiguous' : 'unavailable');
    if (status === 'verified') return { label: 'Transcript verified', Icon: CheckCircle2, className: 'text-emerald-600', title: 'A transcript was found.' };
    if (status === 'ambiguous') return { label: 'Transcript ambiguous', Icon: CheckCircle2, className: 'text-amber-500', title: 'Only partial or caption text was available.' };
    return { label: 'Cannot transcribe this type of content', Icon: XCircle, className: 'text-red-500', title: 'This type of content cannot be transcribed.' };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const error = validateUrl(inputValue);
    setUrlError(error);
    if (error) return;
    setSubmitError('');
    setAnalysisStep(0);
    setAnalysisComplete(false);
    setIsSubmitting(true);
    try {
      await api.saveReel(inputValue.trim());
      setAnalysisComplete(true);
      setInputValue('');
      loadRecent();
      navigate('/vault');
    } catch (requestError) {
      setSubmitError(requestError instanceof ApiError ? requestError.message : 'Unable to save this reel.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full space-y-12 pb-8">
      <header className="max-w-2xl">
        <h1 className="font-display text-4xl sm:text-5xl uppercase tracking-wide text-[#261B33] mb-3">
          SAVE A REEL
        </h1>
        <p className="text-[#776A83] font-medium text-lg">
          Paste a public Instagram, YouTube, or TikTok link. We fetch the title and transcript and store it in your vault.
        </p>
      </header>

      <section className="w-full">
        <div className="bg-white rounded-3xl p-6 sm:p-8 lg:p-10 shadow-[0_8px_30px_-6px_rgba(139,92,246,0.06)] border border-[#E3D4F8]">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="p-5 sm:p-7 rounded-2xl border-2 border-dashed border-[#E3D4F8] bg-[#FBF7FD]/70 hover:border-[#8B5CF6]/50 transition-colors space-y-4">
              <label className="text-[11px] font-bold uppercase tracking-widest text-[#776A83] ml-1 block">
                REEL / SHORT LINK
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                  <LinkIcon size={18} className="text-[#8B5CF6]" />
                </div>
                <input
                  type="url"
                  placeholder="https://www.instagram.com/reel/..."
                  value={inputValue}
                  disabled={isSubmitting}
                  onChange={(e) => { setInputValue(e.target.value); setUrlError(''); setSubmitError(''); }}
                  className={`w-full pl-12 pr-5 py-4 bg-white border ${urlError && urlError !== 'empty' ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20' : 'border-[#E3D4F8] focus:border-[#8B5CF6] focus:ring-[#8B5CF6]/20'} rounded-2xl text-[#261B33] placeholder:text-[#776A83]/40 focus:outline-none focus:ring-2 transition-all text-base font-medium shadow-2xs`}
                />
              </div>
              {urlError === 'invalid' && (
                <div className="flex items-center gap-1.5 text-red-500 text-sm font-medium mt-2 ml-1">
                  <AlertCircle size={14} /> Enter a valid URL.
                </div>
              )}
              {urlError === 'unsupported' && (
                <div className="flex items-center gap-1.5 text-amber-600 text-sm font-medium mt-2 ml-1">
                  <AlertCircle size={14} /> This link isn't supported yet.
                </div>
              )}
              {submitError && (
                <div className="flex items-center gap-1.5 text-red-500 text-sm font-medium mt-2 ml-1">
                  <AlertCircle size={14} /> {submitError}
                </div>
              )}
            </div>

            {isSubmitting ? (
              <AnalysisProgress step={analysisStep} complete={analysisComplete} />
            ) : (
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold py-4 rounded-xl text-base sm:text-lg flex items-center justify-center gap-2 shadow-md shadow-[#8B5CF6]/25 hover:shadow-lg hover:shadow-[#8B5CF6]/35 transition-all cursor-pointer"
              >
                SAVE & ANALYSE REEL <ArrowRight size={20} strokeWidth={2.5} />
              </Button>
            )}
          </form>
        </div>
      </section>

      <section className="pt-8 border-t border-[#E3D4F8]/80">
        <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-sm font-display uppercase tracking-widest text-[#776A83]">Recent</h2>
            <p className="text-sm text-[#776A83] mt-1">Your latest saved reels, sorted by date.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="sr-only" htmlFor="recent-date-filter">Filter recent reels by date</label>
            <div className="relative">
              <CalendarDays size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8B5CF6]" aria-hidden="true" />
              <select id="recent-date-filter" value={dateFilter} onChange={(event) => setDateFilter(event.target.value)} className="appearance-none rounded-xl border border-[#E3D4F8] bg-white py-2.5 pl-9 pr-8 text-sm font-semibold text-[#261B33] focus:border-[#8B5CF6] focus:outline-none focus:ring-1 focus:ring-[#8B5CF6]">
                <option value="all">All dates</option>
                <option value="today">Today</option>
                <option value="7days">Last 7 days</option>
                <option value="30days">Last 30 days</option>
                <option value="custom-range">Custom range</option>
              </select>
            </div>
            <label className="sr-only" htmlFor="recent-sort">Sort recent reels</label>
            <select id="recent-sort" value={sortOrder} onChange={(event) => setSortOrder(event.target.value)} className="rounded-xl border border-[#E3D4F8] bg-white px-3 py-2.5 text-sm font-semibold text-[#261B33] focus:border-[#8B5CF6] focus:outline-none focus:ring-1 focus:ring-[#8B5CF6]">
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
            </select>
          </div>
        </div>
        {dateFilter === 'custom-range' && (
          <div className="flex flex-wrap gap-3 mb-6 rounded-2xl bg-[#F0E8FF]/40 border border-[#E3D4F8] p-4">
            <label className="flex flex-col gap-1 text-xs font-bold uppercase tracking-wider text-[#776A83]">From<input type="date" value={customStart} onChange={(event) => setCustomStart(event.target.value)} className="rounded-lg border border-[#E3D4F8] bg-white px-3 py-2 text-sm font-medium text-[#261B33] normal-case tracking-normal focus:outline-none focus:border-[#8B5CF6]" /></label>
            <label className="flex flex-col gap-1 text-xs font-bold uppercase tracking-wider text-[#776A83]">To<input type="date" value={customEnd} onChange={(event) => setCustomEnd(event.target.value)} className="rounded-lg border border-[#E3D4F8] bg-white px-3 py-2 text-sm font-medium text-[#261B33] normal-case tracking-normal focus:outline-none focus:border-[#8B5CF6]" /></label>
          </div>
        )}
        {recentReels.length === 0 ? (
          <p className="text-[#776A83] font-medium">No reels yet. Paste a link above to get started.</p>
        ) : visibleRecentReels.length === 0 ? (
          <p className="rounded-2xl border-2 border-dashed border-[#E3D4F8] bg-[#FBF7FD]/70 p-6 text-[#776A83] font-medium">No recent reels match this date filter.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 lg:gap-6">
            {visibleRecentReels.map((reel) => {
              const verification = transcriptionState(reel);
              const VerificationIcon = verification.Icon;
              return (
                <article key={reel.reel_id} className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-[0_2px_12px_-4px_rgba(139,92,246,0.04)] hover:shadow-md hover:border-[#8B5CF6]/40 hover:-translate-y-0.5 transition-all">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#776A83]">{reel.platform}</span>
                    <div className="flex items-center gap-2">
                      <div className={`flex items-center gap-1 text-[10px] font-bold ${verification.className}`} title={verification.title}>
                        <VerificationIcon size={15} aria-hidden="true" />
                        <span className="sr-only">{verification.label}</span>
                        <span className="text-[#776A83]/70 font-semibold ml-1">{new Date(reel.created_at).toLocaleDateString()}</span>
                      </div>
                      <button type="button" onClick={() => hideFromRecent(reel.reel_id)} className="rounded-lg p-1.5 text-[#776A83] hover:bg-[#F0E8FF] hover:text-[#261B33] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6] transition-colors" aria-label={`Remove ${reel.title} from recent reels`} title="Remove from recent">
                        <EyeOff size={15} aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                  <button type="button" onClick={() => navigate('/vault')} className="w-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[#8B5CF6] focus-visible:ring-offset-2 rounded-lg">
                    <h3 className="text-[#261B33] font-bold text-base mb-2 line-clamp-2 leading-snug">{reel.title}</h3>
                    {reel.transcript_status === 'verified' && reel.analysis?.summary ? (
                      <><p className="text-[10px] font-bold uppercase tracking-widest text-[#8B5CF6] mb-1">{language === 'english' ? 'Reel summary' : 'Original transcript'}</p><p className="text-sm text-[#776A83] line-clamp-3 leading-6">{language === 'english' ? reel.analysis.summary : reel.transcript}</p></>
                    ) : <p className="text-sm text-[#776A83] line-clamp-3">{language === 'native' ? (reel.transcript || reel.caption || 'This type of content cannot be transcribed.') : 'English transcription is unavailable for this reel.'}</p>}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
