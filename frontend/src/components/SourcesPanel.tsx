import React, { useState } from 'react';

interface SourcesPanelProps {
  isVisible: boolean;
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({ isVisible }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!isVisible) return null;

  return (
    <aside className="lg:col-span-4 flex flex-col gap-7 transition-all duration-300">
      <div className="bg-[#0D1420]/90 backdrop-blur-2xl rounded-3xl p-7 border border-[#3D8BFF]/15 shadow-[0_0_35px_-8px_rgba(61,139,255,0.1)] space-y-6" style={{ backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(61, 139, 255, 0.06) 0%, transparent 70%)' }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-accent-glow text-[22px] drop-shadow-[0_0_8px_rgba(107,168,255,0.5)]">hub</span>
            <h3 className="text-lg font-light text-text-primary tracking-tight">Validated Sources</h3>
          </div>
          <span className="px-3 py-1 rounded-full bg-primary/15 border border-[#3D8BFF]/25 text-accent-glow font-citation text-[11px] font-semibold shadow-[0_0_10px_rgba(61,139,255,0.2)] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-state-success shadow-[0_0_8px_#4ADE9E]"></span>
            18 Sources Verified
          </span>
        </div>
        
        <div className="p-4 rounded-2xl bg-surface-container/40 border border-[#3D8BFF]/10 space-y-3">
          <div className="flex items-center justify-between text-text-muted font-label-sm text-xs">
            <span className="uppercase tracking-wider text-[10px]">Corpus Composition</span>
            <span className="text-accent-glow font-mono text-[11px]">100% Peer-Reviewed</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="px-3 py-1 rounded-full bg-surface-elevated/80 border border-[#3D8BFF]/20 text-accent-glow font-citation text-[11px]">11 Academic</span>
            <span className="px-3 py-1 rounded-full bg-surface-elevated/80 border border-[#3D8BFF]/20 text-text-primary font-citation text-[11px]">4 National Labs</span>
            <span className="px-3 py-1 rounded-full bg-surface-elevated/80 border border-[#3D8BFF]/20 text-text-muted font-citation text-[11px]">3 Industry</span>
          </div>
        </div>
        
        <button 
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-surface-elevated/70 border border-[#3D8BFF]/25 hover:border-primary/50 text-text-primary hover:text-accent-glow transition-all font-label-md text-xs tracking-wider shadow-[0_0_15px_rgba(61,139,255,0.1)] group"
        >
          <span className={`material-symbols-outlined text-[18px] text-accent-glow transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>expand_more</span>
          <span>{isExpanded ? 'Collapse citation index' : 'Expand all 18 sources & citations'}</span>
        </button>
        
        {isExpanded && (
          <div className="flex flex-col gap-4 max-h-[580px] overflow-y-auto pr-1 pt-2 border-t border-[#3D8BFF]/15 transition-all duration-300">
            <SourceCard 
              id="1" 
              title="Elastic strain energy and dendrite propagation in cubic LLZO garnets"
              journal="Nature Energy • 2023"
              score="0.98"
              doi="doi:10.1038/s41560-023-01284-x"
            />
            <SourceCard 
              id="2" 
              title="Battery Performance Database Cycle Testing Report #89"
              journal="Argonne Nat. Lab • 2024"
              score="0.99"
              doi="ANL-ESD-24-89"
              isInternal={true}
            />
            <SourceCard 
              id="3" 
              title="Grain boundary dopants for lithium dendrite suppression"
              journal="MIT Materials Bulletin • 2023"
              score="0.95"
              doi="doi:10.1557/s43577-023-00512"
            />
            <SourceCard 
              id="4" 
              title="Thermal runaway risks in solid-state pouch cells under fast charging"
              journal="IEEE Trans. Transport • 2024"
              score="0.96"
              doi="doi:10.1109/TTE.2024.3382910"
            />
          </div>
        )}
        
        <div className="p-5 bg-surface-container/50 rounded-2xl border border-[#3D8BFF]/15 text-text-muted space-y-3">
          <div className="flex items-center justify-between font-citation text-[11px]">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-accent-glow shadow-[0_0_8px_#6BA8FF]"></span>
              Citation Graph Ingestion
            </span>
            <span className="text-accent-glow font-medium">100% verified</span>
          </div>
          <div className="w-full bg-surface-container/70 h-1.5 rounded-full overflow-hidden p-0.5">
            <div className="bg-gradient-to-r from-primary via-[#569AFF] to-accent-glow h-full w-full rounded-full shadow-[0_0_12px_rgba(61,139,255,0.6)]"></div>
          </div>
          <p className="font-citation text-[10.5px] text-text-muted/80 leading-relaxed">
            All 18 references continuously queried against arXiv, DOE, and crossref registries for updates.
          </p>
        </div>
      </div>
    </aside>
  );
};

const SourceCard = ({ id, title, journal, score, doi, isInternal }: any) => (
  <div className="source-card bg-gradient-to-b from-surface-card/95 to-[#0A101A]/95 hover:from-surface-elevated/95 hover:to-surface-card/95 border border-[#3D8BFF]/15 hover:border-[#3D8BFF]/40 transition-all rounded-2xl p-5 shadow-[0_0_24px_-6px_rgba(61,139,255,0.08)] space-y-2 relative overflow-hidden group">
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="w-5 h-5 rounded-full bg-primary/20 border border-[#3D8BFF]/35 text-accent-glow font-citation text-[10px] flex items-center justify-center font-bold">[{id}]</span>
        <span className="font-citation text-[11px] uppercase tracking-wider text-text-muted/80">{journal}</span>
      </div>
      <div className="flex items-center gap-1 text-state-success font-citation text-[11px] font-medium">
        <span className="material-symbols-outlined text-[13px]">verified</span>
        <span>{score}</span>
      </div>
    </div>
    <h4 className="font-body-sm text-[13px] text-text-primary font-normal group-hover:text-accent-glow transition-colors leading-snug">{title}</h4>
    <div className="flex items-center justify-between pt-2 border-t border-[#3D8BFF]/15">
      {isInternal ? (
        <span className="font-citation text-[10.5px] text-text-muted font-mono">{doi}</span>
      ) : (
        <a href="#" className="font-citation text-[10.5px] text-accent-glow hover:underline flex items-center gap-1 font-mono">
          <span>{doi}</span>
          <span className="material-symbols-outlined text-[11px]">open_in_new</span>
        </a>
      )}
      <button className="px-2.5 py-0.5 rounded-full bg-surface-container/80 border border-[#3D8BFF]/20 font-citation text-[10px] text-text-muted hover:text-text-primary transition-colors">Snippet</button>
    </div>
  </div>
);
