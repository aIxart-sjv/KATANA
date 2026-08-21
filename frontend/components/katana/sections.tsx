'use client'
import { KatanaDashboard } from '@/components/dashboard/katana-dashboard'

const sections = [
  {
    kicker: 'SYSTEM LAYER 01',
    title: 'EVERY SIGNAL MATTERS.',
    body: 'KATANA observes the operating system at its core. Process activity, system behavior, kernel-level events, and evolving runtime patterns are continuously collected to understand what normal actually looks like.',
    align: 'left' as const,
  },
  {
    kicker: 'SYSTEM LAYER 02',
    title: 'NORMAL IS LEARNED. NOT ASSUMED.',
    body: 'Instead of relying only on static signatures, KATANA builds a behavioral understanding of the system. It establishes a baseline and continuously compares new activity against expected patterns.',
    align: 'right' as const,
  },
  {
    kicker: 'SYSTEM LAYER 03',
    title: 'THE ANOMALY REVEALS ITSELF.',
    body: 'When behavior begins to deviate, KATANA identifies the change. Unusual execution patterns, suspicious system activity, and abnormal behavioral relationships are treated as signals for investigation.',
    align: 'left' as const,
  },
  {
    kicker: 'SYSTEM LAYER 04',
    title: 'ANALYSIS WITHOUT A BLACK BOX.',
    body: 'Detection alone is not intelligence. KATANA is designed to explain why activity was flagged, helping the investigator understand the behavioral factors behind an anomaly instead of receiving an unexplained alert.',
    align: 'right' as const,
  },
]

export function Sections() {
  return (
    <>
      {/* ========================================================
          HERO
          ======================================================== */}

      <section
        className="
          relative
          flex
          h-screen
          flex-col
          items-center
          justify-center
          px-6
          text-center
        "
      >
        <p
          data-reveal
          className="
            mb-6
            font-sans
            text-[10px]
            uppercase
            tracking-[0.55em]
            text-primary
            sm:text-xs
          "
        >
          Kernel Anomaly Tracking
        </p>

        <h1
          data-reveal
          className="
            font-serif
            text-6xl
            font-semibold
            tracking-[0.18em]
            text-foreground
            text-balance
            sm:text-7xl
            md:text-8xl
          "
        >
          KATANA
        </h1>

        <div
          data-reveal
          className="
            mt-8
            h-px
            w-24
            bg-gradient-to-r
            from-transparent
            via-primary
            to-transparent
          "
        />

        <p
          data-reveal
          className="
            mt-8
            max-w-xl
            font-sans
            text-sm
            leading-relaxed
            text-muted-foreground
            text-pretty
          "
        >
          An intelligent Linux security system built to observe behavior,
          detect anomalies, analyze threats, and explain what matters.
        </p>

        <div
          data-reveal
          className="
            absolute
            bottom-10
            flex
            flex-col
            items-center
            gap-2
            text-muted-foreground
          "
        >
          <span
            className="
              font-sans
              text-[0.65rem]
              uppercase
              tracking-[0.3em]
            "
          >
            Begin Analysis
          </span>

          <span
            className="
              h-10
              w-px
              animate-pulse
              bg-gradient-to-b
              from-primary
              to-transparent
            "
          />
        </div>
      </section>

      {/* ========================================================
          KATANA STORY SECTIONS
          ======================================================== */}

      {sections.map((section) => (
        <section
          key={section.title}
          className={`
            relative
            flex
            h-screen
            items-center
            px-6
            sm:px-12
            md:px-20
            ${
              section.align === 'right'
                ? 'justify-end'
                : 'justify-start'
            }
          `}
        >
          <div
            data-reveal
            className={`
              max-w-md
              ${
                section.align === 'right'
                  ? 'text-right'
                  : 'text-left'
              }
            `}
          >
            <p
              className="
                mb-4
                font-sans
                text-[10px]
                uppercase
                tracking-[0.45em]
                text-primary
                sm:text-xs
              "
            >
              {section.kicker}
            </p>

            <h2
              className="
                font-serif
                text-4xl
                font-medium
                leading-tight
                tracking-wide
                text-foreground
                text-balance
                md:text-5xl
              "
            >
              {section.title}
            </h2>

            <p
              className="
                mt-6
                font-sans
                text-base
                leading-relaxed
                text-muted-foreground
                text-pretty
              "
            >
              {section.body}
            </p>
          </div>
        </section>
      ))}

      {/* ========================================================
          FINAL INTRO SECTION
          ======================================================== */}

      <section
        className="
          relative
          flex
          h-screen
          flex-col
          items-center
          justify-center
          px-6
          text-center
        "
      >
        <p
          data-reveal
          className="
            mb-6
            font-sans
            text-[10px]
            uppercase
            tracking-[0.55em]
            text-primary
            sm:text-xs
          "
        >
          KATANA // AI SECURITY CORE
        </p>

        <h2
          data-reveal
          className="
            max-w-6xl
            font-serif
            text-5xl
            font-semibold
            tracking-[0.1em]
            text-foreground
            text-balance
            sm:text-6xl
            md:text-7xl
            lg:text-8xl
          "
        >
          INTELLIGENCE BEHIND THE BLADE.
        </h2>

        <p
          data-reveal
          className="
            mt-8
            max-w-2xl
            font-sans
            text-sm
            leading-relaxed
            text-muted-foreground
            text-pretty
          "
        >
          Continuous monitoring. Behavioral anomaly detection. Threat
          analysis. Explainable AI. Human-controlled investigation.
        </p>

        <div
          data-reveal
          className="
            absolute
            bottom-10
            flex
            flex-col
            items-center
            gap-2
            text-muted-foreground
          "
        >
          <span
            className="
              font-sans
              text-[0.65rem]
              uppercase
              tracking-[0.3em]
            "
          >
            System Interface Ahead
          </span>

          <span
            className="
              h-10
              w-px
              animate-pulse
              bg-gradient-to-b
              from-primary
              to-transparent
            "
          />
        </div>
      </section>
      <KatanaDashboard />
    </>
  )
}