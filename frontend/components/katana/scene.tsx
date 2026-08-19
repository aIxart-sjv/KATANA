'use client'

import { Suspense, type MutableRefObject } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Environment, Float } from '@react-three/drei'
import type { Group } from 'three'
import { Katana } from './katana'

type Progress = MutableRefObject<number>

/**
 * Drives the camera as the user scrolls. `progress` is 0 → 1 across the page.
 * Each keyframe is a dramatic angle on the blade; we lerp between them.
 */
function CameraRig({
  progress,
  live,
}: {
  progress: Progress
  live: MutableRefObject<boolean>
}) {
  const { camera } = useThree()

  // camera positions keyed to scroll progress
  const keys = [
    { at: 0.0, pos: [0, 0.2, 6.5], look: [0.5, 0, 0] },
    { at: 0.28, pos: [-2.6, 1.4, 3.2], look: [-1, 0, 0] },
    { at: 0.52, pos: [3.2, 0.1, 2.4], look: [2.4, 0, 0] },
    { at: 0.76, pos: [0, 2.8, 3.6], look: [0.5, 0, 0] },
    { at: 1.0, pos: [0, 0.1, 7.2], look: [0.5, 0, 0] },
  ]

  useFrame(() => {
    if (!live.current) return
    const p = progress.current

    let a = keys[0]
    let b = keys[keys.length - 1]
    for (let i = 0; i < keys.length - 1; i++) {
      if (p >= keys[i].at && p <= keys[i + 1].at) {
        a = keys[i]
        b = keys[i + 1]
        break
      }
    }
    const span = b.at - a.at || 1
    const t = Math.min(Math.max((p - a.at) / span, 0), 1)
    // easeInOut
    const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2

    const px = a.pos[0] + (b.pos[0] - a.pos[0]) * e
    const py = a.pos[1] + (b.pos[1] - a.pos[1]) * e
    const pz = a.pos[2] + (b.pos[2] - a.pos[2]) * e
    camera.position.lerp({ x: px, y: py, z: pz } as never, 0.08)

    const lx = a.look[0] + (b.look[0] - a.look[0]) * e
    const ly = a.look[1] + (b.look[1] - a.look[1]) * e
    const lz = a.look[2] + (b.look[2] - a.look[2]) * e
    camera.lookAt(lx, ly, lz)
  })

  return null
}

export function Scene({
  progress,
  live,
  onReady,
}: {
  progress: Progress
  live: MutableRefObject<boolean>
  onReady: (g: Group) => void
}) {
  return (
    <Canvas
      camera={{ position: [0, 0.3, 6.8], fov: 42 }}
      gl={{ antialias: true, alpha: true }}
      dpr={[1, 2]}
    >
      <color attach="background" args={['#0a0a0c']} />
      <fog attach="fog" args={['#0a0a0c', 8, 22]} />

      <ambientLight intensity={0.25} />
      {/* cool key light raking across the steel */}
      <directionalLight position={[5, 6, 4]} intensity={2.2} color="#cfe0ff" />
      {/* crimson rim light for the blood accent */}
      <spotLight
        position={[-4, 2, -3]}
        angle={0.7}
        penumbra={1}
        intensity={40}
        color="#ff2d3f"
        distance={30}
      />
      <pointLight position={[0, -3, 4]} intensity={8} color="#3a4a6b" />

      <Suspense fallback={null}>
        <Float
          speed={1.1}
          rotationIntensity={0.15}
          floatIntensity={0.35}
          floatingRange={[-0.05, 0.05]}
        >
          <Katana onReady={onReady} />
        </Float>
        <Environment preset="night" environmentIntensity={0.6} />
      </Suspense>

      <CameraRig progress={progress} live={live} />
    </Canvas>
  )
}
