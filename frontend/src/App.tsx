import { useState, useEffect, useRef } from 'react';
import { ChatInput } from './components/ChatInput';
import { ChatWindow } from './components/ChatWindow';
import { JobStatusResponse, ChatMessage } from './types';
import AntigravityLoader from './components/AntigravityLoader';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export default function App() {
  const [isInitializing, setIsInitializing] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const pollInterval = useRef<number | null>(null);

  useEffect(() => {
    // Simulate initial A.L.I.E. loading sequence (matches loader's online status)
    const timer = setTimeout(() => setIsInitializing(false), 9500);
    return () => clearTimeout(timer);
  }, []);

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
      status: 'pending',
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/research`, {
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
          ? { ...msg, status: 'failed', error: err.message } 
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

    if (assistantMessage.status === 'done' || assistantMessage.status === 'failed') {
      if (pollInterval.current) {
        window.clearInterval(pollInterval.current);
        pollInterval.current = null;
      }
      
      if (assistantMessage.status === 'done' && !assistantMessage.report) {
        // Fetch report
        fetch(`${API_BASE_URL}/research/${activeJobId}/report`)
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
                ? { ...msg, error: 'Failed to fetch report', status: 'failed' } 
                : msg
            ));
            setIsLoading(false);
            setActiveJobId(null);
          });
      } else if (assistantMessage.status === 'failed') {
        setIsLoading(false);
        setActiveJobId(null);
      }
      return;
    }

    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/research/${activeJobId}`);
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

  if (isInitializing) {
    return <AntigravityLoader />;
  }

  return (
    <div className="flex flex-col h-screen bg-canvas-base text-on-surface overflow-hidden relative">
      {/* Background Decorative Effects */}
      <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden bg-[#020408]">
        <style>{`
          @keyframes gridMove {
            0% { background-position: 0 0; }
            100% { background-position: 0 40px; }
          }
          @keyframes floatParticle {
            0% { transform: translateY(0) translateX(0) scale(1); opacity: 0; }
            20% { opacity: 0.5; }
            80% { opacity: 0.5; }
            100% { transform: translateY(-100vh) translateX(50px) scale(0.5); opacity: 0; }
          }
        `}</style>
        
        {/* Deep space radial gradients */}
        <div className="absolute -top-[20%] left-1/4 w-[850px] h-[850px] rounded-full blur-[160px] opacity-30" style={{ background: 'radial-gradient(circle, #06B6D4 0%, transparent 70%)' }}></div>
        <div className="absolute top-[40%] -right-[15%] w-[700px] h-[700px] rounded-full blur-[150px] opacity-20" style={{ background: 'radial-gradient(circle, #3D8BFF 0%, transparent 65%)' }}></div>
        <div className="absolute bottom-[-10%] left-[10%] w-[600px] h-[600px] rounded-full blur-[140px] opacity-20" style={{ background: 'radial-gradient(circle, #6BA8FF 0%, transparent 65%)' }}></div>
        
        {/* Cyberpunk Grid */}
        <div className="absolute inset-0 overflow-hidden">
          <div 
            className="absolute inset-[-100%] opacity-[0.12]" 
            style={{ 
              backgroundImage: 'linear-gradient(rgba(6,182,212,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.4) 1px, transparent 1px)', 
              backgroundSize: '40px 40px',
              transform: 'perspective(500px) rotateX(60deg) translateY(-100px) translateZ(-200px)',
              animation: 'gridMove 2s linear infinite'
            }}
          ></div>
        </div>

        {/* Floating particles */}
        {Array.from({ length: 30 }).map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-[#06B6D4] blur-[1px]"
            style={{
              width: Math.random() * 3 + 1 + 'px',
              height: Math.random() * 3 + 1 + 'px',
              left: Math.random() * 100 + '%',
              top: Math.random() * 100 + 100 + '%',
              animation: `floatParticle ${Math.random() * 15 + 10}s linear infinite`,
              animationDelay: `-${Math.random() * 25}s`,
              opacity: 0
            }}
          />
        ))}
      </div>
      
      <ChatWindow messages={messages} isLoading={isLoading} />
      <ChatInput onSubmit={startResearch} isLoading={isLoading} />
    </div>
  );
}
