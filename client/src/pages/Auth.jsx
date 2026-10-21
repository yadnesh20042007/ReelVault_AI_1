import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Play, Eye, EyeOff, Sparkles, ArrowRight } from 'lucide-react';
import Button from '../components/ui/Button';
import { ApiError } from '../services/api';
import { useAuth } from '../auth/useAuth';

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();
  const { signIn, signUp } = useAuth();

  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const newErrors = {};
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      newErrors.email = "Email or username is required.";
    } else if (trimmedEmail.toLowerCase() !== 'admin' && !/\S+@\S+\.\S+/.test(trimmedEmail)) {
      newErrors.email = "Enter a valid email address (or 'admin' for prototyping).";
    }
    
    if (!password) {
      newErrors.password = "Password is required.";
    }

    if (!isLogin) {
      if (!name) newErrors.name = "Full name is required.";
      if (password !== confirmPassword) {
        newErrors.confirmPassword = "Passwords do not match.";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError('');
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      if (isLogin) {
        await signIn(email.trim(), password);
        navigate('/home');
      } else {
        const result = await signUp(email.trim(), password);
        if (result.session) {
          navigate('/home');
        } else {
          setIsLogin(true);
          setSubmitError('Check your email to confirm your account, then log in.');
        }
      }
    } catch (error) {
      setSubmitError(error instanceof ApiError ? error.message : 'Unable to connect to ReelVault. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickAdminLogin = async () => {
    setIsSubmitting(true);
    setSubmitError('');
    try {
      await signIn('admin', 'admin');
      navigate('/home');
    } catch (error) {
      setSubmitError(error instanceof ApiError ? error.message : 'Unable to complete admin login.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#FBF7FD] via-[#F9ECF5]/40 to-[#F0E8FF]/60 flex font-sans text-[#261B33] relative overflow-hidden">
      {/* Soft background ambient blurs */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-[#8B5CF6]/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-10 w-80 h-80 bg-[#E9A8D4]/15 rounded-full blur-3xl pointer-events-none" />

      {/* LEFT SIDE: Branding (Desktop) */}
      <div className="hidden lg:flex flex-1 flex-col justify-between p-12 xl:p-20 border-r border-[#E3D4F8]/80 relative z-10">
        <Link to="/" className="flex items-center gap-2.5 w-max group">
          <div className="w-11 h-11 bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] rounded-2xl flex items-center justify-center shadow-md shadow-[#8B5CF6]/25 group-hover:scale-105 transition-transform">
            <Play className="text-white w-5 h-5 ml-0.5" fill="currentColor" />
          </div>
          <div className="flex items-center gap-1.5">
            <span className="font-display text-2xl tracking-wide uppercase mt-1 text-[#261B33]">ReelVault</span>
            <span className="bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8] text-xs font-black px-2 py-0.5 rounded-md uppercase tracking-wider">AI</span>
          </div>
        </Link>
        
        <div className="max-w-md xl:max-w-lg">
          <h1 className="font-display text-5xl xl:text-6xl uppercase tracking-wide text-[#261B33] mb-6 leading-tight">
            Verify before<br />you apply.
          </h1>
          <p className="text-[#776A83] text-lg leading-relaxed mb-10 font-medium">
            Turn opportunities discovered in short-form content into verified information you can actually act on.
          </p>
          
          <div className="flex items-center flex-wrap gap-y-3 gap-x-4 text-xs font-bold text-[#6D28D9] uppercase tracking-widest bg-white/80 backdrop-blur-sm px-5 py-4 rounded-2xl border border-[#E3D4F8] shadow-2xs">
            <span>Reel</span>
            <span className="text-[#E9A8D4]">→</span>
            <span>Claims</span>
            <span className="text-[#E9A8D4]">→</span>
            <span>Evidence</span>
            <span className="text-[#E9A8D4]">→</span>
            <span className="text-[#261B33]">Opportunity</span>
          </div>
        </div>
        
        <div className="text-sm font-semibold text-[#776A83]/70">© 2026 ReelVault AI</div>
      </div>

      {/* RIGHT SIDE: Auth Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 relative overflow-y-auto z-10">
        
        {/* Mobile Header */}
        <div className="lg:hidden absolute top-6 left-6">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-[#6D28D9] to-[#8B5CF6] rounded-xl flex items-center justify-center shadow-xs">
              <Play className="text-white w-4 h-4 ml-0.5" fill="currentColor" />
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-display text-xl tracking-wide uppercase mt-1 text-[#261B33]">ReelVault</span>
              <span className="bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8] text-[10px] font-black px-1.5 py-0.5 rounded-sm uppercase tracking-wide">AI</span>
            </div>
          </Link>
        </div>

        <div className="w-full max-w-md bg-white rounded-3xl p-8 sm:p-10 shadow-[0_16px_50px_-12px_rgba(139,92,246,0.12)] border border-[#E3D4F8] mt-12 lg:mt-0">
          
          <h2 className="text-2xl sm:text-3xl font-bold text-[#261B33] mb-2 tracking-tight">Welcome to ReelVault</h2>
          <p className="text-[#776A83] mb-6 text-sm font-medium">Sign in to save reel titles and transcripts.</p>

          {/* Offline Prototyping Quick Access Card */}
          {isLogin && (
            <div className="mb-6 p-4 rounded-2xl bg-gradient-to-br from-[#F9ECF5]/80 to-[#F0E8FF]/80 border border-[#E3D4F8] space-y-2.5 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-[#6D28D9] flex items-center gap-1.5">
                  <Sparkles size={14} className="text-[#8B5CF6]" />
                  Prototyping Mode
                </span>
                <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#F0E8FF] text-[#6D28D9] border border-[#E3D4F8]">
                  No Backend Needed
                </span>
              </div>
              <p className="text-xs text-[#776A83] leading-relaxed font-medium">
                Access the complete website with mock reels, verified research, and calendar offline.
              </p>
              <button
                type="button"
                onClick={handleQuickAdminLogin}
                disabled={isSubmitting}
                className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white text-xs font-bold uppercase tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm shadow-[#8B5CF6]/25 disabled:opacity-60"
              >
                <span>Quick Login as Admin</span>
                <ArrowRight size={14} />
              </button>
            </div>
          )}

          {/* Toggle Tabs */}
          <div className="flex bg-[#F0E8FF]/70 p-1 rounded-xl mb-6 border border-[#E3D4F8]/70">
            <button 
              onClick={() => { setIsLogin(true); setErrors({}); setSubmitError(''); }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all cursor-pointer ${isLogin ? 'bg-white shadow-sm text-[#261B33] font-bold' : 'text-[#776A83] hover:text-[#261B33]'}`}
            >
              Log in
            </button>
            <button 
              onClick={() => { setIsLogin(false); setErrors({}); setSubmitError(''); }}
              className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all cursor-pointer ${!isLogin ? 'bg-white shadow-sm text-[#261B33] font-bold' : 'text-[#776A83] hover:text-[#261B33]'}`}
            >
              Sign up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {!isLogin && (
              <div className="space-y-1.5">
                <label className="block text-sm font-semibold text-[#261B33]">Full name</label>
                <input 
                  type="text" 
                  placeholder="John Doe" 
                  value={name} 
                  onChange={(e) => setName(e.target.value)}
                  className={`w-full px-4 py-3 bg-[#FBF7FD] border ${errors.name ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20' : 'border-[#E3D4F8] focus:border-[#8B5CF6] focus:ring-[#8B5CF6]/20'} rounded-xl text-[#261B33] placeholder:text-[#776A83]/50 focus:outline-none focus:ring-2 transition-all`}
                />
                {errors.name && <p className="text-red-500 text-xs font-medium">{errors.name}</p>}
              </div>
            )}

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-semibold text-[#261B33]">Email or username</label>
                {isLogin && <span className="text-[11px] font-semibold text-[#776A83]">admin for offline</span>}
              </div>
              <input 
                type="text" 
                placeholder="you@example.com or admin" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                autoCapitalize="none"
                autoCorrect="off"
                className={`w-full px-4 py-3 bg-[#FBF7FD] border ${errors.email ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20' : 'border-[#E3D4F8] focus:border-[#8B5CF6] focus:ring-[#8B5CF6]/20'} rounded-xl text-[#261B33] placeholder:text-[#776A83]/50 focus:outline-none focus:ring-2 transition-all`}
              />
              {errors.email && <p className="text-red-500 text-xs font-medium">{errors.email}</p>}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-semibold text-[#261B33]">Password</label>
                {isLogin && <span className="text-[11px] font-semibold text-[#776A83]">admin for offline</span>}
              </div>
              <div className="relative">
                <input 
                  type={showPassword ? 'text' : 'password'} 
                  placeholder="••••••••" 
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full px-4 py-3 bg-[#FBF7FD] border ${errors.password ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20' : 'border-[#E3D4F8] focus:border-[#8B5CF6] focus:ring-[#8B5CF6]/20'} rounded-xl text-[#261B33] placeholder:text-[#776A83]/50 focus:outline-none focus:ring-2 transition-all pr-10`}
                />
                <button 
                  type="button" 
                  onClick={() => setShowPassword(!showPassword)} 
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#776A83] hover:text-[#261B33] focus:outline-none cursor-pointer"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-xs font-medium">{errors.password}</p>}
            </div>

            {!isLogin && (
              <div className="space-y-1.5">
                <label className="block text-sm font-semibold text-[#261B33]">Confirm password</label>
                <div className="relative">
                  <input 
                    type={showPassword ? 'text' : 'password'} 
                    placeholder="••••••••" 
                    value={confirmPassword} 
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full px-4 py-3 bg-[#FBF7FD] border ${errors.confirmPassword ? 'border-red-400 focus:border-red-500 focus:ring-red-500/20' : 'border-[#E3D4F8] focus:border-[#8B5CF6] focus:ring-[#8B5CF6]/20'} rounded-xl text-[#261B33] placeholder:text-[#776A83]/50 focus:outline-none focus:ring-2 transition-all pr-10`}
                  />
                </div>
                {errors.confirmPassword && <p className="text-red-500 text-xs font-medium">{errors.confirmPassword}</p>}
              </div>
            )}

            {!isLogin && (
              <div className="flex items-start gap-2.5 pt-2">
                <input 
                  type="checkbox" 
                  id="terms" 
                  required
                  className="mt-0.5 w-4 h-4 rounded border-[#E3D4F8] text-[#8B5CF6] focus:ring-[#8B5CF6] cursor-pointer" 
                />
                <label htmlFor="terms" className="text-xs text-[#776A83] font-medium cursor-pointer">
                  I agree to the <a href="#" className="text-[#8B5CF6] hover:text-[#6D28D9] font-semibold hover:underline">Terms</a> & <a href="#" className="text-[#8B5CF6] hover:text-[#6D28D9] font-semibold hover:underline">Privacy Policy</a>
                </label>
              </div>
            )}

            <Button disabled={isSubmitting} type="submit" className="w-full bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white shadow-md shadow-[#8B5CF6]/25 hover:shadow-lg py-3.5 text-base mt-2 rounded-xl font-bold disabled:opacity-60 cursor-pointer transition-all">
              {isSubmitting ? 'Please wait…' : isLogin ? 'Log in' : 'Create account'}
            </Button>
            {submitError && <div className="text-sm font-medium text-red-600 bg-red-50 border border-red-200 py-2.5 px-3 rounded-xl text-center">{submitError}</div>}
          </form>

          {isLogin && (
            <>
              <div className="my-6 flex items-center gap-4">
                <div className="flex-1 h-px bg-[#E3D4F8]/80"></div>
                <span className="text-xs font-bold text-[#776A83] uppercase tracking-wider">OR</span>
                <div className="flex-1 h-px bg-[#E3D4F8]/80"></div>
              </div>
              
              <div className="w-full bg-[#FBF7FD] border border-[#E3D4F8] text-[#776A83] font-semibold py-3.5 rounded-xl flex items-center justify-center gap-3 shadow-2xs cursor-not-allowed" title="Google login is not configured on this API yet">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Google login is not configured
              </div>
            </>
          )}

          <div className="mt-8 text-center text-sm text-[#776A83] font-medium">
            {isLogin ? (
              <>Don't have an account? <button onClick={() => { setIsLogin(false); setErrors({}); setSubmitError(''); }} className="text-[#8B5CF6] font-bold hover:text-[#6D28D9] hover:underline cursor-pointer">Sign up</button></>
            ) : (
              <>Already have an account? <button onClick={() => { setIsLogin(true); setErrors({}); setSubmitError(''); }} className="text-[#8B5CF6] font-bold hover:text-[#6D28D9] hover:underline cursor-pointer">Log in</button></>
            )}
          </div>
          
        </div>
      </div>
      
    </div>
  );
}
