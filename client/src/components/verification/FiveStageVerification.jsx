import { useState, useEffect } from 'react';
import {
  ArrowRight,
  Bell,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileText,
  Layers,
  LoaderCircle,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  XCircle,
} from 'lucide-react';
import Button from '../ui/Button';
import { api, ApiError } from '../../services/api';

const SAMPLE_RVPACK = `---TRANSCRIPT---
National AI Hackathon 2026 organized by IIT Bombay.
Registration fee is ₹500.
Application deadline is 15th December 2026.
Open to all engineering students.
Cash prize pool worth ₹5,00,000 and direct internship interviews.
---ON_SCREEN---
IIT Bombay AI Hackathon 2026
Apply online at https://iitb.ac.in/hackathon
Registration Fee: ₹500
---META---
author: IIT Bombay
title: IIT Bombay AI Hackathon 2026
category: hackathon
`;

const STAGE_PROGRESS_INFO = [
  { stage: 'Stage 1', label: 'Extracting structure, event metadata & organizer details...' },
  { stage: 'Stage 2', label: 'Decomposing extracted content into atomic verifiable claims...' },
  { stage: 'Stage 3', label: 'Searching official domains & filtering authoritative evidence...' },
  { stage: 'Stage 4', label: 'Evaluating factual claim verdicts against verified sources...' },
  { stage: 'Stage 5', label: 'Synthesizing final opportunity card & determining badge...' },
];

const getBadgeStyles = (badge) => {
  const norm = (badge || '').trim().toUpperCase();
  if (norm === 'OFFICIAL CORROBORATED') {
    return {
      badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-300',
      label: 'OFFICIAL CORROBORATED',
      isOfficial: true,
      cardTitle: 'Official Opportunity Card',
    };
  }
  if (norm === 'PARTIALLY SUPPORTED') {
    return {
      badgeClass: 'bg-amber-50 text-amber-900 border-amber-300',
      label: 'PARTIALLY SUPPORTED',
      isOfficial: false,
      cardTitle: 'Opportunity Card (Partially Supported)',
    };
  }
  if (norm === 'CONTRADICTED') {
    return {
      badgeClass: 'bg-rose-50 text-rose-800 border-rose-300',
      label: 'CONTRADICTED',
      isOfficial: false,
      cardTitle: 'Opportunity Card (Contradicted Claims)',
    };
  }
  return {
    badgeClass: 'bg-slate-100 text-slate-700 border-slate-300',
    label: badge || 'UNVERIFIED / INSUFFICIENT EVIDENCE',
    isOfficial: false,
    cardTitle: 'Opportunity Card (Unverified)',
  };
};

