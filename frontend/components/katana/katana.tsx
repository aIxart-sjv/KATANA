'use client'

import { useEffect, useRef } from 'react'
import { RoundedBox } from '@react-three/drei'
import type { Group } from 'three'

type KatanaProps = {
  onReady?: (group: Group) => void
}

/**
 * Procedural stylized katana, modeled pointing along +X so the intro
 * "slash" reads as a left-to-right sweep.
 *
 * ── Swapping in your own .glb ──────────────────────────────────────────────
 * 1. Drop your file at /public/models/katana.glb
 * 2. import { useGLTF } from '@react-three/drei'
 * 3. const { scene } = useGLTF('/models/katana.glb')
 * 4. Replace the meshes below with <primitive object={scene} />, keeping the
 *    outer <group ref={ref}> and the onReady call intact so the cinematic
 *    animations still drive it.
 */
export function Katana({ onReady }: KatanaProps) {
  const ref = useRef<Group>(null)

  useEffect(() => {
    if (ref.current && onReady) onReady(ref.current)
  }, [onReady])

  return (
    <group ref={ref} rotation={[0, 0, 0.04]}>
      {/* Blade */}
      <RoundedBox
        args={[4.2, 0.16, 0.05]}
        radius={0.024}
        smoothness={4}
        position={[1.4, 0, 0]}
      >
        <meshStandardMaterial
          color="#c7ccd6"
          metalness={1}
          roughness={0.16}
          envMapIntensity={1.6}
        />
      </RoundedBox>

      {/* Hamon temper line — a faint glowing edge near the cutting side */}
      <mesh position={[1.4, -0.05, 0.028]}>
        <boxGeometry args={[4.0, 0.03, 0.006]} />
        <meshStandardMaterial
          color="#e9eef7"
          emissive="#8fa4c9"
          emissiveIntensity={0.5}
          metalness={0.8}
          roughness={0.3}
        />
      </mesh>

      {/* Kissaki — the pointed tip */}
      <mesh position={[3.62, 0.02, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <coneGeometry args={[0.08, 0.36, 4]} />
        <meshStandardMaterial
          color="#c7ccd6"
          metalness={1}
          roughness={0.14}
          envMapIntensity={1.6}
        />
      </mesh>

      {/* Tsuba — the guard */}
      <mesh position={[-0.72, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.34, 0.34, 0.06, 40]} />
        <meshStandardMaterial
          color="#181a1f"
          metalness={0.9}
          roughness={0.45}
          envMapIntensity={0.8}
        />
      </mesh>

      {/* Habaki — brass collar between blade and guard */}
      <mesh position={[-0.6, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.11, 0.11, 0.22, 24]} />
        <meshStandardMaterial
          color="#b08d4c"
          metalness={1}
          roughness={0.3}
          envMapIntensity={1.4}
        />
      </mesh>

      {/* Tsuka — the wrapped handle */}
      <mesh position={[-1.6, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.1, 0.11, 1.7, 24]} />
        <meshStandardMaterial
          color="#2a0d0f"
          metalness={0.2}
          roughness={0.85}
        />
      </mesh>

      {/* Ito — crimson diamond wrap suggested with ridged rings */}
      {Array.from({ length: 9 }).map((_, i) => (
        <mesh
          key={i}
          position={[-0.98 - i * 0.15, 0, 0]}
          rotation={[0, 0, Math.PI / 2]}
        >
          <torusGeometry args={[0.11, 0.022, 8, 20]} />
          <meshStandardMaterial
            color="#6b1b1f"
            metalness={0.3}
            roughness={0.7}
          />
        </mesh>
      ))}

      {/* Kashira — pommel cap */}
      <mesh position={[-2.5, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.12, 0.12, 0.08, 24]} />
        <meshStandardMaterial
          color="#181a1f"
          metalness={0.9}
          roughness={0.45}
        />
      </mesh>
    </group>
  )
}
