import React, { useState, useEffect, useRef } from 'react';
import { ChatInput } from '../components/ChatInput';
import { ChatWindow } from '../components/ChatWindow';
import { JobStatusResponse, ChatMessage } from '../types';
import AntigravityLoader from '../components/AntigravityLoader';
import { useAuth } from '../contexts/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const Chat: React.FC = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const pollInterval = useRef<number | null>(null);
  const { token, logout } = useAuth();

  useEffect(() => {
    // Simulate initial A.L.I.E. loading sequence (matches loader's online status)
    const timer = setTimeout(() => setIsInitializing(false), 9500);
    return () => clearTimeout(timer);
  }, []);

  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };
    
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
      logout();
      throw new Error('Unauthorized');
    }
    return response;
  };

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
      const response = await fetchWithAuth(`${API_BASE_URL}/research`, {
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
        fetchWithAuth(`${API_BASE_URL}/research/${activeJobId}/report`)
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
        const response = await fetchWithAuth(`${API_BASE_URL}/research/${activeJobId}`);
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
  }, [activeJobId, messages, token, logout]);

  if (isInitializing) {
    return <AntigravityLoader />;
  }

  return (
    <>
      <div className="absolute top-4 right-4 z-50">
        <button 
          onClick={logout}
          className="text-cyan-500/70 hover:text-cyan-400 text-sm font-medium transition-colors border border-cyan-500/30 hover:border-cyan-400/50 rounded-full px-4 py-1.5 bg-black/30 backdrop-blur-sm"
        >
          Disconnect
        </button>
      </div>
      <ChatWindow messages={messages} isLoading={isLoading} />
      <ChatInput onSubmit={startResearch} isLoading={isLoading} />
    </>
  );
};
