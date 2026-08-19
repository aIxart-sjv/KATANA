'use client'

const sections = [
  {
    kicker: 'Chapter I — Tamahagane',
    title: 'Born of Fire and Sand',
    body: 'Three days and three nights the smith feeds the tatara furnace, coaxing raw iron sand into tamahagane — the jewel steel that will become a blade.',
    align: 'left' as const,
  },
  {
    kicker: 'Chapter II — The Fold',
    title: 'A Thousand Layers',
    body: 'Folded and hammered again and again, the steel is purified until it holds sixteen thousand layers — strength in the spine, patience in every seam.',
    align: 'right' as const,
  },
  {
    kicker: 'Chapter III — The Hamon',
    title: 'Where the Edge Awakens',
    body: 'Clay-tempered and quenched, the blade curves in the water. Along its edge blooms the hamon — a frozen wave marking the line between soft and unbreakable.',
    align: 'left' as const,
  },
  {
    kicker: 'Chapter IV — Balance',
    title: 'The Weight of Stillness',
    body: 'Guard, collar, and wrap are fitted by hand until the katana rests weightless in the palm — an instrument of restraint far more than force.',
    align: 'right' as const,
  },
]

export function Sections() {
  return (
    <>
      {/* Hero */}
      <section className="relative flex h-screen flex-col items-center justify-center px-6 text-center">
        <p
          data-reveal
          className="mb-6 font-sans text-xs uppercase tracking-[0.5em] text-primary"
        >
          The Soul of the Blade
        </p>
        <h1
          data-reveal
          className="font-serif text-6xl font-semibold tracking-[0.15em] text-foreground text-balance sm:text-7xl md:text-8xl"
        >
          TAMASHII
        </h1>
        <p
          data-reveal
          className="mt-8 max-w-md font-sans text-sm leading-relaxed text-muted-foreground text-pretty"
        >
          A single blade, forged over months, revealed one motion at a time.
        </p>
        <div
          data-reveal
          className="absolute bottom-10 flex flex-col items-center gap-2 text-muted-foreground"
        >
          <span className="font-sans text-[0.65rem] uppercase tracking-[0.3em]">
            Scroll
          </span>
          <span className="h-10 w-px animate-pulse bg-gradient-to-b from-primary to-transparent" />
        </div>
      </section>

      {sections.map((s) => (
        <section
          key={s.title}
          className={`relative flex h-screen items-center px-6 sm:px-12 md:px-20 ${
            s.align === 'right' ? 'justify-end' : 'justify-start'
          }`}
        >
          <div
            data-reveal
            className={`max-w-md ${s.align === 'right' ? 'text-right' : 'text-left'}`}
          >
            <p className="mb-4 font-sans text-xs uppercase tracking-[0.4em] text-primary">
              {s.kicker}
            </p>
            <h2 className="font-serif text-4xl font-medium leading-tight tracking-wide text-foreground text-balance md:text-5xl">
              {s.title}
            </h2>
            <p className="mt-6 font-sans text-base leading-relaxed text-muted-foreground text-pretty">
              {s.body}
            </p>
          </div>
        </section>
      ))}

      {/* Closing / CTA */}
      <section className="relative flex h-screen flex-col items-center justify-center px-6 text-center">
        <p
          data-reveal
          className="mb-4 font-sans text-xs uppercase tracking-[0.4em] text-primary"
        >
          One blade. One owner.
        </p>
        <h2
          data-reveal
          className="font-serif text-5xl font-semibold tracking-[0.12em] text-foreground text-balance md:text-6xl"
        >
          Claim the Steel
        </h2>
        <button
          data-reveal
          type="button"
          className="mt-10 rounded-none border border-primary bg-transparent px-10 py-4 font-sans text-xs uppercase tracking-[0.35em] text-primary transition-colors hover:bg-primary hover:text-primary-foreground"
        >
          Reserve a Commission
        </button>
      </section>
    </>
  )
}
