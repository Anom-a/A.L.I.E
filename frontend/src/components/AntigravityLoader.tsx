import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Particle {
  id: number;
  x: number;        // initial x position (%)
  size: number;      // px
  opacity: number;
  duration: number;  // animation duration (s)
  delay: number;     // animation delay (s)
  drift: number;     // horizontal drift amount (px)
}

interface Shard {
  id: number;
  width: number;
  height: number;
  x: number;           // offset from center (px)
  y: number;           // offset from center (px)
  rotation: number;    // initial rotation (deg)
  orbitRadius: number; // how far it floats
  duration: number;    // animation cycle length (s)
  delay: number;
  opacity: number;
}

type StatusLine =
  | 'Initializing A.L.I.E. neural substrate...'
  | 'Syncing neural pathways...'
  | 'Calibrating zero-g environment...'
  | 'Loading quantum inference engine...'
  | 'Mapping cognitive manifold...'
  | 'Establishing synaptic mesh...'
  | 'Bootstrapping consciousness layer...'
  | 'Online.';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PARTICLE_COUNT = 60;
const SHARD_COUNT = 12;

const STATUS_SEQUENCE: StatusLine[] = [
  'Initializing A.L.I.E. neural substrate...',
  'Syncing neural pathways...',
  'Calibrating zero-g environment...',
  'Loading quantum inference engine...',
  'Mapping cognitive manifold...',
  'Establishing synaptic mesh...',
  'Bootstrapping consciousness layer...',
  'Online.',
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

function generateParticles(count: number): Particle[] {
  const rng = seededRandom(42);
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: rng() * 100,
    size: rng() * 2.5 + 1,
    opacity: rng() * 0.5 + 0.15,
    duration: rng() * 8 + 6,
    delay: rng() * 6,
    drift: (rng() - 0.5) * 60,
  }));
}

function generateShards(count: number): Shard[] {
  const rng = seededRandom(137);
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    width: rng() * 24 + 8,
    height: rng() * 32 + 10,
    x: (rng() - 0.5) * 180,
    y: (rng() - 0.5) * 180,
    rotation: rng() * 360,
    orbitRadius: rng() * 30 + 10,
    duration: rng() * 6 + 5,
    delay: rng() * 3,
    opacity: rng() * 0.35 + 0.08,
  }));
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ParticleField({ particles }: { particles: Particle[] }) {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            bottom: '-4%',
            width: p.size,
            height: p.size,
            background: `radial-gradient(circle, rgba(6,182,212,${p.opacity}) 0%, transparent 70%)`,
            boxShadow: `0 0 ${p.size * 3}px rgba(6,182,212,${p.opacity * 0.6})`,
          }}
          animate={{
            y: [0, -(typeof window !== 'undefined' ? window.innerHeight : 1000) * 1.15],
            x: [0, p.drift],
            opacity: [0, p.opacity, p.opacity, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: 'linear',
          }}
        />
      ))}
    </div>
  );
}

