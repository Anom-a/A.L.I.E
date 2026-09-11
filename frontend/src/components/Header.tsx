import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="fixed top-0 left-72 right-0 h-16 bg-[#05070D]/85 backdrop-blur-2xl border-b border-[#3D8BFF]/10 z-30 flex items-center justify-between px-gutter">
      <div className="flex items-center gap-space-md">
        <img
          alt="A.L.I.E. Blue Neural Emblem"
          className="h-8 w-8 object-contain drop-shadow-[0_0_8px_rgba(61,139,255,0.5)]"
          src="https://lh3.googleusercontent.com/aida/AEtjO1VFpdCX5P83H3-nNIsGoAFe9DIPuLBX9wNfKLp4JRO0J77OOff0SD_GEg9qD32lL29qh4Ww7cCDy_guT75BXCTm5XjbWaq24IJJ5L73nrT1nD9l7V6kPUbtw-wI0r_evgc_m_H-iupEr_1gDmYnncX0eHjOMal_xoNzvlaxUZoBG7Fid9UNUOVPEM2dDtFUnctvBCYr1hqPkPj1xj4A4kUu5JFLP2B1v3JCvVYyU8Zhu3L_Y9vksRDqqA"
        />
        <div className="flex items-center gap-space-xs font-label-md text-label-md">
          <span className="text-text-muted/70 tracking-wider text-[11px] uppercase">Emulator</span>
          <span className="text-border-strong/60">/</span>
          <span className="text-primary flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary inline-block shadow-[0_0_8px_#3D8BFF]"></span>
            <span className="tracking-wide text-accent-glow font-medium">Active Node Alpha</span>
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-space-lg">
        <div className="hidden md:flex items-center gap-space-sm px-space-md py-2 bg-surface-elevated/40 border border-[#3D8BFF]/15 rounded-full text-text-muted focus-within:border-primary/50 focus-within:shadow-[0_0_20px_rgba(61,139,255,0.2)] transition-all">
          <span className="material-symbols-outlined text-[16px] text-accent-glow/80">search</span>
          <span className="font-label-sm text-label-sm text-text-muted/70">Search corpus, citations, or symbols...</span>
          <kbd className="font-citation text-citation px-2 py-0.5 rounded-full bg-surface-container/80 border border-border-strong/40 text-text-muted/80 text-[10px]">⌘K</kbd>
        </div>
        
        <div className="flex items-center gap-space-md border-l border-[#3D8BFF]/10 pl-space-md">
          <div className="flex items-center gap-2 text-text-muted font-label-sm text-label-sm">
            <span className="material-symbols-outlined text-[18px] text-primary drop-shadow-[0_0_8px_rgba(61,139,255,0.6)]">memory</span>
            <span className="tracking-wider text-text-primary/90 font-mono text-[11px]">72% FLOPs</span>
          </div>
          <button className="text-text-muted hover:text-text-primary hover:bg-surface-elevated/60 p-2 rounded-xl transition-all">
            <span className="material-symbols-outlined text-[19px]">tune</span>
          </button>
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#3D8BFF] to-[#6BA8FF] flex items-center justify-center shadow-[0_0_14px_rgba(61,139,255,0.5)]">
            <span className="material-symbols-outlined text-white text-[18px] font-semibold">person</span>
          </div>
        </div>
      </div>
    </header>
  );
};
