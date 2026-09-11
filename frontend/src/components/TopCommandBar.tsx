import React, { useState } from 'react';

interface TopCommandBarProps {
  onToggleDrawer: () => void;
}

export const TopCommandBar: React.FC<TopCommandBarProps> = ({ onToggleDrawer }) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'deepdive'>('summary');

  return (
    <div className="w-full bg-[#0D1420]/90 backdrop-blur-2xl rounded-3xl p-12 mb-12 relative overflow-hidden border border-[#3D8BFF]/15 shadow-[0_0_45px_-10px_rgba(61,139,255,0.12)]" style={{ backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(61, 139, 255, 0.08) 0%, transparent 70%)' }}>
      <div className="absolute -right-24 -top-24 w-96 h-96 bg-[#3D8BFF]/12 rounded-full blur-[110px] pointer-events-none"></div>
      <div className="absolute -left-20 -bottom-20 w-80 h-80 bg-[#6BA8FF]/8 rounded-full blur-[100px] pointer-events-none"></div>
      
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-10 relative z-10">
        <div className="space-y-5 max-w-4xl">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-2 border-b border-[#3D8BFF]/15">
            <div className="inline-flex items-center p-1 rounded-xl bg-surface-container/70 border border-[#3D8BFF]/20 shadow-[0_0_15px_rgba(61,139,255,0.1)]">
              <button 
                className={`px-4 py-1.5 rounded-lg font-label-md text-xs tracking-wider transition-all duration-200 font-medium flex items-center gap-1.5 ${
                  activeTab === 'summary' 
                    ? 'bg-primary text-white shadow-[0_0_12px_rgba(61,139,255,0.5)]' 
                    : 'text-text-muted hover:text-accent-glow hover:bg-surface-elevated/60'
                }`}
                onClick={() => setActiveTab('summary')}
              >
                <span className="material-symbols-outlined text-[15px]">subject</span>
                <span>Summary</span>
              </button>
              <button 
                className={`px-4 py-1.5 rounded-lg font-label-md text-xs tracking-wider transition-all duration-200 font-medium flex items-center gap-1.5 ${
                  activeTab === 'deepdive' 
                    ? 'bg-primary text-white shadow-[0_0_12px_rgba(61,139,255,0.5)]' 
                    : 'text-text-muted hover:text-accent-glow hover:bg-surface-elevated/60'
                }`}
                onClick={() => setActiveTab('deepdive')}
              >
                <span className="material-symbols-outlined text-[15px]">analytics</span>
                <span>Deep Dive</span>
              </button>
            </div>
            
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-surface-elevated/60 border border-[#3D8BFF]/15">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-glow animate-pulse shadow-[0_0_8px_#6BA8FF]"></span>
              <span className="font-label-sm text-[11px] text-accent-glow/90 tracking-wide">Summary Mode · High-Level Synthesis</span>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-3.5">
            <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface-elevated/80 text-accent-glow font-citation text-[11px] tracking-widest uppercase border border-[#3D8BFF]/20 shadow-[0_0_15px_rgba(61,139,255,0.15)]">
              <span className="w-1.5 h-1.5 rounded-full bg-state-success animate-pulse shadow-[0_0_8px_#4ADE9E]"></span>
              Peer-Synthesized Report #8094
            </span>
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-surface-container/60 border border-[#3D8BFF]/15 font-citation text-[11px] text-text-muted">
              <span className="material-symbols-outlined text-[14px] text-accent-glow">verified</span>
              Confidence: <strong className="text-text-primary font-normal">96.4%</strong>
            </span>
            <span className="font-citation text-[11px] text-text-muted/80 tracking-wide">Corpus: 42,100 Articles • Latency: 1.84s</span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-light text-text-primary tracking-tight leading-[1.2]">
            Micro-Cracking Dynamics in <span className="font-normal text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent-glow to-[#d8e6ff] drop-shadow-[0_0_24px_rgba(61,139,255,0.4)]">LLZO Solid-State</span> Electrolytes Under 4C+ Fast Charging
          </h1>
          
          <div className="flex flex-wrap items-center gap-5 text-text-muted font-label-sm text-[12px] pt-2">
            <span>Synthesized by <span className="text-text-primary font-medium tracking-wide">A.L.I.E. v2.4</span></span>
            <span className="text-border-strong">•</span>
            <span>October 24, 2024 • 14:32 UTC</span>
            <span className="text-border-strong">•</span>
            <span className="text-state-success flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">verified</span>
              <span className="tracking-wide">Fully Verifiable Artifact</span>
            </span>
          </div>
        </div>
        
        <div className="flex items-center flex-wrap gap-3.5 shrink-0 pt-3">
          <button 
            onClick={onToggleDrawer}
            className="flex items-center gap-2 px-4.5 h-11 rounded-xl bg-surface-elevated/60 border border-[#3D8BFF]/15 text-text-primary hover:border-primary/40 hover:bg-surface-elevated transition-all font-label-md text-[12px]"
          >
            <span className="material-symbols-outlined text-[18px] text-accent-glow">dock_to_left</span>
            <span className="hidden sm:inline">Sources Panel</span>
          </button>
          <button className="flex items-center gap-2 px-4.5 h-11 rounded-xl bg-surface-elevated/60 border border-[#3D8BFF]/15 text-text-primary hover:border-primary/40 hover:bg-surface-elevated transition-all font-label-md text-[12px]">
            <span className="material-symbols-outlined text-[18px] text-text-muted">code_blocks</span>
            <span className="hidden sm:inline">Markdown / JSON</span>
          </button>
          <button className="flex items-center gap-2 px-4.5 h-11 rounded-xl bg-surface-elevated/60 border border-[#3D8BFF]/15 text-text-primary hover:border-primary/40 hover:bg-surface-elevated transition-all font-label-md text-[12px]">
            <span className="material-symbols-outlined text-[18px] text-text-muted">share</span>
            <span>Share</span>
          </button>
          <button className="flex items-center gap-2.5 px-7 h-11 rounded-xl bg-gradient-to-r from-[#3D8BFF] via-[#569AFF] to-[#6BA8FF] text-white font-semibold transition-all hover:scale-[1.02] shadow-[0_0_24px_rgba(61,139,255,0.45)] hover:shadow-[0_0_36px_rgba(107,168,255,0.6)]">
            <span className="material-symbols-outlined text-[18px]">picture_as_pdf</span>
            <span className="font-label-md text-[12px] tracking-wider uppercase">Export PDF</span>
          </button>
        </div>
      </div>
    </div>
  );
};
