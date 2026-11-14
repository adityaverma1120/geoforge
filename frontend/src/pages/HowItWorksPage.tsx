import React from 'react';

interface HowItWorksPageProps {
  onNavigate: (route: string) => void;
}

const STEPS = [
  {
    n: '01',
    title: 'Drop your video',
    body: 'Upload any drone footage — MP4, MOV, or AVI. No prep needed. We accept 1080p, 4K, whatever your drone shot.',
    note: 'Tip: slow, overlapping flight paths give better results than rapid sweeps.',
  },
  {
    n: '02',
    title: 'Bad frames get cut',
    body: 'Every frame is scored for sharpness. Blurry frames from prop wash, fast pans, or hovering are dropped so they don\'t corrupt the reconstruction.',
    note: 'Uses Laplacian variance scoring — the same technique professional photogrammetry tools use.',
  },
  {
    n: '03',
    title: 'Camera positions are solved',
    body: 'Feature keypoints (SIFT/ORB) are matched across hundreds of overlapping frames. From those matches, the pipeline works out exactly where the camera was at every moment.',
    note: 'Bundle adjustment tightens everything — camera positions, focal length, lens distortion.',
  },
  {
    n: '04',
    title: 'Depth maps become a mesh',
    body: 'Once cameras are placed, dense stereo matching fills in a point cloud with millions of 3D points. Those points get surfaced into a watertight polygonal mesh.',
    note: 'Screened Poisson reconstruction + automatic UV unwrapping for photo textures.',
  },
  {
    n: '05',
    title: 'You get an interactive model',
    body: 'The finished model opens right in the browser — orbit it, zoom in, inspect details. Download the GLB for Blender or OBJ/LAS for GIS tools.',
    note: 'No plugins, no GPU on your side. Runs in WebGL.',
  },
];

export const HowItWorksPage: React.FC<HowItWorksPageProps> = ({ onNavigate }) => {
  return (
    <div className="flex-1 flex flex-col w-full" style={{ background: '#090909' }}>
      <div className="max-w-2xl mx-auto px-5 md:px-10 py-16 md:py-24 w-full">

        {/* Back */}
        <button
          onClick={() => onNavigate('home')}
          className="flex items-center gap-1.5 text-[12px] font-mono mb-10 transition-colors cursor-pointer"
          style={{ color: '#555' }}
          onMouseEnter={e => (e.currentTarget.style.color = '#f0f0f0')}
          onMouseLeave={e => (e.currentTarget.style.color = '#555')}
        >
          <span className="material-symbols-outlined text-[15px]">arrow_back</span>
          Back
        </button>

        {/* Heading */}
        <div className="mb-16">
          <h1 className="text-[36px] md:text-[50px] font-black text-white leading-tight mb-4">
            How it works
          </h1>
          <p className="text-[15px] leading-[26px]" style={{ color: '#666' }}>
            Five stages, fully automated. Here's what actually happens between
            you hitting upload and seeing your 3D model.
          </p>
        </div>

        {/* Steps */}
        <div className="flex flex-col">
          {STEPS.map((step, i) => (
            <div
              key={step.n}
              className="flex gap-6 pb-12"
              style={{ borderLeft: `1px solid ${i === STEPS.length - 1 ? 'transparent' : 'rgba(255,255,255,0.07)'}`, paddingLeft: '28px', marginLeft: '10px', position: 'relative' }}
            >
              {/* Node */}
              <div
                className="absolute flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold font-mono"
                style={{
                  left: '-10px',
                  top: '2px',
                  background: '#090909',
                  border: '1.5px solid #f59e0b',
                  color: '#f59e0b',
                }}
              >
                {i + 1}
              </div>

              <div className="flex flex-col gap-3 flex-1">
                <div className="flex items-baseline gap-3">
                  <span className="text-[11px] font-mono" style={{ color: '#f59e0b' }}>{step.n}</span>
                  <h2 className="text-[18px] font-bold text-white">{step.title}</h2>
                </div>

                <p className="text-[14px] leading-[24px]" style={{ color: '#777' }}>{step.body}</p>

                <p
                  className="text-[12px] leading-[20px] pl-3"
                  style={{ borderLeft: '2px solid rgba(245,158,11,0.3)', color: '#555' }}
                >
                  {step.note}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-4 pt-10 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <p className="text-[13px] mb-4" style={{ color: '#555' }}>Ready to try it?</p>
          <button
            onClick={() => onNavigate('upload')}
            className="flex items-center gap-2 px-6 py-3 rounded-lg text-[14px] font-bold text-black transition-all active:scale-[0.97] cursor-pointer"
            style={{ background: 'linear-gradient(135deg,#f59e0b,#d97706)', boxShadow: '0 4px 20px rgba(245,158,11,0.25)' }}
          >
            <span className="material-symbols-outlined text-[17px]">upload</span>
            Upload a video
          </button>
        </div>

      </div>
    </div>
  );
};
