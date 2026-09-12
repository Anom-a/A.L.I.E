import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#020408] text-white relative overflow-hidden">
      {/* Background Deep Space Gradients */}
      <div className="absolute top-[20%] left-1/4 w-[600px] h-[600px] rounded-full blur-[160px] opacity-30 pointer-events-none" style={{ background: 'radial-gradient(circle, #06B6D4 0%, transparent 70%)' }}></div>
      <div className="absolute top-[40%] -right-[15%] w-[500px] h-[500px] rounded-full blur-[150px] opacity-20 pointer-events-none" style={{ background: 'radial-gradient(circle, #3D8BFF 0%, transparent 65%)' }}></div>
      
      {/* Grid Pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20" style={{ backgroundImage: 'linear-gradient(rgba(6,182,212,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.3) 1px, transparent 1px)', backgroundSize: '40px 40px', transform: 'perspective(500px) rotateX(60deg) translateY(-100px) translateZ(-200px)'}}></div>

      <div className="z-10 text-center space-y-8 max-w-3xl px-6 relative">
        <div className="inline-block mb-4">
          <div className="h-[2px] w-12 bg-cyan-500 mx-auto mb-6"></div>
          <h1 className="text-6xl md:text-8xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600 drop-shadow-sm">
            A.L.I.E.
          </h1>
        </div>
        <p className="text-xl md:text-2xl text-cyan-100/70 font-light max-w-2xl mx-auto">
          Your personal AI research assistant. Synthesize complex information and get actionable insights in seconds.
        </p>
        
        <div className="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-6 pt-12">
          <Link to="/login" className="w-full sm:w-auto px-10 py-4 rounded border border-cyan-500/50 bg-cyan-500/10 hover:bg-cyan-500/20 hover:border-cyan-400 transition-all font-medium text-lg text-cyan-300 backdrop-blur-sm tracking-wide">
            ACCESS TERMINAL
          </Link>
          <Link to="/register" className="w-full sm:w-auto px-10 py-4 rounded bg-cyan-600 hover:bg-cyan-500 transition-colors font-medium text-lg text-white shadow-[0_0_20px_rgba(6,182,212,0.4)] tracking-wide">
            INITIALIZE RECORD
          </Link>
        </div>
      </div>
    </div>
  );
}
