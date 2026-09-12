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
        className="relative flex items-center bg-surface-elevated/80 backdrop-blur-2xl border border-[#3D8BFF]/20 rounded-2xl shadow-[0_0_32px_-6px_rgba(61,139,255,0.15)] focus-within:border-primary/50 focus-within:shadow-[0_0_40px_-6px_rgba(61,139,255,0.25)] transition-all p-2 gap-2"
      >
        <textarea
          className="flex-1 bg-transparent border-none outline-none text-text-primary text-[15px] font-light placeholder:text-text-muted/60 resize-none max-h-32 min-h-[50px] py-3 px-4 leading-relaxed scrollbar-hide"
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
          className="h-[50px] px-6 rounded-xl bg-gradient-to-r from-primary to-accent-glow text-white font-medium tracking-wide shadow-[0_0_20px_rgba(61,139,255,0.3)] hover:shadow-[0_0_28px_rgba(107,168,255,0.5)] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          {isLoading ? (
            <span className="material-symbols-outlined animate-spin text-[20px]">refresh</span>
          ) : (
            <span className="material-symbols-outlined text-[20px]">send</span>
          )}
          Start Research
        </button>
      </form>
    </div>
  );
};
