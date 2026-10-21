import { useEffect, useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  User,
  Mail,
  ShieldCheck,
  LogOut,
  Bookmark,
  Sparkles,
  Copy,
  Check,
  ExternalLink,
  Calendar,
  Clock,
  ArrowRight,
  Layers,
  Settings,
  Shield,
  Activity,
  CheckCircle2,
  RefreshCw,
  Edit2,
  Bell,
  X,
  Save,
  Briefcase,
  Globe
} from 'lucide-react';
import { useAuth } from '../auth/useAuth';
import { useProfile } from '../auth/useProfile';
import { api } from '../services/api';

export default function Profile() {
  const navigate = useNavigate();
  const { user, session, signOut } = useAuth();

  const [copiedId, setCopiedId] = useState(false);
  const [reels, setReels] = useState([]);
  const [loadingReels, setLoadingReels] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  // Profile Setup State
  const { profile, saveProfile, userId } = useProfile();
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editForm, setEditForm] = useState(null);

  const INTERESTED_IN_OPTIONS = ['Hackathons', 'Internships', 'Scholarships', 'Competitions', 'Jobs', 'Offers'];
  const DOMAIN_OPTIONS = ['AI / Machine Learning', 'Web Development', 'App Development', 'Data Science', 'Cybersecurity', 'Cloud / DevOps', 'UI / UX', 'Open Source', 'Other'];
  const MODE_OPTIONS = ['Any', 'Remote', 'Hybrid', 'On-site'];

  const handleStartSetup = () => {
    setEditForm(profile || {
      fullName: '',
      username: '',
      interestedIn: [],
      interestDomains: [],
      opportunityMode: 'Any',
      notifications: {
        deadlineReminders: true,
        verificationCompleted: true,
        importantUpdates: true
      }
    });
    setIsEditingProfile(true);
  };

  const handleSaveProfile = () => {
    if (!editForm.fullName || !editForm.username) {
      alert("Full Name and Username are required.");
      return;
    }
    saveProfile(editForm);
    setIsEditingProfile(false);
  };

  const handleToggleArray = (field, value) => {
    setEditForm(prev => {
      const arr = prev[field] || [];
      if (arr.includes(value)) {
        return { ...prev, [field]: arr.filter(i => i !== value) };
      } else {
        return { ...prev, [field]: [...arr, value] };
      }
    });
  };

  const handleNotificationToggle = (key) => {
    setEditForm(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: !prev.notifications[key]
      }
    }));
  };

  // User customizable preferences with localStorage persistence
  const [autoResearch, setAutoResearch] = useState(() => {
    return localStorage.getItem('reelvault_pref_auto_research') === 'true';
  });
  const [timezone, setTimezone] = useState(() => {
    return localStorage.getItem('reelvault_pref_tz') || 'Asia/Kolkata (IST)';
  });
  const [exportFormat, setExportFormat] = useState(() => {
    return localStorage.getItem('reelvault_pref_export') || 'reelvault';
  });
  const [calendarSaved, setCalendarSaved] = useState(false);

  const handleExportFormatChange = (e) => {
    const val = e.target.value;
    setExportFormat(val);
    setCalendarSaved(false);
    if (val === 'reelvault') {
      localStorage.setItem('reelvault_pref_export', val);
    }
  };

  const displayEmail = user?.email || session?.user?.email || 'Signed in';
  const displayName = displayEmail.includes('@')
    ? displayEmail.split('@')[0].charAt(0).toUpperCase() + displayEmail.split('@')[0].slice(1)
    : 'User';
  // Load user's reels to calculate real-time stats
  const fetchUserVault = async () => {
    setLoadingReels(true);
    try {
      const data = await api.listReels();
      setReels(Array.isArray(data) ? data : []);
    } catch {
      setReels([]);
    } finally {
      setLoadingReels(false);
    }
  };

  useEffect(() => {
    fetchUserVault();
  }, []);

  useEffect(() => {
    if (window.location.hash === '#calendar-integration') {
      setTimeout(() => {
        const el = document.getElementById('calendar-integration');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          el.classList.add('ring-4', 'ring-[#8B5CF6]/40', 'transition-all', 'duration-500');
          setTimeout(() => el.classList.remove('ring-4', 'ring-[#8B5CF6]/40'), 2000);
        }
      }, 100);
    }
  }, []);

  // Compute live stats
  const stats = useMemo(() => {
    const total = reels.length;
    const platforms = new Set(reels.map((r) => r.platform).filter(Boolean));
    const withTranscript = reels.filter((r) => r.transcript && r.transcript.trim().length > 0).length;
    return {
      total,
      platformsCount: platforms.size || (total > 0 ? 1 : 0),
      withTranscript,
      platformNames: Array.from(platforms),
    };
  }, [reels]);

  const handleCopyId = () => {
    navigator.clipboard.writeText(userId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleToggleAutoResearch = () => {
    const next = !autoResearch;
    setAutoResearch(next);
    localStorage.setItem('reelvault_pref_auto_research', String(next));
  };

  const handleTimezoneChange = (e) => {
    const val = e.target.value;
    setTimezone(val);
    localStorage.setItem('reelvault_pref_tz', val);
  };


  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await signOut();
      navigate('/auth');
    } catch {
      setIsLoggingOut(false);
      setShowLogoutConfirm(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto pb-16 space-y-8">
      {/* Page Header */}
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8] text-xs font-bold uppercase tracking-wider mb-2">
            <User size={13} />
            <span>Account Dashboard</span>
          </div>
          <h1 className="font-display text-4xl sm:text-5xl tracking-wide text-[#261B33] uppercase leading-none">
            Your Profile
          </h1>
          <p className="text-[#776A83] font-medium text-base mt-2">
            Manage your ReelVault credentials, preferences, and opportunity vault activity.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchUserVault}
          disabled={loadingReels}
          className="self-start sm:self-auto inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#776A83] hover:text-[#6D28D9] bg-white border border-[#E3D4F8] hover:border-[#8B5CF6]/50 px-3 py-2 rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
          title="Refresh statistics"
        >
          <RefreshCw size={14} className={loadingReels ? 'animate-spin text-[#8B5CF6]' : ''} />
          <span>Sync Data</span>
        </button>
      </header>

      {/* Hero Profile Card */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#261B33] via-[#3B1D5A] to-[#1E0D36] border border-[#8B5CF6]/30 rounded-[2rem] p-6 sm:p-8 text-white shadow-xl shadow-[#8B5CF6]/10">
        {/* Glow ambient background accents */}
        <div className="absolute -right-16 -top-16 w-64 h-64 bg-[#8B5CF6]/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute right-32 -bottom-20 w-48 h-48 bg-[#E9A8D4]/15 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
            {/* Avatar badge */}
            <div className="relative">
              <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-gradient-to-tr from-[#8B5CF6] to-[#E9A8D4] text-[#261B33] flex items-center justify-center font-display text-3xl sm:text-4xl shadow-md font-bold uppercase tracking-wider">
                {profile?.fullName ? profile.fullName.charAt(0) : displayName.charAt(0)}
              </div>
              <span
                className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-500 border-2 border-[#261B33] rounded-full"
                title="Active Session"
              />
            </div>

            {/* Profile Info */}
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-2xl sm:text-3xl font-display uppercase tracking-wide text-white">
                  {profile?.fullName || displayName}
                </h2>
                <span className="bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8] text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full tracking-widest flex items-center gap-1">
                  <ShieldCheck size={11} strokeWidth={3} className="text-[#8B5CF6]" /> Verified
                </span>
                <span className="bg-white/10 text-gray-200 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full tracking-wider border border-white/15">
                  Early Adopter
                </span>
              </div>
              <div className="flex items-center gap-2">
                {profile?.username && (
                  <span className="text-[#EDE9FE]/80 text-sm font-medium">
                    @{profile.username}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 text-[#EDE9FE]/90 text-sm font-medium">
                <Mail size={14} className="text-[#E9A8D4]" />
                <span>{displayEmail}</span>
              </div>

              {/* User ID with Copy Action */}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-[#EDE9FE]/70 font-mono bg-black/25 px-2 py-1 rounded-md border border-white/10">
                  ID: {userId.length > 20 ? `${userId.slice(0, 12)}...${userId.slice(-6)}` : userId}
                </span>
                <button
                  type="button"
                  onClick={handleCopyId}
                  className="p-1 rounded-md bg-white/10 hover:bg-white/20 text-gray-300 hover:text-white transition-colors cursor-pointer"
                  title="Copy User ID"
                >
                  {copiedId ? <Check size={13} className="text-[#E9A8D4]" /> : <Copy size={13} />}
                </button>
                {copiedId && (
                  <span className="text-[11px] font-medium text-[#E9A8D4] animate-fade-in">
                    Copied!
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick Jump Action */}
          <div className="flex md:flex-col items-center md:items-end justify-between gap-3 pt-4 md:pt-0 border-t md:border-t-0 border-white/10">
            <div className="text-left md:text-right">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#EDE9FE]/70 block">
                Session Status
              </span>
              <span className="text-sm font-semibold text-[#E9A8D4] flex items-center gap-1.5 md:justify-end">
                <span className="w-2 h-2 rounded-full bg-[#E9A8D4] animate-pulse" />
                Authenticated
              </span>
            </div>

            <div className="flex gap-2">
              {profile && !isEditingProfile && (
                <button
                  type="button"
                  onClick={handleStartSetup}
                  className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-white text-[#6D28D9] hover:bg-[#F0E8FF] font-bold text-xs uppercase tracking-wider transition-all shadow-sm cursor-pointer"
                >
                  <Edit2 size={15} />
                  <span>Edit Profile</span>
                </button>
              )}
              <Link
                to="/vault"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs uppercase tracking-wider transition-all border border-white/15 hover:border-white/30"
              >
                <Bookmark size={15} />
                <span className="hidden sm:inline">Go to Vault</span>
                <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Setup Profile Banner */}
      {!profile && !isEditingProfile && (
        <div className="bg-gradient-to-r from-[#F9ECF5] to-[#F0E8FF] border border-[#E3D4F8] rounded-[2rem] p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
          <div>
            <h3 className="text-[#261B33] font-display text-2xl uppercase tracking-wide">Complete Your Profile</h3>
            <p className="text-[#776A83] text-sm font-medium mt-1">Set up your preferences to get personalized opportunity recommendations.</p>
          </div>
          <button 
            type="button"
            onClick={handleStartSetup} 
            className="w-full sm:w-auto bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white px-8 py-3.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all shadow-md shadow-[#8B5CF6]/25 cursor-pointer"
          >
            Set Up Profile
          </button>
        </div>
      )}

      {/* Editing Form */}
      {isEditingProfile && editForm && (
        <section className="bg-white rounded-[2rem] p-6 sm:p-8 border border-[#E3D4F8] shadow-xl space-y-8 animate-fade-in">
          <div className="flex items-center justify-between border-b border-[#E3D4F8]/70 pb-4">
            <h2 className="font-display text-2xl uppercase tracking-wide text-[#261B33]">
              {profile ? 'Edit Profile' : 'Set Up Profile'}
            </h2>
            <button 
              type="button"
              onClick={() => setIsEditingProfile(false)}
              className="p-2 hover:bg-[#F0E8FF] rounded-full text-[#776A83] hover:text-[#261B33] transition-colors cursor-pointer"
            >
              <X size={20} />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Basic Info */}
            <div className="space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[#776A83] flex items-center gap-2">
                <User size={16} className="text-[#8B5CF6]" /> Basic Info
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#776A83] mb-1">Full Name *</label>
                  <input 
                    type="text" 
                    value={editForm.fullName} 
                    onChange={e => setEditForm({...editForm, fullName: e.target.value})}
                    className="w-full px-4 py-2.5 bg-[#FBF7FD] border border-[#E3D4F8] rounded-xl text-sm font-semibold text-[#261B33] focus:outline-none focus:border-[#8B5CF6] focus:ring-1 focus:ring-[#8B5CF6]/20 transition-all"
                    placeholder="Jane Doe"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#776A83] mb-1">Username *</label>
                  <input 
                    type="text" 
                    value={editForm.username} 
                    onChange={e => setEditForm({...editForm, username: e.target.value})}
                    className="w-full px-4 py-2.5 bg-[#FBF7FD] border border-[#E3D4F8] rounded-xl text-sm font-semibold text-[#261B33] focus:outline-none focus:border-[#8B5CF6] focus:ring-1 focus:ring-[#8B5CF6]/20 transition-all"
                    placeholder="janedoe"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-[#776A83] mb-1">Email (Read-only)</label>
                  <input 
                    type="email" 
                    value={displayEmail} 
                    disabled
                    className="w-full px-4 py-2.5 bg-gray-100 border border-[#E3D4F8] rounded-xl text-sm font-semibold text-gray-500 cursor-not-allowed"
                  />
                </div>
              </div>
            </div>

            {/* Opportunity Preferences */}
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#776A83] flex items-center gap-2 mb-3">
                  <Briefcase size={16} className="text-[#8B5CF6]" /> Interested In
                </h3>
                <div className="flex flex-wrap gap-2">
                  {INTERESTED_IN_OPTIONS.map(opt => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleToggleArray('interestedIn', opt)}
                      className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                        (editForm.interestedIn || []).includes(opt) 
                          ? 'bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] text-white shadow-xs' 
                          : 'bg-[#FBF7FD] border border-[#E3D4F8] text-[#776A83] hover:bg-[#F0E8FF] hover:text-[#261B33]'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#776A83] flex items-center gap-2 mb-3">
                  <Globe size={16} className="text-[#8B5CF6]" /> Interest Domains
                </h3>
                <div className="flex flex-wrap gap-2">
                  {DOMAIN_OPTIONS.map(opt => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleToggleArray('interestDomains', opt)}
                      className={`px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                        (editForm.interestDomains || []).includes(opt) 
                          ? 'bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] text-white shadow-xs' 
                          : 'bg-[#FBF7FD] border border-[#E3D4F8] text-[#776A83] hover:bg-[#F0E8FF] hover:text-[#261B33]'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-[#776A83] mb-3">Opportunity Mode</h3>
                <div className="flex flex-wrap gap-2">
                  {MODE_OPTIONS.map(opt => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => setEditForm({...editForm, opportunityMode: opt})}
                      className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        editForm.opportunityMode === opt 
                          ? 'bg-[#8B5CF6] text-white shadow-xs' 
                          : 'bg-white border border-[#E3D4F8] text-[#776A83] hover:bg-[#F0E8FF]'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-[#E3D4F8]/70 pt-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-[#776A83] flex items-center gap-2 mb-4">
              <Bell size={16} className="text-[#8B5CF6]" /> Notifications
            </h3>
            <div className="space-y-3">
              {[
                { key: 'deadlineReminders', label: 'Deadline Reminders' },
                { key: 'verificationCompleted', label: 'Verification Completed' },
                { key: 'importantUpdates', label: 'Important Opportunity Updates' }
              ].map(notif => (
                <div key={notif.key} className="flex items-center justify-between py-2 border-b border-[#E3D4F8]/40 last:border-0">
                  <span className="text-sm font-medium text-[#261B33]">{notif.label}</span>
                  <button
                    type="button"
                    role="switch"
                    onClick={() => handleNotificationToggle(notif.key)}
                    className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                      editForm.notifications?.[notif.key] ? 'bg-[#8B5CF6]' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                        editForm.notifications?.[notif.key] ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-6 border-t border-[#E3D4F8]/70 flex justify-end gap-3">
            <button 
              type="button"
              onClick={() => setIsEditingProfile(false)}
              className="px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider text-[#776A83] hover:bg-[#F0E8FF] transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button 
              type="button"
              onClick={handleSaveProfile}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs uppercase tracking-wider transition-all shadow-md shadow-[#8B5CF6]/25 cursor-pointer"
            >
              <Save size={16} />
              Save Profile
            </button>
          </div>
        </section>
      )}

      {/* Profile Display View */}
      {profile && !isEditingProfile && (
        <section className="bg-white rounded-[2rem] p-6 sm:p-7 border border-[#E3D4F8] shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-[#E3D4F8]/70 pb-4">
            <div className="flex items-center gap-2">
              <Briefcase size={18} className="text-[#8B5CF6]" />
              <h2 className="font-display text-xl uppercase tracking-wide text-[#261B33]">
                Opportunity Preferences
              </h2>
            </div>
            <span className="text-xs font-bold uppercase text-[#6D28D9] bg-[#F0E8FF] border border-[#E3D4F8] px-2.5 py-1 rounded-md">Mode: {profile.opportunityMode}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#776A83] mb-3">Interested In</h3>
              <div className="flex flex-wrap gap-2">
                {profile.interestedIn?.length > 0 ? profile.interestedIn.map(opt => (
                  <span key={opt} className="px-3 py-1 rounded-full text-xs font-bold bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8]">
                    {opt}
                  </span>
                )) : <span className="text-sm text-[#776A83]/60">None selected</span>}
              </div>
            </div>

            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#776A83] mb-3">Interest Domains</h3>
              <div className="flex flex-wrap gap-2">
                {profile.interestDomains?.length > 0 ? profile.interestDomains.map(opt => (
                  <span key={opt} className="px-3 py-1 rounded-full text-xs font-bold bg-[#F9ECF5] text-[#6D28D9] border border-[#E3D4F8]">
                    {opt}
                  </span>
                )) : <span className="text-sm text-[#776A83]/60">None selected</span>}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Activity & Performance Metrics Grid */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-[#8B5CF6]" />
            <h2 className="font-display text-xl uppercase tracking-wide text-[#261B33]">
              Vault & AI Statistics
            </h2>
          </div>
          <span className="text-xs text-[#776A83] font-medium">Real-time usage</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Total Saved */}
          <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm flex flex-col justify-between hover:border-[#8B5CF6]/40 transition-colors">
            <div className="flex items-center justify-between text-[#776A83] mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#776A83]">Total Saved</span>
              <div className="w-8 h-8 rounded-lg bg-[#F0E8FF] text-[#6D28D9] flex items-center justify-center">
                <Bookmark size={16} />
              </div>
            </div>
            <div>
              <div className="text-3xl font-display text-[#261B33]">
                {loadingReels ? '—' : stats.total}
              </div>
              <p className="text-xs text-[#776A83] mt-1 font-medium">
                {stats.total === 1 ? '1 reel stored in vault' : `${stats.total} reels stored in vault`}
              </p>
            </div>
          </div>

          {/* Card 2: Extracted Transcripts */}
          <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm flex flex-col justify-between hover:border-[#8B5CF6]/40 transition-colors">
            <div className="flex items-center justify-between text-[#776A83] mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#776A83]">Transcripts</span>
              <div className="w-8 h-8 rounded-lg bg-[#F0E8FF] text-[#6D28D9] flex items-center justify-center">
                <Layers size={16} />
              </div>
            </div>
            <div>
              <div className="text-3xl font-display text-[#261B33]">
                {loadingReels ? '—' : stats.withTranscript}
              </div>
              <p className="text-xs text-[#776A83] mt-1 font-medium">
                Verbatim audio extractions
              </p>
            </div>
          </div>

          {/* Card 3: Platforms Tracked */}
          <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm flex flex-col justify-between hover:border-[#8B5CF6]/40 transition-colors">
            <div className="flex items-center justify-between text-[#776A83] mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#776A83]">Platforms</span>
              <div className="w-8 h-8 rounded-lg bg-[#F0E8FF] text-[#6D28D9] flex items-center justify-center">
                <ExternalLink size={16} />
              </div>
            </div>
            <div>
              <div className="text-3xl font-display text-[#261B33]">
                {loadingReels ? '—' : stats.platformsCount || 3}
              </div>
              <p className="text-xs text-[#776A83] mt-1 font-medium">
                {stats.platformNames.length > 0
                  ? stats.platformNames.join(', ')
                  : 'Instagram, YouTube, TikTok'}
              </p>
            </div>
          </div>

          {/* Card 4: AI Model Tier */}
          <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-sm flex flex-col justify-between hover:border-[#8B5CF6]/40 transition-colors">
            <div className="flex items-center justify-between text-[#776A83] mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-[#776A83]">Verification</span>
              <div className="w-8 h-8 rounded-lg bg-[#F9ECF5] text-[#8B5CF6] flex items-center justify-center">
                <Sparkles size={16} />
              </div>
            </div>
            <div>
              <div className="text-xl font-display text-[#6D28D9] uppercase tracking-wide">
                Opportunity Engine
              </div>
              <p className="text-xs text-[#776A83] mt-1 font-medium">
                Official source verification
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Two-Column Grid: Preferences & Security */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Preferences Section */}
        <section className="bg-white rounded-[2rem] p-6 sm:p-7 border border-[#E3D4F8] shadow-sm space-y-6">
          <div className="flex items-center gap-2 border-b border-[#E3D4F8]/70 pb-4">
            <Settings size={18} className="text-[#8B5CF6]" />
            <h2 className="font-display text-xl uppercase tracking-wide text-[#261B33]">
              Pipeline Preferences
            </h2>
          </div>

          <div className="space-y-5">
            {/* Timezone Setting */}
            <div className="space-y-1.5">
              <label htmlFor="pref-timezone" className="block text-xs font-bold uppercase tracking-wider text-[#776A83]">
                Default Timezone
              </label>
              <p className="text-xs text-[#776A83]">
                Used to resolve ambiguous deadlines extracted from reels (e.g. "this Friday").
              </p>
              <select
                id="pref-timezone"
                value={timezone}
                onChange={handleTimezoneChange}
                className="w-full mt-1 px-3.5 py-2.5 bg-[#FBF7FD] border border-[#E3D4F8] rounded-xl text-sm font-semibold text-[#261B33] focus:outline-none focus:border-[#8B5CF6] focus:ring-1 focus:ring-[#8B5CF6]/20 transition-all"
              >
                <option value="Asia/Kolkata (IST)">Asia/Kolkata (IST) — Default</option>
                <option value="UTC (Coordinated Universal Time)">UTC (Universal)</option>
                <option value="America/New_York (EST/EDT)">America/New_York (EST)</option>
                <option value="Europe/London (GMT/BST)">Europe/London (GMT)</option>
              </select>
            </div>

            {/* Calendar Export Format */}
            <div className="space-y-1.5 pt-2 border-t border-[#E3D4F8]/60" id="calendar-integration">
              <label htmlFor="pref-export" className="block text-xs font-bold uppercase tracking-wider text-[#776A83]">
                Calendar Integration
              </label>
              <p className="text-xs text-[#776A83]">
                Choose how you want to track confirmed opportunity deadlines.
              </p>
              <select
                id="pref-export"
                value={exportFormat}
                onChange={handleExportFormatChange}
                className="w-full mt-1 px-3.5 py-2.5 bg-[#FBF7FD] border border-[#E3D4F8] rounded-xl text-sm font-semibold text-[#261B33] focus:outline-none focus:border-[#8B5CF6] focus:ring-1 focus:ring-[#8B5CF6]/20 transition-all"
              >
                <option value="reelvault">ReelVault Calendar (Default)</option>
                <option value="google">Google Calendar</option>
              </select>

              {exportFormat === 'google' && (
                <div className="mt-4 p-4 bg-[#F0E8FF]/40 rounded-xl border border-[#E3D4F8]">
                  <p className="text-sm font-medium text-[#261B33] mb-4">
                    Google Calendar is enabled. Events will open in Google Calendar with their details pre-filled.
                  </p>
                  
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        localStorage.setItem('reelvault_pref_export', 'google');
                        setCalendarSaved(true);
                      }}
                      className="bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all shadow-sm cursor-pointer"
                    >
                      SAVE CALENDAR PREFERENCE
                    </button>
                    {calendarSaved && (
                      <Link to="/vault" className="text-xs font-bold uppercase tracking-wider text-[#8B5CF6] hover:text-[#6D28D9] flex items-center gap-1">
                        BACK TO VAULT <ArrowRight size={13} />
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Auto Verification Toggle */}
            <div className="flex items-center justify-between pt-2 border-t border-[#E3D4F8]/60">
              <div className="space-y-0.5 pr-4">
                <span className="block text-xs font-bold uppercase tracking-wider text-[#261B33]">
                  Instant Deep Research
                </span>
                <span className="block text-xs text-[#776A83]">
                  Trigger automated web verification as soon as a reel transcript is saved.
                </span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={autoResearch}
                onClick={handleToggleAutoResearch}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  autoResearch ? 'bg-[#8B5CF6]' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                    autoResearch ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </section>

        {/* Security & Authentication Info */}
        <section className="bg-white rounded-[2rem] p-6 sm:p-7 border border-[#E3D4F8] shadow-sm flex flex-col justify-between space-y-6">
          <div>
            <div className="flex items-center gap-2 border-b border-[#E3D4F8]/70 pb-4 mb-5">
              <Shield size={18} className="text-[#8B5CF6]" />
              <h2 className="font-display text-xl uppercase tracking-wide text-[#261B33]">
                Security & Session
              </h2>
            </div>

            <div className="space-y-3.5">
              <div className="flex items-center justify-between p-3 rounded-xl bg-[#FBF7FD] border border-[#E3D4F8]/80">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center">
                    <CheckCircle2 size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-[#261B33]">Auth Token Active</div>
                    <div className="text-[11px] text-[#776A83]">Secure JWT Bearer Session</div>
                  </div>
                </div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md">
                  Encrypted
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#FBF7FD] border border-[#E3D4F8]/80">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-[#F0E8FF] text-[#6D28D9] flex items-center justify-center">
                    <Clock size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-[#261B33]">Automatic Refresh</div>
                    <div className="text-[11px] text-[#776A83]">Session kept alive securely</div>
                  </div>
                </div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#6D28D9] bg-[#F0E8FF] border border-[#E3D4F8] px-2 py-1 rounded-md">
                  Active
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-[#FBF7FD] border border-[#E3D4F8]/80">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center">
                    <Calendar size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-[#261B33]">Opportunity Retention</div>
                    <div className="text-[11px] text-[#776A83]">Per-user isolated vault data</div>
                  </div>
                </div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800 bg-amber-50 px-2 py-1 rounded-md">
                  Private
                </span>
              </div>
            </div>
          </div>

          {/* Sign Out Card Button */}
          <div className="pt-4 border-t border-[#E3D4F8]/70">
            {!showLogoutConfirm ? (
              <button
                type="button"
                onClick={() => setShowLogoutConfirm(true)}
                className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-red-200 text-red-600 hover:bg-red-50 hover:border-red-300 rounded-xl text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer"
              >
                <LogOut size={16} />
                <span>Sign Out of ReelVault</span>
              </button>
            ) : (
              <div className="p-3.5 bg-red-50/70 border border-red-200 rounded-xl space-y-3">
                <p className="text-xs font-semibold text-red-900 text-center">
                  Are you sure you want to end your current session?
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleLogout}
                    disabled={isLoggingOut}
                    className="flex-1 py-2 px-3 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-colors disabled:opacity-60 cursor-pointer"
                  >
                    {isLoggingOut ? 'Signing out...' : 'Yes, Sign Out'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowLogoutConfirm(false)}
                    disabled={isLoggingOut}
                    className="flex-1 py-2 px-3 bg-white border border-gray-200 text-gray-700 hover:bg-gray-100 rounded-lg text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Quick Navigation Footer Banner */}
      <div className="bg-white rounded-2xl p-5 border border-[#E3D4F8] shadow-xs flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#F0E8FF] text-[#8B5CF6] border border-[#E3D4F8] flex items-center justify-center font-bold">
            <Bookmark size={20} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-[#261B33]">Ready to save another opportunity?</h4>
            <p className="text-xs text-[#776A83] font-medium">Paste Instagram, YouTube, or TikTok short links anytime.</p>
          </div>
        </div>

        <Link
          to="/home"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white text-xs font-bold uppercase tracking-wider transition-all shadow-sm shadow-[#8B5CF6]/25"
        >
          <span>Save a Reel</span>
          <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  );
}
