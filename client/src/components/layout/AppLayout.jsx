import { Outlet } from 'react-router-dom';
import TopNav from './TopNav';
import BottomNav from './BottomNav';
export default function AppLayout() {
  return (
    <div className="min-h-screen flex flex-col pb-16 md:pb-0 bg-[#FBF7FD] text-[#261B33] font-sans selection:bg-[#E9A8D4]/30 selection:text-[#6D28D9]">
      <TopNav />
      <main className="flex-1 w-full max-w-5xl mx-auto p-4 md:p-8 lg:p-10">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}

