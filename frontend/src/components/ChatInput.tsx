import React, { useState } from 'react';

interface ChatInputProps {
  onSubmit: (topic: string) => void;
  isLoading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto mt-auto pb-8 pt-4 bg-transparent px-4 flex-shrink-0 z-20">
      <form 
        onSubmit={handleSubmit}
        className="relative flex items-center bg-[#05070D]/60 backdrop-blur-3xl border border-[#06B6D4]/30 rounded-2xl shadow-[0_8px_32px_0_rgba(6,182,212,0.15)] focus-within:border-[#06B6D4]/70 focus-within:shadow-[0_0_40px_rgba(6,182,212,0.35)] transition-all p-2 gap-2"
      >
        <textarea
          className="flex-1 bg-transparent border-none outline-none text-[#F2F6FC] text-[15px] font-light placeholder:text-[#6BA8FF]/40 resize-none max-h-32 min-h-[50px] py-3 px-4 leading-relaxed scrollbar-hide drop-shadow-[0_0_8px_rgba(6,182,212,0.3)]"
          placeholder="Ask A.L.I.E. a research question..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="group h-[50px] px-6 rounded-xl bg-transparent border border-[#06B6D4]/80 text-[#06B6D4] font-medium tracking-widest uppercase shadow-[inset_0_0_15px_rgba(6,182,212,0.2),0_0_20px_rgba(6,182,212,0.3)] hover:bg-[#06B6D4]/15 hover:text-white hover:shadow-[inset_0_0_25px_rgba(6,182,212,0.5),0_0_35px_rgba(6,182,212,0.6)] disabled:opacity-30 disabled:hover:bg-transparent disabled:cursor-not-allowed transition-all duration-300 flex items-center gap-2 overflow-hidden relative"
        >
          {isLoading ? (
            <span className="material-symbols-outlined animate-spin text-[20px] drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]">refresh</span>
          ) : (
            <span className="material-symbols-outlined text-[20px] drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]">send</span>
          )}
          <span className="relative z-10 drop-shadow-[0_0_5px_rgba(6,182,212,0.8)]">Start Research</span>
        </button>
      </form>
    </div>
  );
};
