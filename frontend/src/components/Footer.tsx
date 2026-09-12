import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer
      className="w-full py-8 px-5 md:px-10 border-t"
      style={{ background: '#090909', borderColor: 'rgba(255,255,255,0.05)' }}
    >
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">

        <div className="flex items-center gap-2.5">
          <span
            className="w-6 h-6 rounded-[5px] flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)' }}
          >
            <span className="material-symbols-outlined text-[12px] text-black" style={{ fontVariationSettings: "'FILL' 1,'wght' 700,'GRAD' 0,'opsz' 20" }}>
              flight_takeoff
            </span>
          </span>
          <span className="text-[13px] font-bold text-white">GeoForge</span>
          <span className="text-[12px] ml-1" style={{ color: '#333' }}>— drone video → interactive 3D models</span>
        </div>

        <p className="text-[12px]" style={{ color: '#333' }}>
          Built for drone operators, engineers, and curious people.
        </p>

      </div>
    </footer>
  );
};
