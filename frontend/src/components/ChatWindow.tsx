import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../types';
import { Core3D } from './Core3D';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

const CitePill: React.FC<{ id: string }> = ({ id }) => (
  <button className="inline-flex items-center justify-center font-citation text-citation px-2.5 py-0.5 rounded-full bg-surface-container/90 border border-[#3D8BFF]/25 hover:bg-primary hover:text-white text-accent-glow transition-colors mx-0.5">
    [{id}]
  </button>
);

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 w-full max-w-5xl mx-auto overflow-y-auto px-4 py-8 space-y-8 scrollbar-hide z-10 flex flex-col pt-12">
      {messages.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center text-center m-auto pb-32 w-full max-w-lg relative">
          <div className="h-48 sm:h-64 w-full mb-6 sm:mb-8 relative z-10">
            <Core3D />
          </div>
          <h2 className="text-4xl sm:text-5xl font-headline-xl font-bold tracking-tight text-white mb-2 sm:mb-3 drop-shadow-[0_0_25px_rgba(61,139,255,0.8)] relative z-10" style={{ textShadow: '0 0 15px rgba(6,182,212,0.6)' }}>
            A.L.I.E.
          </h2>
          <p className="font-label-md text-label-md uppercase tracking-[0.15em] sm:tracking-[0.3em] text-accent-glow font-medium drop-shadow-[0_0_10px_rgba(61,139,255,0.5)] relative z-10 px-2 text-center leading-relaxed">
            Advanced Lucent Intelligence Emulator
          </p>
          
          {/* Subtle background flair for empty state */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full rounded-full bg-primary/5 blur-[100px] pointer-events-none z-0"></div>
        </div>
      )}

      {messages.map((msg) => (
        <div key={msg.id} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[85%] rounded-2xl p-6 ${
            msg.role === 'user' 
              ? 'bg-surface-elevated border border-[#3D8BFF]/20 text-text-primary rounded-tr-sm shadow-[0_0_20px_rgba(61,139,255,0.08)]'
              : 'bg-[#0D1420]/80 backdrop-blur-xl border border-[#3D8BFF]/15 text-text-primary rounded-tl-sm shadow-[0_0_30px_rgba(61,139,255,0.05)]'
          }`}>
            {msg.role === 'assistant' && (
              <div className="flex items-center gap-3 mb-4 border-b border-[#3D8BFF]/10 pb-3">
                <span className="material-symbols-outlined text-accent-glow text-xl">psychology</span>
                <span className="font-label-sm text-[11px] uppercase tracking-widest text-text-muted">A.L.I.E. Synthesis</span>
              </div>
            )}
            
            <div className="font-body-lg text-[16px] leading-[28px] font-light whitespace-pre-wrap">
              {msg.content}
            </div>

            {msg.error && (
              <div className="mt-4 p-4 rounded-xl bg-state-error/10 border border-state-error/20 flex items-start gap-3">
                <span className="material-symbols-outlined text-state-error">error</span>
                <p className="text-state-error/90 text-sm">{msg.error}</p>
              </div>
            )}

            {msg.status && msg.status !== 'done' && msg.status !== 'failed' && (
              <div className="mt-4 flex items-center gap-3 text-accent-glow animate-pulse">
                <span className="material-symbols-outlined animate-spin text-[18px]">refresh</span>
                <span className="font-label-sm text-sm tracking-wide">
                  {msg.status === 'pending' && 'Initializing Research...'}
                  {msg.status === 'running' && 'Researching...'}
                </span>
              </div>
            )}

            {msg.report && msg.report.sections && (
              <div className="mt-6 space-y-6">
                {msg.report.sections.map((section, idx) => (
                  <div key={idx} className="bg-surface-elevated/40 rounded-xl p-6 border border-[#3D8BFF]/10">
                    <h3 className="font-label-md text-label-md uppercase tracking-widest text-accent-glow font-semibold mb-4">{section.title}</h3>
                    <p className="font-body-lg text-[16px] text-text-primary/90 leading-[28px] font-light whitespace-pre-wrap mb-4">
                      {section.content}
                    </p>
                    {section.citation_ids && section.citation_ids.length > 0 && (
                      <div className="pt-4 border-t border-[#3D8BFF]/10 flex flex-wrap gap-2">
                        <span className="font-label-sm text-[11px] text-text-muted uppercase tracking-wider mr-2 my-auto">Citations:</span>
                        {section.citation_ids.map(cid => <CitePill key={cid} id={cid.substring(0, 8)} />)}
                      </div>
                    )}
                  </div>
                ))}

                {msg.report.citations && msg.report.citations.length > 0 && (
                  <div className="mt-8 pt-6 border-t border-[#3D8BFF]/15">
                    <h4 className="font-headline-sm text-sm text-text-primary mb-4 font-medium">All References</h4>
                    <div className="space-y-3">
                      {msg.report.citations.map((cite, idx) => (
                        <div key={idx} className="bg-surface-container/50 p-3 rounded-lg border border-[#3D8BFF]/10 text-xs flex flex-col gap-1">
                          <div className="flex items-start justify-between text-text-muted">
                            <span className="text-accent-glow/80 font-mono break-all">{cite.source_url_or_id}</span>
                            <span className="whitespace-nowrap ml-4">Retrieved: {new Date(cite.retrieved_at).toLocaleDateString()}</span>
                          </div>
                          <div className="text-secondary font-medium">{cite.source_name}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} className="h-4" />
    </div>
  );
};
