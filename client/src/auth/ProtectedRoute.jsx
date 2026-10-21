import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';

export default function ProtectedRoute() {
  const { session, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="min-h-screen bg-[#FBF7FD]" />;
  return session ? <Outlet /> : <Navigate to="/auth" replace state={{ from: location.pathname }} />;
}
