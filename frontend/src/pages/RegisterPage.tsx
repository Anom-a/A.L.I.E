import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setToken = useAuthStore(state => state.setToken);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Registration failed');
      }

      const data = await res.json();
      setToken(data.access_token);
      navigate('/app');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#020408] text-white">
      <div className="w-full max-w-md p-8 rounded-xl bg-surface/50 border border-border/50 backdrop-blur-md shadow-2xl">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-cyan-400">Initialize Record</h2>
          <p className="text-sm text-gray-400 mt-2">Create your A.L.I.E. identity</p>
        </div>
        
        {error && <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded mb-6 text-sm">{error}</div>}

        <form onSubmit={handleRegister} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Email Designation</label>
            <input
              type="email"
              required
              className="w-full bg-canvas-base border border-border/50 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500 transition-colors"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Access Code</label>
            <input
              type="password"
              required
              className="w-full bg-canvas-base border border-border/50 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500 transition-colors"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium py-3 rounded-lg transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : 'Register Subject'}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-400">
          Already authorized? <Link to="/login" className="text-cyan-400 hover:underline">Access Terminal</Link>
        </div>
      </div>
    </div>
  );
}