export default function FiveStageVerification() {
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingProgressIndex, setLoadingProgressIndex] = useState(0);
  const [error, setError] = useState('');
  const [activeRun, setActiveRun] = useState(null);
  const [connectingReminder, setConnectingReminder] = useState(false);
  const [reminderConfirmedDate, setReminderConfirmedDate] = useState('');
  const [reminderMessage, setReminderMessage] = useState('');
  const [showDatePrompt, setShowDatePrompt] = useState(false);

  useEffect(() => {
    if (!isLoading) return;
    const interval = setInterval(() => {
      setLoadingProgressIndex((prev) => (prev < STAGE_PROGRESS_INFO.length - 1 ? prev + 1 : prev));
    }, 1500);
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleLoadSample = () => {
    setContent(SAMPLE_RVPACK);
    setError('');
  };

  const handleVerify = async (e) => {
    if (e) e.preventDefault();
    if (!content.trim()) {
      setError('Please provide .rvpack text containing TRANSCRIPT, ON_SCREEN, and META sections.');
      return;
    }

    setError('');
    setIsLoading(true);
    setReminderMessage('');
    setShowDatePrompt(false);

    try {
      const res = await api.submitRVPack(content.trim());
      setActiveRun(res);
    } catch (err) {
      if (err?.status === 504 || (err?.message && err.message.toLowerCase().includes('timeout'))) {
        setError('Verification timed out contacting external search/AI provider. Partial stage results may be saved; you can resume this run.');
      } else if (err?.status === 503) {
        setError('External AI or search provider temporarily unavailable. Please retry in a few moments.');
      } else {
        setError(err instanceof ApiError ? err.message : 'Verification pipeline failed.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResume = async () => {
    if (!activeRun?.id) return;
    setIsLoading(true);
    setError('');
    try {
      const res = await api.resumeVerificationRun(activeRun.id);
      setActiveRun(res);
    } catch (err) {
      if (err?.status === 504 || (err?.message && err.message.toLowerCase().includes('timeout'))) {
        setError('Resume attempt timed out. You can retry resuming.');
      } else {
        setError(err instanceof ApiError ? err.message : 'Could not resume verification run.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnectReminder = async (explicitDate = null) => {
    if (!activeRun?.id) return;
    setConnectingReminder(true);
    setError('');

    try {
      const payload = {
        label: `Deadline: ${activeRun.card?.title || 'Opportunity'}`,
        event_date: explicitDate || reminderConfirmedDate || undefined,
      };
      const res = await api.connectVaultReminder(activeRun.id, payload);
      setReminderMessage(res.message || 'Deadline reminder connected to Vault!');
      setShowDatePrompt(false);
      // Refresh run to show connected state
      const updated = await api.getVerificationRun(activeRun.id);
      setActiveRun(updated);
    } catch (err) {
      if (err?.code === 'ambiguous_deadline_year' || (err?.message && err.message.includes('ambiguous'))) {
        setShowDatePrompt(true);
        setError('Application deadline year is ambiguous in the announcement. Please specify the date below.');
      } else {
        setError(err instanceof ApiError ? err.message : 'Could not connect reminder.');
      }
    } finally {
      setConnectingReminder(false);
    }
  };

  const getStagePayload = (stageName) => {
    const stg = activeRun?.stages?.find((s) => s.stage_name === stageName);
    return stg?.payload || null;
  };

  const extracted = getStagePayload('extracted');
  const claims = getStagePayload('claims');
  const evidence = getStagePayload('evidence');
  const verdict = getStagePayload('verdict');
  const card = activeRun?.card || getStagePayload('card');

  const STAGES = [
    { key: 'extracted', name: '1. Extracted', icon: FileText },
    { key: 'claims', name: '2. Claims', icon: Layers },
    { key: 'evidence', name: '3. Evidence', icon: Search },
    { key: 'verdict', name: '4. Verdict', icon: ShieldCheck },
    { key: 'card', name: '5. Card', icon: Sparkles },
  ];

  return (
    <div className="space-y-8">
      {/* Input Form */}
      <div className="p-5 sm:p-7 rounded-2xl border-2 border-dashed border-[#E3D4F8] bg-[#FBF7FD]/70 hover:border-[#8B5CF6]/50 transition-colors space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <label className="text-[11px] font-bold uppercase tracking-widest text-[#776A83] ml-1 block">
            .RVPACK CONTENT (TRANSCRIPT, ON_SCREEN, META)
          </label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleLoadSample}
              className="text-xs font-bold text-[#8B5CF6] hover:text-[#6D28D9] bg-[#F0E8FF] px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
            >
              Load Sample .rvpack
            </button>
            {content && (
              <button
                type="button"
                onClick={() => { setContent(''); setActiveRun(null); setError(''); }}
                className="text-xs font-medium text-[#776A83] hover:text-red-500 transition-colors cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <textarea
          rows={7}
          placeholder="---TRANSCRIPT---&#10;Paste reel audio transcript...&#10;---ON_SCREEN---&#10;Key on-screen text and links...&#10;---META---&#10;author: Organizer name&#10;"
          value={content}
          disabled={isLoading}
          onChange={(e) => { setContent(e.target.value); setError(''); }}
          className="w-full p-4 font-mono text-xs sm:text-sm bg-white border border-[#E3D4F8] focus:border-[#8B5CF6] focus:ring-[#8B5CF6]/20 rounded-2xl text-[#261B33] placeholder:text-[#776A83]/40 focus:outline-none focus:ring-2 transition-all shadow-2xs"
        />

        {error && (
          <div className="flex items-center gap-2 text-red-500 text-sm font-medium ml-1">
            <XCircle size={15} />
            <span>{error}</span>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
          <Button
            type="button"
            disabled={isLoading || !content.trim()}
            onClick={handleVerify}
            className="w-full sm:w-auto px-8 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold py-3.5 rounded-xl text-base flex items-center justify-center gap-2 shadow-md shadow-[#8B5CF6]/25 hover:shadow-lg hover:shadow-[#8B5CF6]/35 transition-all cursor-pointer disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <LoaderCircle size={18} className="animate-spin" /> Executing 5-Stage Verification…
              </>
            ) : (
              <>
                VERIFY FIVE STAGES <ArrowRight size={18} strokeWidth={2.5} />
              </>
            )}
          </Button>

          {activeRun && activeRun.status !== 'completed' && (
            <button
              type="button"
              onClick={handleResume}
              disabled={isLoading}
              className="flex items-center gap-1.5 text-xs font-bold text-[#6D28D9] bg-[#F0E8FF] px-4 py-3 rounded-xl hover:bg-[#E3D4F8] transition-colors cursor-pointer"
            >
              <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
              Resume Incomplete Run
            </button>
          )}
        </div>

        {/* Real-time Stage Execution Progress Tracker */}
        {isLoading && (
          <div className="mt-4 p-4 rounded-xl bg-white border border-[#E3D4F8] shadow-sm space-y-2.5 animate-fadeIn">
            <div className="flex items-center justify-between text-xs font-bold text-[#6D28D9]">
              <span className="flex items-center gap-2">
                <LoaderCircle size={14} className="animate-spin text-[#8B5CF6]" />
                Verification Pipeline in Progress (bounded 8-20s timeouts)
              </span>
              <span className="text-[#776A83]">
                Stage {loadingProgressIndex + 1} of {STAGE_PROGRESS_INFO.length}
              </span>
            </div>
            <div className="w-full bg-[#F0E8FF] h-2 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] h-full transition-all duration-500 rounded-full"
                style={{ width: `${((loadingProgressIndex + 1) / STAGE_PROGRESS_INFO.length) * 100}%` }}
              />
            </div>
            <p className="text-xs text-[#776A83]">
              <strong className="text-[#261B33]">{STAGE_PROGRESS_INFO[loadingProgressIndex].stage}:</strong>{' '}
              {STAGE_PROGRESS_INFO[loadingProgressIndex].label}
            </p>
          </div>
        )}
      </div>

      {/* Five-Stage Workflow Output */}
      {activeRun && (
        <div className="space-y-6 animate-fadeIn">
          {/* Header & Status Indicator */}
          <div className="bg-white rounded-2xl p-4 sm:p-5 border border-[#E3D4F8] shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
                  Run ID: {activeRun.id.slice(0, 8)}...
                </span>
                <span className="text-xs font-bold uppercase tracking-wider text-[#776A83]">
                  Status: <strong className="text-[#6D28D9]">{activeRun.status}</strong>
                </span>
              </div>
              <p className="text-xs text-[#776A83] mt-1">
                Five-stage verification pipeline executed in strict sequence: Extracted → Claims → Evidence → Verdict → Card.
              </p>
            </div>

            {/* Stages Stepper */}
            <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto pb-1">
              {STAGES.map(({ key, name, icon: Icon }) => {
                const isCompleted = activeRun.completed_stages?.includes(key);
                return (
                  <div
                    key={key}
                    className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                      isCompleted
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-[#F0E8FF]/60 text-[#776A83] border border-[#E3D4F8]'
                    }`}
                  >
                    <Icon size={12} />
                    <span>{name}</span>
                    {isCompleted && <CheckCircle2 size={11} className="text-emerald-600 ml-0.5" />}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Registration Fee & Risk Signals Banner if detected */}
          {verdict?.has_scam_warning && (
            <div className="rounded-2xl border-2 border-amber-300 bg-amber-50/90 p-4 sm:p-5 text-amber-900 shadow-sm flex items-start gap-3.5">
              <ShieldAlert className="text-amber-600 shrink-0 mt-0.5" size={22} />
              <div className="space-y-1">
                <h4 className="font-bold text-sm text-amber-950 uppercase tracking-wide">
                  Registration Fee Caution
                </h4>
                {verdict.scam_warnings?.map((w, idx) => (
                  <p key={idx} className="text-xs sm:text-sm text-amber-800 leading-relaxed">
                    {w}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Grid of Stages 1 - 4 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Stage 1: Extracted */}
            {extracted && (
              <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-[#E3D4F8] pb-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#6D28D9] flex items-center gap-1.5">
                    <FileText size={14} /> Stage 1: Extracted
                  </span>
                  <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    Completed
                  </span>
                </div>
                <div className="space-y-1.5 text-xs text-[#261B33]">
                  <div><strong className="text-[#776A83]">Title:</strong> {extracted.title || 'N/A'}</div>
                  <div>
                    <strong className="text-[#776A83]">Organizer:</strong>{' '}
                    <span className={extracted.organizer === 'Unverified organizer' ? 'text-amber-700 font-bold' : ''}>
                      {extracted.organizer || 'Unverified organizer'}
                    </span>
                  </div>
                  {extracted.author && (
                    <div><strong className="text-[#776A83]">Account / Creator:</strong> {extracted.author}</div>
                  )}
                  <div><strong className="text-[#776A83]">Category:</strong> <span className="capitalize">{extracted.category}</span></div>
                  <div>
                    <strong className="text-[#776A83]">Deadline:</strong>{' '}
                    {extracted.deadline?.date ? (
                      <span className="font-bold text-emerald-700">{extracted.deadline.date}</span>
                    ) : extracted.deadline?.raw ? (
                      <span className="text-amber-600">{extracted.deadline.raw} (Year ambiguous)</span>
                    ) : (
                      'None'
                    )}
                  </div>
                  <div>
                    <strong className="text-[#776A83]">Fee:</strong>{' '}
                    {extracted.has_fee ? (
                      <span className="text-amber-700 font-bold">{extracted.fee_raw || 'Fee required'}</span>
                    ) : (
                      'Free / None specified'
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Stage 2: Claims */}
            {claims && (
              <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-[#E3D4F8] pb-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#6D28D9] flex items-center gap-1.5">
                    <Layers size={14} /> Stage 2: Decomposed Claims
                  </span>
                  <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    {claims.total_claims} Claims
                  </span>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {claims.claims?.map((c) => (
                    <div key={c.claim_id} className="text-xs p-2 rounded-lg bg-[#FBF7FD] border border-[#E3D4F8]/70">
                      <div className="flex items-center justify-between text-[10px] text-[#776A83] font-bold uppercase mb-1">
                        <span>{c.claim_id} · {c.claim_type}</span>
                        {c.is_fee_warning_claim && (
                          <span className="text-amber-600 bg-amber-50 px-1 rounded">Fee Warning</span>
                        )}
                      </div>
                      <p className="text-[#261B33]">{c.claim_text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Stage 3: Evidence */}
            {evidence && (
              <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-[#E3D4F8] pb-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#6D28D9] flex items-center gap-1.5">
                    <Search size={14} /> Stage 3: Evidence & Sources
                  </span>
                  <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                    {evidence.evidence_items?.length || 0} Sources
                  </span>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {evidence.evidence_items?.length > 0 ? (
                    evidence.evidence_items.map((ev) => (
                      <div key={ev.id} className="text-xs p-2.5 rounded-lg bg-[#FBF7FD] border border-[#E3D4F8]/70 space-y-1">
                        <div className="flex items-center justify-between">
                          <a
                            href={ev.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-bold text-[#6D28D9] hover:underline flex items-center gap-1 truncate max-w-[200px]"
                          >
                            {ev.title || ev.domain} <ExternalLink size={10} />
                          </a>
                          <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                            ev.domain_trust === 'high' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-700'
                          }`}>
                            {ev.domain_trust}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#776A83] line-clamp-2">{ev.snippet}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-[#776A83]">No external web queries required; validated from source text.</p>
                  )}
                </div>
              </div>
            )}

            {/* Stage 4: Verdict */}
            {verdict && (
              <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-[#E3D4F8] pb-2.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#6D28D9] flex items-center gap-1.5">
                    <ShieldCheck size={14} /> Stage 4: Claim Verdicts
                  </span>
                  <span className={`text-[10px] uppercase font-black px-2 py-0.5 rounded ${
                    verdict.overall_verdict === 'supported' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}>
                    {verdict.overall_verdict}
                  </span>
                </div>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {verdict.claim_verdicts?.map((cv) => (
                    <div key={cv.claim_id} className="text-xs p-2 rounded-lg bg-[#FBF7FD] border border-[#E3D4F8]/70">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-[#261B33]">{cv.claim_id}</span>
                        <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${
                          cv.verdict === 'supported' ? 'bg-emerald-50 text-emerald-700' :
                          cv.verdict === 'contradicted' ? 'bg-rose-50 text-rose-700' :
                          'bg-amber-50 text-amber-700'
                        }`}>
                          {cv.verdict}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#776A83]">{cv.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Stage 5: Opportunity Card */}
          {card && (() => {
            const badgeInfo = getBadgeStyles(card.badge);
            return (
              <div className="bg-gradient-to-br from-white to-[#FBF7FD] rounded-3xl p-6 sm:p-8 border-2 border-[#8B5CF6]/30 shadow-lg shadow-[#8B5CF6]/10 space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#E3D4F8] pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-[#8B5CF6] text-white">
                        Stage 5: {badgeInfo.cardTitle}
                      </span>
                      <span className={`text-xs font-bold uppercase tracking-wider border px-2.5 py-0.5 rounded-full ${badgeInfo.badgeClass}`}>
                        {badgeInfo.label}
                      </span>
                    </div>
                    <h3 className="text-xl sm:text-2xl font-display font-bold text-[#261B33] mt-2">
                      {card.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-[#776A83]">
                      Organized by <strong className="text-[#261B33]">{card.organizer}</strong> · Category: {card.category}
                    </p>
                    {!badgeInfo.isOfficial && (
                      <div className="mt-2 text-xs text-amber-800 bg-amber-50/80 border border-amber-200 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                        <ShieldAlert size={14} className="text-amber-600 shrink-0" />
                        <span>
                          Not officially corroborated by verified primary sources. Exercise due diligence before registering.
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="text-right">
                    <div className="text-xs text-[#776A83]">Deadline</div>
                    <div className="text-base font-black text-[#6D28D9]">
                      {card.deadline?.date || card.deadline?.raw || 'Not specified'}
                    </div>
                  </div>
                </div>

              {/* Card Action: Connect Vault Reminder */}
              <div className="p-4 rounded-2xl bg-[#F0E8FF]/60 border border-[#E3D4F8] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <div className="text-xs font-bold uppercase text-[#6D28D9] flex items-center gap-1.5">
                    <Bell size={14} /> Vault Deadline Reminder
                  </div>
                  <p className="text-xs text-[#776A83] mt-0.5">
                    {card.deadline?.vault_reminder_status === 'connected'
                      ? '✓ This deadline is actively connected to your Vault calendar reminders.'
                      : 'Save this deadline to your Vault calendar shelf to prevent missed applications.'}
                  </p>
                </div>

                {card.deadline?.vault_reminder_status === 'connected' ? (
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1.5 rounded-xl flex items-center gap-1.5">
                    <CheckCircle2 size={14} /> Reminder Connected
                  </span>
                ) : (
                  <Button
                    type="button"
                    onClick={() => handleConnectReminder()}
                    disabled={connectingReminder}
                    className="shrink-0 bg-[#6D28D9] hover:bg-[#5B21B6] text-white text-xs font-bold px-4 py-2.5 rounded-xl flex items-center gap-2 cursor-pointer"
                  >
                    {connectingReminder ? <LoaderCircle size={14} className="animate-spin" /> : <Calendar size={14} />}
                    Connect to Vault Reminder
                  </Button>
                )}
              </div>

              {/* Ambiguous Date Confirmation Prompt */}
              {showDatePrompt && (
                <div className="p-4 rounded-2xl bg-amber-50 border border-amber-300 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-amber-900">
                    <Clock size={15} className="text-amber-700" />
                    <span>Please Confirm Explicit Deadline Date (YYYY-MM-DD)</span>
                  </div>
                  <p className="text-xs text-amber-800">
                    The source announcement did not specify a year (e.g. &ldquo;15th November&rdquo;). ReelVault AI requires explicit confirmation rather than inventing a date.
                  </p>
                  <div className="flex items-center gap-3">
                    <input
                      type="date"
                      value={reminderConfirmedDate}
                      onChange={(e) => setReminderConfirmedDate(e.target.value)}
                      className="px-3 py-2 text-xs rounded-xl border border-amber-300 bg-white text-amber-950 font-bold focus:outline-none"
                    />
                    <button
                      type="button"
                      disabled={!reminderConfirmedDate || connectingReminder}
                      onClick={() => handleConnectReminder(reminderConfirmedDate)}
                      className="px-4 py-2 text-xs font-bold bg-amber-700 hover:bg-amber-800 text-white rounded-xl cursor-pointer disabled:opacity-50"
                    >
                      Confirm & Save Reminder
                    </button>
                  </div>
                </div>
              )}

              {reminderMessage && (
                <div className="flex items-center gap-2 text-emerald-700 text-xs font-bold bg-emerald-50 p-3 rounded-xl border border-emerald-200">
                  <CheckCircle2 size={16} />
                  <span>{reminderMessage}</span>
                </div>
              )}
            </div>
          );
        })()}
        </div>
      )}
    </div>
  );
}
