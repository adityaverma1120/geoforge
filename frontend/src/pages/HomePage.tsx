import React from 'react';

interface HomePageProps {
  onNavigate: (route: string) => void;
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigate }) => {
  return (
    <div className="flex-1 flex flex-col w-full">

      {/* ─── Hero ─────────────────────────────────────────────── */}
      <section className="relative w-full overflow-hidden" style={{ background: '#090909' }}>

        {/* Grid bg */}
        <div className="absolute inset-0 cad-grid pointer-events-none opacity-100" />

        {/* Amber glow behind the visual */}
        <div
          className="absolute right-0 top-0 w-[55%] h-full pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 60% 60% at 70% 40%, rgba(245,158,11,0.07) 0%, transparent 70%)' }}
        />

        <div className="relative z-10 max-w-6xl mx-auto px-5 md:px-10 py-20 md:py-28 flex flex-col md:flex-row md:items-center gap-14 md:gap-10">

          {/* Left — copy */}
          <div className="flex-1 flex flex-col gap-7 max-w-xl">

            <span
              className="inline-flex items-center gap-2 w-fit px-3 py-1 rounded-full text-[11px] font-semibold tracking-widest uppercase"
              style={{ background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#f59e0b] animate-pulse" />
              Photogrammetry · Structure from Motion
            </span>

            <h1 className="text-[42px] sm:text-[58px] font-black leading-[1.0] tracking-tight text-white">
              Drone footage.{' '}
              <br />
              <span style={{ color: '#f59e0b' }}>3D model.</span>
              <br />
              <span className="text-[#444] font-light">No work.</span>
            </h1>

            <p className="text-[16px] leading-[28px] text-[#888]">
              Drop in a flight video and GeoForge runs the full reconstruction
              pipeline — frame filtering, feature matching, bundle adjustment,
              mesh generation — and hands you back an interactive 3D model.
            </p>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => onNavigate('upload')}
                className="flex items-center gap-2 px-6 py-3 rounded-lg text-[14px] font-bold text-black transition-all active:scale-[0.97] cursor-pointer"
                style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)', boxShadow: '0 4px 24px rgba(245,158,11,0.3)' }}
              >
                <span className="material-symbols-outlined text-[18px]">upload</span>
                Upload a video
              </button>
              <button
                onClick={() => onNavigate('how-it-works')}
                className="flex items-center gap-2 px-6 py-3 rounded-lg text-[14px] font-semibold text-[#888] hover:text-white border border-white/10 hover:border-white/20 transition-all active:scale-[0.97] cursor-pointer"
                style={{ background: 'rgba(255,255,255,0.03)' }}
              >
                How it works
              </button>
            </div>

            <div className="flex flex-wrap gap-x-6 gap-y-2 pt-1">
              {[
                'MP4 · MOV · AVI',
                'Outputs GLB + OBJ',
                'Runs on the server — not your laptop',
              ].map(t => (
                <span key={t} className="flex items-center gap-1.5 text-[12px] text-[#555]">
                  <span className="w-1 h-1 rounded-full bg-[#f59e0b] opacity-70" />
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Right — terrain visual */}
          <div className="flex-1 max-w-lg w-full">
            <div
              className="relative rounded-2xl overflow-hidden"
              style={{
                background: '#0e0e0e',
                border: '1px solid rgba(255,255,255,0.08)',
                boxShadow: '0 0 80px rgba(245,158,11,0.08), 0 32px 64px rgba(0,0,0,0.5)',
              }}
            >
              {/* Fake browser chrome */}
              <div
                className="flex items-center gap-1.5 px-4 py-3 border-b"
                style={{ background: '#131313', borderColor: 'rgba(255,255,255,0.06)' }}
              >
                <span className="w-2.5 h-2.5 rounded-full bg-[#3a3a3a]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#3a3a3a]" />
                <span className="w-2.5 h-2.5 rounded-full bg-[#3a3a3a]" />
                <span className="ml-3 text-[11px] font-mono text-[#444]">model-viewer · site-survey.glb</span>
                <span
                  className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded"
                  style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b' }}
                >
                  LIVE
                </span>
              </div>

              {/* Simulated 3D terrain viewport using CSS */}
              <div className="relative w-full" style={{ paddingBottom: '62%', background: '#0a0a0a' }}>
                <div className="absolute inset-0 flex items-center justify-center overflow-hidden">
                  {/* Perspective grid terrain */}
                  <div className="w-full h-full relative" style={{ perspective: '600px' }}>
                    <div
                      className="absolute inset-0"
                      style={{
                        transform: 'rotateX(45deg) rotateZ(-10deg) scale(1.6)',
                        transformOrigin: 'center 70%',
                        backgroundImage: `
                          linear-gradient(rgba(245,158,11,0.25) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(245,158,11,0.25) 1px, transparent 1px)
                        `,
                        backgroundSize: '36px 36px',
                      }}
                    />
                    {/* Elevation glow */}
                    <div
                      className="absolute"
                      style={{
                        width: '220px',
                        height: '220px',
                        top: '20%',
                        left: '30%',
                        background: 'radial-gradient(ellipse, rgba(245,158,11,0.18) 0%, transparent 65%)',
                        transform: 'rotateX(45deg)',
                        filter: 'blur(12px)',
                      }}
                    />
                  </div>
                </div>

                {/* HUD overlays */}
                <div className="absolute top-3 left-3 flex flex-col gap-1.5">
                  {[
                    { label: 'Altitude',   val: '48.2 m' },
                    { label: 'Points',     val: '2.4M' },
                    { label: 'Coverage',   val: '94%' },
                  ].map(({ label, val }) => (
                    <div
                      key={label}
                      className="flex items-center gap-2 px-2.5 py-1 rounded text-[10px] font-mono"
                      style={{ background: 'rgba(0,0,0,0.75)', border: '1px solid rgba(255,255,255,0.08)', backdropFilter: 'blur(4px)' }}
                    >
                      <span style={{ color: '#555' }}>{label}</span>
                      <span style={{ color: '#f59e0b' }}>{val}</span>
                    </div>
                  ))}
                </div>

                <div
                  className="absolute bottom-3 right-3 text-[10px] font-mono px-2.5 py-1 rounded"
                  style={{ background: 'rgba(245,158,11,0.12)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}
                >
                  ● processing step 4/7
                </div>
              </div>

              {/* Pipeline strip below viewport */}
              <div
                className="flex items-center gap-3 px-4 py-3 font-mono text-[11px] overflow-x-auto"
                style={{ background: '#0d0d0d', borderTop: '1px solid rgba(255,255,255,0.05)' }}
              >
                {[
                  { label: 'extract', done: true },
                  { label: 'filter',  done: true },
                  { label: 'match',   done: true },
                  { label: 'solve',   done: false, active: true },
                  { label: 'mesh',    done: false },
                  { label: 'export',  done: false },
                ].map(({ label, done, active }) => (
                  <span
                    key={label}
                    className="flex items-center gap-1.5 shrink-0"
                    style={{ color: done ? '#f59e0b' : active ? '#f5f5f5' : '#333' }}
                  >
                    <span>{done ? '✓' : active ? '▶' : '○'}</span>
                    <span>{label}</span>
                    {label !== 'export' && <span style={{ color: '#2a2a2a' }}>—</span>}
                  </span>
                ))}
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ─── Three honest facts ──────────────────────────────── */}
      <section className="py-20 border-t" style={{ background: '#0d0d0d', borderColor: 'rgba(255,255,255,0.05)' }}>
        <div className="max-w-6xl mx-auto px-5 md:px-10">

          <div className="mb-12">
            <h2 className="text-[28px] md:text-[38px] font-black text-white leading-tight mb-3">
              What you actually get
            </h2>
            <p className="text-[15px] text-[#555] max-w-lg">
              Not a point cloud preview in a broken web viewer. A real textured 3D model you can orbit, download, and use.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-px" style={{ background: 'rgba(255,255,255,0.06)' }}>
            {[
              {
                n: '01',
                title: 'Sharp frames only',
                body: 'Every frame is scored for sharpness. Blurry shots from prop wash or fast pans are cut automatically — you don\'t need to pre-trim anything.',
              },
              {
                n: '02',
                title: 'Dense point cloud',
                body: 'Millions of 3D points computed via structure-from-motion. Bundle adjustment tightens camera poses before the mesh is generated.',
              },
              {
                n: '03',
                title: 'Browser-ready GLB',
                body: 'Spin it around right here. Or download and open in Blender, Unity, or any GIS tool. The file is yours.',
              },
            ].map(({ n, title, body }) => (
              <div
                key={n}
                className="flex flex-col gap-5 p-8 group transition-all"
                style={{ background: '#0d0d0d' }}
              >
                <span className="text-[11px] font-mono" style={{ color: '#f59e0b' }}>{n}</span>
                <div>
                  <h3 className="text-[18px] font-bold text-white mb-2">{title}</h3>
                  <p className="text-[13px] leading-[22px] text-[#555]">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────────────── */}
      <section className="py-24 border-t" style={{ background: '#090909', borderColor: 'rgba(255,255,255,0.05)' }}>
        <div className="max-w-2xl mx-auto px-5 flex flex-col items-center text-center gap-6">
          <h2 className="text-[32px] md:text-[42px] font-black text-white leading-tight">
            Have a drone video<br />sitting around?
          </h2>
          <p className="text-[15px] text-[#555] max-w-sm">
            Upload it and see what comes out. The pipeline usually takes a few minutes depending on length.
          </p>
          <button
            onClick={() => onNavigate('upload')}
            className="mt-2 flex items-center gap-2 px-7 py-3.5 rounded-lg text-[14px] font-bold text-black transition-all active:scale-[0.97] cursor-pointer"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)', boxShadow: '0 4px 24px rgba(245,158,11,0.28)' }}
          >
            <span className="material-symbols-outlined text-[18px]">upload</span>
            Let's go
          </button>
        </div>
      </section>

    </div>
  );
};
