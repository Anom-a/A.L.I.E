import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { OrbitControls, Float } from '@react-three/drei';

const CoreShape: React.FC = () => {
  const outerRef = useRef<THREE.Mesh>(null);
  const innerRef = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (outerRef.current) {
      outerRef.current.rotation.x += delta * 0.15;
      outerRef.current.rotation.y += delta * 0.2;
    }
    if (innerRef.current) {
      innerRef.current.rotation.x -= delta * 0.1;
      innerRef.current.rotation.y += delta * 0.25;
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
      {/* Inner glowing solid core */}
      <mesh ref={innerRef}>
        <icosahedronGeometry args={[1, 1]} />
        <meshStandardMaterial
          color="#3D8BFF"
          emissive="#06B6D4"
          emissiveIntensity={2}
          toneMapped={false}
          wireframe={false}
          transparent
          opacity={0.85}
        />
      </mesh>

      {/* Outer wireframe shell */}
      <mesh ref={outerRef}>
        <icosahedronGeometry args={[1.5, 2]} />
        <meshStandardMaterial
          color="#6BA8FF"
          emissive="#6BA8FF"
          emissiveIntensity={0.8}
          wireframe={true}
          transparent
          opacity={0.3}
        />
      </mesh>
    </Float>
  );
};

export const Core3D: React.FC = () => {
  return (
    <div className="w-full h-full min-h-[200px] flex items-center justify-center relative">
      {/* Backdrop glow to ground the 3D object in 2D space */}
      <div className="absolute inset-0 m-auto w-32 h-32 rounded-full bg-primary/20 blur-[50px] mix-blend-screen pointer-events-none" />
      
      <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={2} color="#06B6D4" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#3D8BFF" />
        <CoreShape />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
      </Canvas>
    </div>
  );
};
