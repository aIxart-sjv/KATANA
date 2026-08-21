'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import type { Group } from 'three'
import { Scene } from './scene'
import { Sections } from './sections'
import { playWhoosh } from './use-whoosh'

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger)
}

export function Experience() {
  const progress = useRef(0)
  const live = useRef(false)
  const katana = useRef<Group | null>(null)

  const canvasWrap = useRef<HTMLDivElement>(null)
  const flash = useRef<HTMLDivElement>(null)
  const blackout = useRef<HTMLDivElement>(null)
  const scrollRoot = useRef<HTMLDivElement>(null)

  const [phase, setPhase] = useState<'ready' | 'cinematic' | 'live'>('ready')

  // Lock scroll until the cinematic completes.
  useEffect(() => {
    document.body.style.overflow = phase === 'live' ? '' : 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [phase])

  const onReady = useCallback((g: Group) => {
    katana.current = g
    // Pre-stage the blade off-screen left (hidden behind the blackout).
    g.position.set(-13, 0.4, 0)
    g.scale.set(2.4, 1, 1)
    g.rotation.z = 0.6
  }, [])

  // Once "live", set up the scroll-driven progress + reveals.
  useEffect(() => {
    if (phase !== 'live') return
    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: document.body,
        start: 'top top',
        end: 'bottom bottom',
        scrub: true,
        onUpdate: (self) => {
          progress.current = self.progress
        },
      })

      gsap.utils.toArray<HTMLElement>('[data-reveal]').forEach((el) => {
        gsap.fromTo(
          el,
          { autoAlpha: 0, y: 42, filter: 'blur(6px)' },
          {
            autoAlpha: 1,
            y: 0,
            filter: 'blur(0px)',
            duration: 1,
            ease: 'power3.out',
            scrollTrigger: {
              trigger: el,
              start: 'top 82%',
              toggleActions: 'play none none reverse',
            },
          },
        )
      })
      ScrollTrigger.refresh()
    })
    return () => ctx.revert()
  }, [phase])

  const startCinematic = useCallback(() => {
    if (phase !== 'ready') return
    setPhase('cinematic')
    playWhoosh()

    const g = katana.current
    const tl = gsap.timeline({
      onComplete: () => {
        live.current = true
        setPhase('live')
      },
    })

    // Reveal the world from black.
    tl.to(blackout.current, { autoAlpha: 0, duration: 0.35, ease: 'power2.out' }, 0.05)

    // Motion-blurred slash across the frame.
    tl.set(canvasWrap.current, { filter: 'blur(10px)' }, 0)
    if (g) {
      tl.to(
        g.position,
        { x: 0.4, y: 0, duration: 0.42, ease: 'power4.out' },
        0.12,
      )
      tl.to(
        g.scale,
        { x: 1, duration: 0.42, ease: 'power4.out' },
        0.12,
      )
      tl.to(
        g.rotation,
        { z: 0.04, duration: 0.5, ease: 'power3.out' },
        0.12,
      )
    }
    tl.to(canvasWrap.current, { filter: 'blur(0px)', duration: 0.14 }, 0.42)

    // Impact flash.
    tl.set(flash.current, { autoAlpha: 0.95 }, 0.46)
    tl.to(flash.current, { autoAlpha: 0, duration: 0.5, ease: 'power2.out' }, 0.5)
  }, [phase])

  return (
    <main className="relative">
      {/* Fixed 3D background */}
      <div
        ref={canvasWrap}
        className="fixed inset-0 z-0 h-screen w-full will-change-[filter]"
      >
        <Scene progress={progress} live={live} onReady={onReady} />
      </div>

      {/* Vignette for cinematic depth */}
      <div className="pointer-events-none fixed inset-0 z-[1] bg-[radial-gradient(ellipse_at_center,transparent_45%,rgba(0,0,0,0.7)_100%)]" />

      {/* Scrollable DOM layer */}
      <div ref={scrollRoot} className="relative z-10">
        <Sections />
      </div>

      {/* Impact flash */}
      <div
        ref={flash}
        className="pointer-events-none fixed inset-0 z-40 bg-foreground opacity-0"
        aria-hidden
      />

      {/* Intro blackout + enter gate */}
      {phase !== 'live' && (
        <div
          ref={blackout}
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#050506]"
        >
          {phase === 'ready' && (
            <div className="flex flex-col items-center gap-8 text-center">
              <p className="font-serif text-2xl tracking-[0.4em] text-muted-foreground">
                刀
              </p>
              <button
                type="button"
                onClick={startCinematic}
                className="group relative border border-primary/60 px-12 py-5 font-sans text-xs uppercase tracking-[0.4em] text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
              >
                Draw the Blade
              </button>
              <p className="max-w-xs font-sans text-[0.65rem] uppercase tracking-[0.3em] text-muted-foreground/60">
                Sound on · Best experienced with headphones
              </p>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
