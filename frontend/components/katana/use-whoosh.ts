'use client'

/**
 * Synthesizes a katana "whoosh + steel ring" using the Web Audio API so we
 * don't depend on an external whoosh.mp3 asset. Must be triggered from a user
 * gesture (a click) to satisfy browser autoplay policies.
 */
export function playWhoosh() {
  if (typeof window === 'undefined') return
  const AudioCtx =
    window.AudioContext ||
    (window as unknown as { webkitAudioContext: typeof AudioContext })
      .webkitAudioContext
  if (!AudioCtx) return

  const ctx = new AudioCtx()
  const now = ctx.currentTime

  // --- Air whoosh: filtered noise sweeping in pitch ---
  const bufferSize = ctx.sampleRate * 0.9
  const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
  const data = noiseBuffer.getChannelData(0)
  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1
  }
  const noise = ctx.createBufferSource()
  noise.buffer = noiseBuffer

  const band = ctx.createBiquadFilter()
  band.type = 'bandpass'
  band.Q.value = 1.2
  band.frequency.setValueAtTime(400, now)
  band.frequency.exponentialRampToValueAtTime(3600, now + 0.28)
  band.frequency.exponentialRampToValueAtTime(600, now + 0.7)

  const noiseGain = ctx.createGain()
  noiseGain.gain.setValueAtTime(0.0001, now)
  noiseGain.gain.exponentialRampToValueAtTime(0.5, now + 0.12)
  noiseGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.7)

  noise.connect(band).connect(noiseGain).connect(ctx.destination)

  // --- Steel ring: metallic tone on impact ---
  const ringDelay = 0.26
  const osc = ctx.createOscillator()
  osc.type = 'triangle'
  osc.frequency.setValueAtTime(2100, now + ringDelay)
  osc.frequency.exponentialRampToValueAtTime(1400, now + ringDelay + 0.5)

  const ringGain = ctx.createGain()
  ringGain.gain.setValueAtTime(0.0001, now + ringDelay)
  ringGain.gain.exponentialRampToValueAtTime(0.22, now + ringDelay + 0.02)
  ringGain.gain.exponentialRampToValueAtTime(0.0001, now + ringDelay + 1.1)

  osc.connect(ringGain).connect(ctx.destination)

  noise.start(now)
  noise.stop(now + 0.75)
  osc.start(now + ringDelay)
  osc.stop(now + ringDelay + 1.2)

  // tidy up
  window.setTimeout(() => ctx.close().catch(() => {}), 1800)
}
