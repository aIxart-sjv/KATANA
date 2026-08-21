'use client'

import {
  Suspense,
  useMemo,
  useRef,
  type MutableRefObject,
} from 'react'

import {
  Canvas,
  useFrame,
  useThree,
} from '@react-three/fiber'

import {
  Environment,
  Float,
} from '@react-three/drei'

import type {
  Group,
  Points,
  PointLight,
} from 'three'

import { Katana } from './katana'

type Progress = MutableRefObject<number>

/*
 * ============================================================
 * INTERACTIVE BACKGROUND FIELD
 *
 * Subtle particle environment behind the katana.
 * The field responds to mouse movement but remains restrained.
 * ============================================================
 */

function BackgroundField() {
  const particles =
    useRef<Points>(null)

  const glow =
    useRef<PointLight>(null)

  const positions = useMemo(() => {
    const count = 500

    const data =
      new Float32Array(
        count * 3,
      )

    for (let i = 0; i < count; i++) {
      const index = i * 3

      data[index] =
        (Math.random() - 0.5) * 18

      data[index + 1] =
        (Math.random() - 0.5) * 12

      data[index + 2] =
        (Math.random() - 0.5) * 8 - 2
    }

    return data
  }, [])

  useFrame((state, delta) => {
    const mouseX =
      state.pointer.x

    const mouseY =
      state.pointer.y

    /*
     * ========================================================
     * PARTICLE PARALLAX
     * ========================================================
     */

    if (particles.current) {
      particles.current.rotation.y +=
        delta * 0.003

      particles.current.rotation.x +=
        delta * 0.001

      particles.current.position.x +=
        (
          mouseX * 0.8 -
          particles.current.position.x
        ) * 0.015

      particles.current.position.y +=
        (
          mouseY * 0.5 -
          particles.current.position.y
        ) * 0.015
    }

    /*
     * ========================================================
     * MOUSE FOLLOWING RED AMBIENT GLOW
     * ========================================================
     */

    if (glow.current) {
      glow.current.position.x +=
        (
          mouseX * 5 -
          glow.current.position.x
        ) * 0.04

      glow.current.position.y +=
        (
          mouseY * 3 -
          glow.current.position.y
        ) * 0.04
    }
  })

  return (
    <>
      {/* ======================================================
          PARTICLE FIELD
          ====================================================== */}

      <points
        ref={particles}
      >
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[
              positions,
              3,
            ]}
          />
        </bufferGeometry>

        <pointsMaterial
          size={0.025}
          color="#8b1d27"
          transparent
          opacity={0.45}
          sizeAttenuation
          depthWrite={false}
        />
      </points>

      {/* ======================================================
          INTERACTIVE RED GLOW
          ====================================================== */}

      <pointLight
        ref={glow}
        position={[0, 0, 2]}
        intensity={3}
        distance={10}
        color="#b21f2d"
      />
    </>
  )
}

/*
 * ============================================================
 * CAMERA RIG
 * ============================================================
 */

