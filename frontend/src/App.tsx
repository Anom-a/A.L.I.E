import { useState, useEffect, useRef } from 'react';
import { ChatInput } from './components/ChatInput';
import { ChatWindow } from './components/ChatWindow';
import { JobStatusResponse, ChatMessage } from './types';

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const pollInterval = useRef<number | null>(null);

  const startResearch = async (topic: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: topic,
    };
    
    const assistantMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '', // Empty initially, will show loading
      status: 'PENDING',
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
      });

      if (!response.ok) {
        throw new Error(`Failed to start research: ${response.statusText}`);
      }

      const data: JobStatusResponse = await response.json();
      setActiveJobId(data.job_id);
      
      // Update assistant message with job id (invisible, just for tracking)
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessage.id 
          ? { ...msg, status: data.status, jobId: data.job_id } 
          : msg
      ));
    } catch (err: any) {
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessage.id 
          ? { ...msg, status: 'FAILED', error: err.message } 
          : msg
      ));
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!activeJobId) return;

    // Find the message associated with this active job
    const assistantMessage = messages.find(m => m.role === 'assistant' && (m as any).jobId === activeJobId);
    if (!assistantMessage) return;

    if (assistantMessage.status === 'DONE' || assistantMessage.status === 'FAILED') {
      if (pollInterval.current) {
        window.clearInterval(pollInterval.current);
        pollInterval.current = null;
      }
      
      if (assistantMessage.status === 'DONE' && !assistantMessage.report) {
        // Fetch report
        fetch(`/api/research/${activeJobId}/report`)
          .then(res => res.json())
          .then(data => {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessage.id 
                ? { ...msg, report: data, content: 'Research complete.' } 
                : msg
            ));
            setIsLoading(false);
            setActiveJobId(null); // Clear active job so we can start a new one
          })
          .catch(err => {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessage.id 
                ? { ...msg, error: 'Failed to fetch report', status: 'FAILED' } 
                : msg
            ));
            setIsLoading(false);
            setActiveJobId(null);
          });
      } else if (assistantMessage.status === 'FAILED') {
        setIsLoading(false);
        setActiveJobId(null);
      }
      return;
    }

    const poll = async () => {
      try {
        const response = await fetch(`/api/research/${activeJobId}`);
        if (response.ok) {
          const data: JobStatusResponse = await response.json();
          
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessage.id 
              ? { ...msg, status: data.status, error: data.error || msg.error } 
              : msg
          ));
        }
      } catch (err) {
        console.error("Poll failed", err);
      }
    };

    pollInterval.current = window.setInterval(poll, 2000);
    return () => {
      if (pollInterval.current) window.clearInterval(pollInterval.current);
    };
  }, [activeJobId, messages]);

  return (
    <div className="flex flex-col h-screen bg-canvas-base text-on-surface overflow-hidden relative">
      {/* Background Decorative Effects */}
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
        <div className="absolute -top-[20%] left-1/4 w-[850px] h-[850px] rounded-full blur-[160px] opacity-25 pointer-events-none" style={{ background: 'radial-gradient(circle, #3D8BFF 0%, rgba(107, 168, 255, 0.08) 50%, transparent 70%)' }}></div>
        <div className="absolute top-[40%] -right-[15%] w-[700px] h-[700px] rounded-full blur-[150px] opacity-20 pointer-events-none" style={{ background: 'radial-gradient(circle, #1a4f9e 0%, transparent 65%)' }}></div>
        <div className="absolute bottom-[-10%] left-[10%] w-[600px] h-[600px] rounded-full blur-[140px] opacity-15 pointer-events-none" style={{ background: 'radial-gradient(circle, #2463eb 0%, transparent 65%)' }}></div>
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(rgba(61, 139, 255, 0.6) 1px, transparent 1px)', backgroundSize: '36px 36px' }}></div>
      </div>
      
      <ChatWindow messages={messages} isLoading={isLoading} />
      <ChatInput onSubmit={startResearch} isLoading={isLoading} />
    </div>
  );
}
