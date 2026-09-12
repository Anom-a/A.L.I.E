import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Chat } from './pages/Chat';

export default function App() {
  return (
    <Router>
      <AuthProvider>
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

          <Routes>
            <Route path="/login" element={<LoginRoute />} />
            <Route path="/register" element={<RegisterRoute />} />
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Chat />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

// Helper components to redirect logged-in users away from auth pages
const LoginRoute = () => {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <Login />;
};

const RegisterRoute = () => {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <Register />;
};
