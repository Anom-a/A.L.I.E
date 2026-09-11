import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { TopCommandBar } from './components/TopCommandBar';
import { DocumentPanel } from './components/DocumentPanel';
import { SourcesPanel } from './components/SourcesPanel';

export default function App() {
  const [sourcesVisible, setSourcesVisible] = useState(true);

  return (
    <div className="flex min-h-screen bg-canvas-base text-on-surface">
      {/* Background Decorative Effects */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-[20%] left-1/4 w-[850px] h-[850px] rounded-full blur-[160px] opacity-25 pointer-events-none" style={{ background: 'radial-gradient(circle, #3D8BFF 0%, rgba(107, 168, 255, 0.08) 50%, transparent 70%)' }}></div>
        <div className="absolute top-[40%] -right-[15%] w-[700px] h-[700px] rounded-full blur-[150px] opacity-20 pointer-events-none" style={{ background: 'radial-gradient(circle, #1a4f9e 0%, transparent 65%)' }}></div>
        <div className="absolute bottom-[-10%] left-[10%] w-[600px] h-[600px] rounded-full blur-[140px] opacity-15 pointer-events-none" style={{ background: 'radial-gradient(circle, #2463eb 0%, transparent 65%)' }}></div>
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(rgba(61, 139, 255, 0.6) 1px, transparent 1px)', backgroundSize: '36px 36px' }}></div>
      </div>

      <Sidebar />
      
      <div className="pl-72 flex flex-col w-full relative z-10">
        <Header />
        
        <main className="w-full pt-20 bg-canvas-base flex-1 px-gutter py-space-xl">
          <div className="flex flex-col w-full max-w-7xl mx-auto">
            <TopCommandBar onToggleDrawer={() => setSourcesVisible(!sourcesVisible)} />
            
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className={sourcesVisible ? "lg:col-span-8" : "lg:col-span-12"}>
                <DocumentPanel />
              </div>
              <SourcesPanel isVisible={sourcesVisible} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
