'use client'

import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'
import * as THREE from 'three'

function RacingLine() {
  const lineRef = useRef<THREE.Group>(null)

  // Generate a smooth racing line curve
  const points: [number, number, number][] = []
  const segments = 200

  for (let i = 0; i <= segments; i++) {
    const t = (i / segments) * Math.PI * 2
    // Create a flowing racing line shape
    const x = Math.sin(t) * 4 + Math.sin(t * 2) * 1.5
    const y = Math.cos(t * 3) * 0.3
    const z = Math.cos(t) * 3 + Math.cos(t * 2) * 1
    points.push([x, y, z])
  }

  useFrame((state) => {
    if (lineRef.current) {
      lineRef.current.rotation.y = state.clock.elapsedTime * 0.03
      lineRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.02) * 0.1
    }
  })

  return (
    <group ref={lineRef} position={[0, 0, 0]}>
      {/* Main racing line */}
      <Line
        points={points}
        color="#EA580C"
        lineWidth={2}
        transparent
        opacity={0.6}
      />
      {/* Ghost line for depth */}
      <Line
        points={points.map(([x, y, z]) => [x * 1.02, y * 1.02, z * 1.02] as [number, number, number])}
        color="#EA580C"
        lineWidth={1}
        transparent
        opacity={0.2}
      />
      {/* Inner reference line */}
      <Line
        points={points.map(([x, y, z]) => [x * 0.95, y, z * 0.95] as [number, number, number])}
        color="#4B5563"
        lineWidth={0.5}
        transparent
        opacity={0.3}
      />
    </group>
  )
}

function TelemetryGrid() {
  const gridRef = useRef<THREE.GridHelper>(null)

  useFrame((state) => {
    if (gridRef.current) {
      gridRef.current.position.z = (state.clock.elapsedTime * 0.5) % 2
    }
  })

  return (
    <gridHelper
      ref={gridRef}
      args={[40, 40, '#1C1F23', '#151719']}
      position={[0, -3, 0]}
      rotation={[0, 0, 0]}
    />
  )
}

function TelemetryDots() {
  const dotsRef = useRef<THREE.Points>(null)

  // Create random dot positions
  const positions = new Float32Array(100 * 3)
  for (let i = 0; i < 100; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 20
    positions[i * 3 + 1] = (Math.random() - 0.5) * 10
    positions[i * 3 + 2] = (Math.random() - 0.5) * 20
  }

  useFrame((state) => {
    if (dotsRef.current) {
      dotsRef.current.rotation.y = state.clock.elapsedTime * 0.01
    }
  })

  return (
    <points ref={dotsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={100}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#06B6D4"
        size={0.03}
        transparent
        opacity={0.4}
        sizeAttenuation
      />
    </points>
  )
}

export function RacingLineCanvas() {
  return (
    <div className="w-full h-full opacity-60">
      <Canvas
        camera={{ position: [0, 2, 12], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.5} />
        <RacingLine />
        <TelemetryGrid />
        <TelemetryDots />
      </Canvas>
    </div>
  )
}
