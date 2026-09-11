import React from 'react';
import { NavItem, SessionItem } from '../types';

export const Sidebar: React.FC = () => {
  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-gradient-to-b from-[#080d16]/95 via-[#060912]/95 to-[#05070D]/98 backdrop-blur-2xl border-r border-[#3D8BFF]/10 z-40 flex flex-col justify-between select-none shadow-[8px_0_40px_rgba(0,0,0,0.6)]">
      <div className="flex flex-col flex-1 min-h-0">
        <div className="h-24 px-space-lg flex items-center gap-space-sm border-b border-[#3D8BFF]/10">
          <img
            alt="A.L.I.E. Blue Neural Emblem"
            className="h-10 w-10 object-contain drop-shadow-[0_0_12px_rgba(61,139,255,0.6)]"
            src="https://lh3.googleusercontent.com/aida/AEtjO1VFpdCX5P83H3-nNIsGoAFe9DIPuLBX9wNfKLp4JRO0J77OOff0SD_GEg9qD32lL29qh4Ww7cCDy_guT75BXCTm5XjbWaq24IJJ5L73nrT1nD9l7V6kPUbtw-wI0r_evgc_m_H-iupEr_1gDmYnncX0eHjOMal_xoNzvlaxUZoBG7Fid9UNUOVPEM2dDtFUnctvBCYr1hqPkPj1xj4A4kUu5JFLP2B1v3JCvVYyU8Zhu3L_Y9vksRDqqA"
          />
          <div className="flex flex-col">
            <span className="font-headline-sm text-headline-sm text-text-primary font-medium tracking-tight">A.L.I.E.</span>
            <span className="font-label-sm text-label-sm text-text-muted/90 tracking-wider">Lucent Emulator v2.4</span>
          </div>
        </div>
        
        <div className="p-space-md my-2">
          <button className="w-full flex items-center justify-center gap-space-sm h-12 px-space-md rounded-xl bg-gradient-to-r from-[#3D8BFF] via-[#569AFF] to-[#6BA8FF] text-white font-semibold shadow-[0_0_24px_rgba(61,139,255,0.4)] hover:shadow-[0_0_32px_rgba(107,168,255,0.6)] hover:scale-[1.01] transition-all duration-200">
            <span className="material-symbols-outlined text-[19px]">add</span>
            <span className="font-label-md text-label-md tracking-wider uppercase">New Inquiry</span>
          </button>
        </div>
        
        <nav className="px-space-sm space-y-1.5">
          <NavItem icon="account_tree" label="Active Pipelines" />
          <NavItem icon="auto_stories" label="Library & Reports" isActive={true} />
          <NavItem icon="hub" label="Sources & Graph" />
          <NavItem icon="neurology" label="Model Registry" />
        </nav>
        
        <div className="flex-1 flex flex-col min-h-0 mt-space-lg border-t border-[#3D8BFF]/10 pt-space-md px-space-sm">
          <div className="px-space-sm py-space-xs flex items-center justify-between mb-2">
            <span className="font-label-sm text-label-sm uppercase tracking-widest text-text-muted/80 text-[10px]">Research Sessions</span>
            <span className="font-label-sm text-label-sm text-outline/80 text-[10px]">Recent</span>
          </div>
          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            <SessionItem name="Quantum Decoupling L2" time="12m" status="active" />
            <SessionItem name="CRISPR Off-target Met..." time="1h" status="success" />
            <SessionItem name="LLM Hallucination Pr..." time="3h" status="pending" />
          </div>
        </div>
      </div>
      
      <div className="p-space-md border-t border-[#3D8BFF]/10 bg-surface-card/70 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-state-success shadow-[0_0_8px_#4ADE9E]"></span>
          <span className="font-label-sm text-label-sm text-text-muted tracking-wider uppercase text-[10px]">System Optimal</span>
        </div>
        <button className="text-text-muted hover:text-primary transition-colors">
          <span className="material-symbols-outlined text-[18px]">terminal</span>
        </button>
      </div>
    </aside>
  );
};

const NavItem: React.FC<NavItem> = ({ icon, label, isActive }) => {
  if (isActive) {
    return (
      <a href="#" className="flex items-center gap-space-sm px-space-md py-3 rounded-xl transition-all bg-gradient-to-r from-surface-elevated to-surface-card/80 text-primary font-medium border border-primary/25 shadow-[0_0_20px_rgba(61,139,255,0.15)]">
        <span className="material-symbols-outlined text-[20px] text-accent-glow drop-shadow-[0_0_8px_rgba(107,168,255,0.6)]">{icon}</span>
        <span className="font-body-sm text-body-sm tracking-wide text-white">{label}</span>
      </a>
    );
  }
  return (
    <a href="#" className="flex items-center gap-space-sm px-space-md py-3 rounded-xl text-secondary/70 hover:bg-surface-elevated/60 hover:text-text-primary transition-all">
      <span className="material-symbols-outlined text-[20px]">{icon}</span>
      <span className="font-body-sm text-body-sm">{label}</span>
    </a>
  );
};

const SessionItem: React.FC<SessionItem> = ({ name, time, status }) => {
  const statusColors = {
    active: 'bg-accent-glow shadow-[0_0_8px_#6BA8FF] animate-pulse',
    success: 'bg-state-success shadow-[0_0_8px_#4ADE9E]',
    pending: 'bg-state-pending'
  };

  return (
    <a href="#" className="group flex items-center justify-between px-space-sm py-2.5 rounded-lg text-text-muted/80 hover:bg-surface-elevated/60 hover:text-text-primary transition-all">
      <div className="flex items-center gap-2.5 truncate">
        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${statusColors[status]}`}></span>
        <span className="font-label-sm text-label-sm truncate">{name}</span>
      </div>
      <span className="font-citation text-citation text-text-muted/60 group-hover:text-primary">{time}</span>
    </a>
  );
};