function NeuralCore({ shards }: { shards: Shard[] }) {
  return (
    <div className="relative flex items-center justify-center" style={{ width: 280, height: 280 }}>
      {/* Outer pulse ring */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 240,
          height: 240,
          border: '1px solid rgba(6,182,212,0.15)',
          boxShadow: '0 0 40px rgba(6,182,212,0.06), inset 0 0 40px rgba(6,182,212,0.04)',
        }}
        animate={{ scale: [1, 1.12, 1], opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Inner glow orb */}
      <motion.div
        className="absolute rounded-full"
        style={{
          width: 90,
          height: 90,
          background: 'radial-gradient(circle, rgba(6,182,212,0.35) 0%, rgba(6,182,212,0.08) 50%, transparent 70%)',
          boxShadow: '0 0 60px rgba(6,182,212,0.25), 0 0 120px rgba(6,182,212,0.08)',
        }}
        animate={{ scale: [1, 1.25, 1], opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
      />

      {/* Shattered glass shards orbiting */}
      {shards.map((s) => (
        <motion.div
          key={s.id}
          className="absolute"
          style={{
            width: s.width,
            height: s.height,
            left: `calc(50% + ${s.x}px)`,
            top: `calc(50% + ${s.y}px)`,
            background: `linear-gradient(${s.rotation}deg, rgba(6,182,212,${s.opacity}) 0%, rgba(6,182,212,${s.opacity * 0.3}) 100%)`,
            borderRadius: '2px',
            border: '0.5px solid rgba(6,182,212,0.12)',
            backdropFilter: 'blur(2px)',
            transformOrigin: 'center center',
          }}
          animate={{
            y: [0, -s.orbitRadius, 0, s.orbitRadius * 0.7, 0],
            x: [0, s.orbitRadius * 0.6, 0, -s.orbitRadius * 0.4, 0],
            rotate: [s.rotation, s.rotation + 90, s.rotation + 180, s.rotation + 270, s.rotation + 360],
            opacity: [s.opacity, s.opacity * 1.5, s.opacity, s.opacity * 0.8, s.opacity],
          }}
          transition={{
            duration: s.duration,
            delay: s.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

      {/* Centre infinity / eye symbol */}
      <motion.svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        className="absolute"
        animate={{ rotate: [0, 360] }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
      >
        <path
          d="M14 24c0-4.4 3.6-8 8-8s8 5.3 8 8-3.6 8-8 8-8-3.6-8-8zm16 0c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8-8-5.3-8-8z"
          stroke="rgba(6,182,212,0.5)"
          strokeWidth="1.2"
          strokeLinecap="round"
        />
        <path
          d="M4 24c0-5.5 4.5-10 10-10s10 6.7 10 10-4.5 10-10 10S4 29.5 4 24zm20 0c0-5.5 4.5-10 10-10s10 4.5 10 10-4.5 10-10 10-10-6.7-10-10z"
          stroke="rgba(6,182,212,0.2)"
          strokeWidth="0.8"
          strokeLinecap="round"
        />
      </motion.svg>
    </div>
  );
}

function StatusTerminal({ lines }: { lines: StatusLine[] }) {
  return (
    <div
      className="relative rounded-xl px-6 py-4 max-w-md w-full"
      style={{
        background: 'rgba(5,7,13,0.65)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(6,182,212,0.12)',
        boxShadow: '0 0 30px rgba(6,182,212,0.06)',
      }}
    >
      {/* Terminal header dots */}
      <div className="flex gap-1.5 mb-3">
        <span className="block w-2 h-2 rounded-full bg-red-500/60" />
        <span className="block w-2 h-2 rounded-full bg-yellow-500/50" />
        <span className="block w-2 h-2 rounded-full bg-green-500/50" />
      </div>

      <div className="font-label-md text-label-sm space-y-1.5 min-h-[120px]">
        <AnimatePresence mode="popLayout">
          {lines.map((line, i) => (
            <motion.div
              key={`${line}-${i}`}
              initial={{ opacity: 0, y: 8, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="flex items-start gap-2"
            >
              <span
                className="select-none shrink-0"
                style={{
                  color: line === 'Online.'
                    ? 'rgba(74,222,158,0.9)'
                    : 'rgba(6,182,212,0.6)',
                }}
              >
                {line === 'Online.' ? '✓' : '›'}
              </span>
              <span
                style={{
                  color: line === 'Online.'
                    ? 'rgba(74,222,158,0.9)'
                    : 'rgba(6,182,212,0.8)',
                  textShadow: line === 'Online.'
                    ? '0 0 12px rgba(74,222,158,0.4)'
                    : '0 0 8px rgba(6,182,212,0.25)',
                }}
              >
                {line}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Blinking cursor */}
        <motion.span
          className="inline-block w-2 h-4 ml-4"
          style={{ background: 'rgba(6,182,212,0.7)' }}
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.8, repeat: Infinity, ease: 'steps(2)' }}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export default function AntigravityLoader() {
  const particles = useMemo(() => generateParticles(PARTICLE_COUNT), []);
  const shards = useMemo(() => generateShards(SHARD_COUNT), []);

  const [visibleLines, setVisibleLines] = useState<StatusLine[]>([]);
  const [lineIndex, setLineIndex] = useState(0);

  // Progressively reveal status lines
  useEffect(() => {
    if (lineIndex >= STATUS_SEQUENCE.length) return;

    const delay = lineIndex === STATUS_SEQUENCE.length - 1 ? 2200 : 1400 + Math.random() * 800;
    const timer = window.setTimeout(() => {
      setVisibleLines((prev) => [...prev.slice(-5), STATUS_SEQUENCE[lineIndex]]);
      setLineIndex((prev) => prev + 1);
    }, delay);

    return () => window.clearTimeout(timer);
  }, [lineIndex]);

  return (
    <div
      className="relative flex flex-col items-center justify-center h-screen w-screen overflow-hidden"
      style={{ background: 'radial-gradient(ellipse at 50% 40%, #0a1628 0%, #05070d 70%)' }}
    >
      {/* Subtle grid overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(6,182,212,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.4) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Particles */}
      <ParticleField particles={particles} />

      {/* Floating Neural Core */}
      <motion.div
        className="relative z-10 mb-10"
        animate={{
          y: [0, -18, 0, 12, 0],
          x: [0, 8, 0, -6, 0],
          rotate: [0, 1.5, 0, -1, 0],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
      >
        <NeuralCore shards={shards} />
      </motion.div>

      {/* Title */}
      <motion.h1
        className="relative z-10 font-headline-xl text-headline-xl tracking-tight mb-2 text-center"
        style={{
          color: 'rgba(6,182,212,0.9)',
          textShadow: '0 0 30px rgba(6,182,212,0.3), 0 0 60px rgba(6,182,212,0.1)',
        }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1, delay: 0.3 }}
      >
        A.L.I.E.
      </motion.h1>

      <motion.p
        className="relative z-10 font-label-md text-label-md tracking-[0.25em] uppercase mb-8"
        style={{
          color: 'rgba(6,182,212,0.45)',
          textShadow: '0 0 15px rgba(6,182,212,0.15)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.7 }}
      >
        Applied Lucent Intelligence Emulator
      </motion.p>

      {/* Status Terminal */}
      <motion.div
        className="relative z-10 px-4 w-full flex justify-center"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 1 }}
      >
        <StatusTerminal lines={visibleLines} />
      </motion.div>

      {/* Bottom ambient glow */}
      <div
        className="pointer-events-none absolute bottom-0 left-0 right-0 h-40"
        style={{
          background: 'linear-gradient(to top, rgba(6,182,212,0.04), transparent)',
        }}
      />
    </div>
  );
}
