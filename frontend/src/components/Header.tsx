import React, { useState } from 'react';

interface HeaderProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentRoute, onNavigate }) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const nav = (route: string) => {
    setMobileOpen(false);
    onNavigate(route);
  };

  const linkClass = (route: string) =>
    `text-[13px] font-medium transition-colors cursor-pointer ${
      currentRoute === route
        ? 'text-white'
        : 'text-[#666] hover:text-[#ccc]'
    }`;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.07] bg-[#090909]/85 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-5 md:px-10 h-14 flex items-center justify-between">

        {/* Logo */}
        <button
          onClick={() => nav('home')}
          className="flex items-center gap-2.5 cursor-pointer focus:outline-none group"
        >
          {/* Amber hexagon mark */}
          <span
            className="w-7 h-7 rounded-[6px] flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}
          >
            <span className="material-symbols-outlined text-[14px] text-black" style={{ fontVariationSettings: "'FILL' 1,'wght' 700,'GRAD' 0,'opsz' 20" }}>
              flight_takeoff
            </span>
          </span>
          <span className="text-[15px] font-bold text-white tracking-tight">GeoForge</span>
        </button>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          <button onClick={() => nav('home')} className={linkClass('home')}>Home</button>
          <button onClick={() => nav('how-it-works')} className={linkClass('how-it-works')}>
            How it works
          </button>
          <button onClick={() => nav('history')} className={linkClass('history')}>
            Job History
          </button>
        </nav>

        {/* CTA + mobile toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => nav('upload')}
            className="hidden md:flex items-center gap-1.5 text-black text-[13px] font-semibold px-4 py-2 rounded-lg transition-all active:scale-95 cursor-pointer"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}
          >
            <span className="material-symbols-outlined text-[15px]">upload</span>
            Upload video
          </button>

          <button
            className="md:hidden text-[#666] hover:text-white transition-colors p-1"
            onClick={() => setMobileOpen(o => !o)}
            aria-label="Toggle menu"
          >
            <span className="material-symbols-outlined">{mobileOpen ? 'close' : 'menu'}</span>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-[#0d0d0d] border-t border-white/[0.07] px-5 py-5 flex flex-col gap-5">
          <button onClick={() => nav('home')} className="text-left text-[14px] text-[#999] hover:text-white transition-colors">Home</button>
          <button onClick={() => nav('how-it-works')} className="text-left text-[14px] text-[#999] hover:text-white transition-colors">How it works</button>
          <button onClick={() => nav('history')} className="text-left text-[14px] text-[#999] hover:text-white transition-colors">Job History</button>
          <button
            onClick={() => nav('upload')}
            className="text-[14px] font-semibold px-5 py-2.5 rounded-lg w-full text-center text-black"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}
          >
            Upload video
          </button>
        </div>
      )}
    </header>
  );
};