function CameraRig({
  progress,
  live,
}: {
  progress: Progress
  live: MutableRefObject<boolean>
}) {
  const {
    camera,
    pointer,
  } = useThree()

  const keys = [
    {
      at: 0.0,
      pos: [0, 0.2, 6.5],
      look: [0.5, 0, 0],
    },
    {
      at: 0.28,
      pos: [-2.6, 1.4, 3.2],
      look: [-1, 0, 0],
    },
    {
      at: 0.52,
      pos: [3.2, 0.1, 2.4],
      look: [2.4, 0, 0],
    },
    {
      at: 0.76,
      pos: [0, 2.8, 3.6],
      look: [0.5, 0, 0],
    },
    {
      at: 1.0,
      pos: [0, 0.1, 7.2],
      look: [0.5, 0, 0],
    },
  ]

  useFrame(() => {
    if (!live.current) {
      return
    }

    const p =
      progress.current

    let a =
      keys[0]

    let b =
      keys[keys.length - 1]

    for (
      let i = 0;
      i < keys.length - 1;
      i++
    ) {
      if (
        p >= keys[i].at &&
        p <= keys[i + 1].at
      ) {
        a =
          keys[i]

        b =
          keys[i + 1]

        break
      }
    }

    const span =
      b.at - a.at || 1

    const t =
      Math.min(
        Math.max(
          (p - a.at) /
            span,
          0,
        ),
        1,
      )

    const e =
      t < 0.5
        ? 2 * t * t
        : 1 -
          Math.pow(
            -2 * t + 2,
            2,
          ) /
            2

    /*
     * ========================================================
     * SCROLL CAMERA POSITION
     * ========================================================
     */

    const baseX =
      a.pos[0] +
      (b.pos[0] - a.pos[0]) *
        e

    const baseY =
      a.pos[1] +
      (b.pos[1] - a.pos[1]) *
        e

    const baseZ =
      a.pos[2] +
      (b.pos[2] - a.pos[2]) *
        e

    /*
     * Very subtle mouse parallax.
     */

    const targetX =
      baseX +
      pointer.x * 0.08

    const targetY =
      baseY +
      pointer.y * 0.08

    camera.position.x +=
      (
        targetX -
        camera.position.x
      ) * 0.04

    camera.position.y +=
      (
        targetY -
        camera.position.y
      ) * 0.04

    camera.position.z +=
      (
        baseZ -
        camera.position.z
      ) * 0.04

    /*
     * ========================================================
     * CAMERA LOOK TARGET
     * ========================================================
     */

    const lx =
      a.look[0] +
      (b.look[0] - a.look[0]) *
        e

    const ly =
      a.look[1] +
      (b.look[1] - a.look[1]) *
        e

    const lz =
      a.look[2] +
      (b.look[2] - a.look[2]) *
        e

    camera.lookAt(
      lx +
        pointer.x * 0.03,
      ly +
        pointer.y * 0.03,
      lz,
    )
  })

  return null
}

/*
 * ============================================================
 * SCENE
 * ============================================================
 */

export function Scene({
  progress,
  live,
  onReady,
}: {
  progress: Progress
  live: MutableRefObject<boolean>
  onReady: (
    g: Group,
  ) => void
}) {
  return (
    <Canvas
      camera={{
        position: [
          0,
          0.3,
          6.8,
        ],
        fov: 42,
      }}
      gl={{
        antialias: true,
        alpha: true,
      }}
      dpr={[1, 2]}
    >
      {/* ======================================================
          WORLD
          ====================================================== */}

      <color
        attach="background"
        args={['#070709']}
      />

      <fog
        attach="fog"
        args={[
          '#070709',
          8,
          22,
        ]}
      />

      {/* ======================================================
          BASE LIGHTING
          ====================================================== */}

      <ambientLight
        intensity={0.2}
      />

      {/* Cool steel light */}

      <directionalLight
        position={[
          5,
          6,
          4,
        ]}
        intensity={2.2}
        color="#cfe0ff"
      />

      {/* Crimson rim light */}

      <spotLight
        position={[
          -4,
          2,
          -3,
        ]}
        angle={0.7}
        penumbra={1}
        intensity={35}
        color="#b21f2d"
        distance={30}
      />

      <pointLight
        position={[
          0,
          -3,
          4,
        ]}
        intensity={6}
        color="#3a4a6b"
      />

      {/* ======================================================
          INTERACTIVE ENVIRONMENT
          ====================================================== */}

      <BackgroundField />

      {/* ======================================================
          KATANA
          ====================================================== */}

      <Suspense fallback={null}>
        <Float
          speed={1.1}
          rotationIntensity={0.15}
          floatIntensity={0.35}
          floatingRange={[
            -0.05,
            0.05,
          ]}
        >
          <Katana
            onReady={onReady}
          />
        </Float>

        <Environment
          preset="night"
          environmentIntensity={0.6}
        />
      </Suspense>

      <CameraRig
        progress={progress}
        live={live}
      />
    </Canvas>
  )
}