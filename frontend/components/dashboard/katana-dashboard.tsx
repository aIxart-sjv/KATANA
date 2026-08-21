'use client'

import {
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  Activity,
  Bell,
  Bot,
  BrainCircuit,
  ChevronRight,
  CircleAlert,
  Cpu,
  FileSearch,
  Gauge,
  Layers3,
  MonitorCog,
  Radar,
  Settings,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Terminal,
} from 'lucide-react'

import { useKatanaDashboard } from '@/hooks/use-katana-dashboard'


// ===============================================================
// TYPES
// ===============================================================

type PageName =
  | 'Overview'
  | 'Live Monitor'
  | 'Threats'
  | 'Processes'
  | 'Explainability'
  | 'Investigation'
  | 'Settings'


type DashboardEvent = {
  id: string
  timestamp: string
  event_type: string
  process_name: string
  score: number | null
  anomaly_score: number | null
  status: string
  total_events: number
}


type RecentIncident = {
  timestamp?: string
  severity?: string | null
  confidence?: number | null
  score?: number | null
  evidence?: string[]
  recommended_actions?: string[]
  ai_analysis?: {
    risk?: string
    summary?: string
    analysis?: string
    mitre_attack?: string[]
  } | null
}


type ProcessSummary = {
  name: string
  events: number
  anomalyCount: number
  latestScore: number | null
  latestTimestamp: string
  status: string
}


// ===============================================================
// NAVIGATION
// ===============================================================

const navigation: Array<{
  label: PageName
  icon: typeof Gauge
}> = [
  {
    label: 'Overview',
    icon: Gauge,
  },
  {
    label: 'Live Monitor',
    icon: Activity,
  },
  {
    label: 'Threats',
    icon: ShieldAlert,
  },
  {
    label: 'Processes',
    icon: Cpu,
  },
  {
    label: 'Explainability',
    icon: BrainCircuit,
  },
  {
    label: 'Investigation',
    icon: FileSearch,
  },
]


// ===============================================================
// CONSTANTS
// ===============================================================

const MAX_EVENT_HISTORY = 60

const MAX_GRAPH_POINTS = 30


const pageContent: Record<
  PageName,
  {
    eyebrow: string
    title: string
    description: string
  }
> = {
  Overview: {
    eyebrow: 'Command Center',
    title: 'Security Overview',
    description:
      'High-level real-time security posture and behavioral intelligence for this host.',
  },

  'Live Monitor': {
    eyebrow: 'Behavioral Telemetry',
    title: 'Live Monitor',
    description:
      'Continuous frontend history of behavioral scores and recent kernel activity.',
  },

  Threats: {
    eyebrow: 'Threat Intelligence',
    title: 'Threat Assessment',
    description:
      'Active anomalies, incident severity, confidence, and recent behavioral detections.',
  },

  Processes: {
    eyebrow: 'Process Intelligence',
    title: 'Observed Processes',
    description:
      'Processes currently represented in the frontend behavioral event history.',
  },

  Explainability: {
    eyebrow: 'KATANA Intelligence',
    title: 'Explainability',
    description:
      'Why activity was flagged, what evidence exists, and how KATANA interprets the risk.',
  },

  Investigation: {
    eyebrow: 'Human-Guided Response',
    title: 'Investigation',
    description:
      'Deterministic investigation recommendations generated from confirmed behavioral anomalies.',
  },

  Settings: {
    eyebrow: 'System Configuration',
    title: 'Monitoring Settings',
    description:
      'Runtime visibility and frontend monitoring configuration for the current KATANA session.',
  },
}


// ===============================================================
// HELPERS
// ===============================================================

function formatNumber(
  value: number | null | undefined,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return '0'
  }

  return new Intl.NumberFormat().format(
    value,
  )
}


function formatScore(
  value: number | null | undefined,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  return value.toFixed(4)
}


function formatPercent(
  value: number | null | undefined,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  const percentage =
    value <= 1
      ? value * 100
      : value

  return `${percentage.toFixed(1)}%`
}


function formatTime(
  timestamp?: string,
) {
  if (!timestamp) {
    return '—'
  }

  const date =
    new Date(
      timestamp,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return timestamp
  }

  return date.toLocaleTimeString(
    [],
    {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    },
  )
}


function formatRelativeTime(
  timestamp?: string,
) {
  if (!timestamp) {
    return '—'
  }

  const date =
    new Date(
      timestamp,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return timestamp
  }

  const difference =
    Date.now() -
    date.getTime()

  const seconds =
    Math.max(
      0,
      Math.floor(
        difference / 1000,
      ),
    )

  if (seconds < 60) {
    return `${seconds} sec ago`
  }

  const minutes =
    Math.floor(
      seconds / 60,
    )

  if (minutes < 60) {
    return `${minutes} min ago`
  }

  const hours =
    Math.floor(
      minutes / 60,
    )

  return `${hours} hr ago`
}


function normalizeSeverity(
  severity?: string | null,
) {
  if (!severity) {
    return 'LOW'
  }

  return severity.toUpperCase()
}


function normalizeScore(
  score: number | null,
  threshold: number | null,
) {
  if (
    score === null ||
    threshold === null
  ) {
    return 0.5
  }

  const distance =
    Math.abs(
      score -
      threshold,
    )

  const normalized =
    1 -
    Math.min(
      distance * 4,
      1,
    )

  return Math.min(
    Math.max(
      normalized,
      0,
    ),
    1,
  )
}


function getEventStatus(
  score: number | null,
  threshold: number | null,
  severity?: string | null,
) {
  const normalizedSeverity =
    normalizeSeverity(
      severity,
    )

  if (
    normalizedSeverity ===
    'CRITICAL'
  ) {
    return 'CRITICAL'
  }

  if (
    normalizedSeverity ===
    'HIGH'
  ) {
    return 'ANOMALY'
  }

  if (
    normalizedSeverity ===
    'MEDIUM'
  ) {
    return 'WATCH'
  }

  if (
    score !== null &&
    threshold !== null &&
    score <= threshold
  ) {
    return 'ANOMALY'
  }

  return 'NORMAL'
}


function getSystemStatus(
  pipelineRunning: boolean,
  mlStatus: string,
  currentSeverity?: string | null,
) {
  if (!pipelineRunning) {
    return {
      value: 'OFFLINE',
      detail: 'Pipeline is not running',
      accent: 'red' as const,
    }
  }

  const severity =
    normalizeSeverity(
      currentSeverity,
    )

  if (
    severity ===
    'CRITICAL'
  ) {
    return {
      value: 'CRITICAL',
      detail: 'Critical threat detected',
      accent: 'red' as const,
    }
  }

  if (
    severity ===
    'HIGH'
  ) {
    return {
      value: 'ALERT',
      detail:
        'High severity anomaly detected',
      accent: 'red' as const,
    }
  }

  if (
    mlStatus ===
    'learning'
  ) {
    return {
      value: 'LEARNING',
      detail:
        'Building behavioral baseline',
      accent: 'white' as const,
    }
  }

  return {
    value: 'GUARDED',
    detail:
      'Behavior monitoring active',
    accent: 'emerald' as const,
  }
}


// ===============================================================
// DASHBOARD
// ===============================================================

export function KatanaDashboard() {
  const [
    activePage,
    setActivePage,
  ] = useState<PageName>(
    'Overview',
  )

  const [
    events,
    setEvents,
  ] = useState<
    DashboardEvent[]
  >([])


  const {
    data: dashboard,
    loading,
    error,
  } = useKatanaDashboard()


  // -------------------------------------------------------------
  // SAFE DATA EXTRACTION
  // -------------------------------------------------------------

  const system =
    dashboard?.system

  const ml =
    dashboard?.ml

  const dashboardEvents =
    dashboard?.events

  const incidents =
    dashboard?.incidents

  const analysis =
    dashboard?.analysis


  const pipelineRunning =
    Boolean(
      system?.pipeline_running,
    )

  const connected =
    pipelineRunning


  const mlStatus =
    ml?.status ??
    'learning'


  const totalEvents =
    dashboardEvents?.total ??
    0


  const totalIncidents =
    incidents?.total ??
    0


  const currentSeverity =
    incidents?.current_severity ??
    null


  const currentConfidence =
    incidents?.current_confidence ??
    null


  const latestScore =
    ml?.latest_anomaly_score ??
    null


  const threshold =
    ml?.threshold ??
    null


  const recentIncidents:
    RecentIncident[] =
    incidents?.recent ?? []


  const latestAI =
    analysis?.latest_ai_analysis ??
    null


  const latestRecommendations =
    analysis?.latest_recommendations ??
    []


  const latestIncident =
    recentIncidents[0] ??
    null


  // -------------------------------------------------------------
  // FRONTEND EVENT HISTORY
  // -------------------------------------------------------------
  //
  // Backend returns current dashboard state.
  //
  // Frontend polling preserves meaningful snapshots locally.
  //
  // This provides:
  //
  // - Live graph history
  // - Recent activity
  // - Process summaries
  //
  // No backend changes required.
  // -------------------------------------------------------------

  useEffect(
    () => {
      if (!dashboard) {
        return
      }

      if (!pipelineRunning) {
        return
      }

      const timestamp =
        dashboardEvents?.last_event_at ??
        new Date().toISOString()

      const score =
        latestScore

      const status =
        getEventStatus(
          score,
          threshold,
          currentSeverity,
        )

      const severity =
        normalizeSeverity(
          currentSeverity,
        )

      const latestEvidence =
        latestIncident
          ?.evidence
          ?.[0]

      const eventType =
        latestEvidence ??
        (
          severity ===
          'CRITICAL'
            ? 'CRITICAL_BEHAVIORAL_ANOMALY'
            : severity ===
                'HIGH'
              ? 'HIGH_BEHAVIORAL_ANOMALY'
              : severity ===
                  'MEDIUM'
                ? 'BEHAVIORAL_ANOMALY'
                : mlStatus ===
                    'learning'
                  ? 'BASELINE_LEARNING'
                  : 'KERNEL_ACTIVITY'
        )

      const processName =
        latestIncident
          ?.evidence
          ?.[0] ??
        (
          mlStatus ===
          'learning'
            ? 'behavioral-baseline'
            : 'kernel-monitor'
        )

      const snapshotId =
        `${timestamp}-${totalEvents}-${score ?? 'null'}`

      const nextEvent:
        DashboardEvent = {
          id:
            snapshotId,

          timestamp,

          event_type:
            eventType,

          process_name:
            processName,

          score,

          anomaly_score:
            score,

          status,

          total_events:
            totalEvents,
        }

      setEvents(
        (
          previous,
        ) => {
          const latest =
            previous[
              previous.length - 1
            ]

          if (
            latest?.id ===
            nextEvent.id
          ) {
            return previous
          }

          const next =
            [
              ...previous,
              nextEvent,
            ]

          return next.slice(
            -MAX_EVENT_HISTORY,
          )
        },
      )
    },
    [
      dashboard,
      pipelineRunning,
      dashboardEvents?.last_event_at,
      totalEvents,
      latestScore,
      threshold,
      currentSeverity,
      mlStatus,
      latestIncident,
    ],
  )


  // -------------------------------------------------------------
  // SYSTEM STATUS
  // -------------------------------------------------------------

  const systemStatus =
    getSystemStatus(
      pipelineRunning,
      mlStatus,
      currentSeverity,
    )


  // -------------------------------------------------------------
  // ANOMALY QUEUE
  // -------------------------------------------------------------

  const anomalyQueue =
    recentIncidents.slice(
      0,
      10,
    )


  // -------------------------------------------------------------
  // ACTIVITY GRAPH
  // -------------------------------------------------------------

  const graphPoints =
    useMemo(
      () => {
        const source =
          events.slice(
            -MAX_GRAPH_POINTS,
          )

        if (
          source.length === 0
        ) {
          return []
        }

        const normalizedValues =
          source.map(
            (
              event,
            ) =>
              normalizeScore(
                event.score ??
                  event.anomaly_score ??
                  null,
                threshold,
              ),
          )

        const minValue =
          Math.min(
            ...normalizedValues,
          )

        const maxValue =
          Math.max(
            ...normalizedValues,
          )

        const range =
          maxValue -
          minValue

        return source.map(
          (
            event,
            index,
          ) => {
            const rawValue =
              normalizeScore(
                event.score ??
                  event.anomaly_score ??
                  null,
                threshold,
              )

            const normalized =
              range > 0.0001
                ? (
                    rawValue -
                    minValue
                  ) /
                  range
                : 0.5

            const x =
              source.length === 1
                ? 500
                : (
                    index /
                    (
                      source.length -
                      1
                    )
                  ) *
                  1000

            const y =
              260 -
              normalized *
                220

            return {
              x,
              y,
              normalized,
              event,
            }
          },
        )
      },
      [
        events,
        threshold,
      ],
    )


  const graphLine =
    graphPoints.length > 0
      ? graphPoints
          .map(
            (
              point,
              index,
            ) =>
              `${
                index === 0
                  ? 'M'
                  : 'L'
              }${point.x.toFixed(
                1,
              )} ${point.y.toFixed(
                1,
              )}`,
          )
          .join(
            ' ',
          )
      : ''


  const graphArea =
    graphLine
      ? `${graphLine} L1000 300 L0 300 Z`
      : ''


  // -------------------------------------------------------------
  // AI DATA
  // -------------------------------------------------------------

  const aiSummary =
    latestAI?.summary ??
    latestAI?.analysis ??
    (
      mlStatus ===
      'learning'
        ? 'KATANA is currently learning the normal behavioral baseline for this host.'
        : totalIncidents > 0
          ? 'A behavioral anomaly was detected and requires investigation.'
          : 'No recent anomaly requires AI escalation.'
    )


  const aiRisk =
    latestAI?.risk ??
    currentSeverity ??
    'LOW'


  const primarySignal =
    latestIncident
      ?.evidence
      ?.[0] ??
    'No active anomaly evidence'


  const mitreTechniques =
    latestAI?.mitre_attack ??
    latestIncident
      ?.ai_analysis
      ?.mitre_attack ??
    []


  const baselineProgress =
    ml?.baseline_required &&
    ml.baseline_required > 0
      ? Math.min(
          100,
          (
            (
              ml.baseline_samples ??
              0
            ) /
              ml.baseline_required
          ) *
            100,
        )
      : 0


  // -------------------------------------------------------------
  // PROCESS INTELLIGENCE
  // -------------------------------------------------------------

  const processSummaries =
    useMemo<
      ProcessSummary[]
    >(
      () => {
        const processMap =
          new Map<
            string,
            ProcessSummary
          >()

        for (
          const event of events
        ) {
          const name =
            event.process_name ||
            'unknown-process'

          const existing =
            processMap.get(
              name,
            )

          const anomaly =
            event.status ===
              'ANOMALY' ||
            event.status ===
              'CRITICAL'

          if (existing) {
            existing.events += 1

            if (anomaly) {
              existing.anomalyCount +=
                1
            }

            existing.latestScore =
              event.score ??
              event.anomaly_score

            existing.latestTimestamp =
              event.timestamp

            existing.status =
              event.status

            continue
          }

          processMap.set(
            name,
            {
              name,
              events: 1,
              anomalyCount:
                anomaly
                  ? 1
                  : 0,
              latestScore:
                event.score ??
                event.anomaly_score,
              latestTimestamp:
                event.timestamp,
              status:
                event.status,
            },
          )
        }

        return Array.from(
          processMap.values(),
        ).sort(
          (
            a,
            b,
          ) => {
            if (
              b.anomalyCount !==
              a.anomalyCount
            ) {
              return (
                b.anomalyCount -
                a.anomalyCount
              )
            }

            return (
              b.events -
              a.events
            )
          },
        )
      },
      [
        events,
      ],
    )


  // -------------------------------------------------------------
  // PAGE DATA
  // -------------------------------------------------------------

  const currentPage =
    pageContent[
      activePage
    ]


  // =============================================================
  // PAGE RENDERING
  // =============================================================

  const renderPage =
    () => {
      switch (
        activePage
      ) {
        case 'Overview':
          return (
            <OverviewPage
              connected={
                connected
              }
              loading={
                loading
              }
              systemStatus={
                systemStatus
              }
              totalIncidents={
                totalIncidents
              }
              totalEvents={
                totalEvents
              }
              currentSeverity={
                currentSeverity
              }
              currentConfidence={
                currentConfidence
              }
              latestScore={
                latestScore
              }
              threshold={
                threshold
              }
              events={
                events
              }
              anomalyQueue={
                anomalyQueue
              }
              aiSummary={
                aiSummary
              }
              aiRisk={
                aiRisk
              }
              primarySignal={
                primarySignal
              }
              onNavigate={
                setActivePage
              }
            />
          )

        case 'Live Monitor':
          return (
            <LiveMonitorPage
              connected={
                connected
              }
              loading={
                loading
              }
              graphPoints={
                graphPoints
              }
              graphLine={
                graphLine
              }
              graphArea={
                graphArea
              }
              latestScore={
                latestScore
              }
              threshold={
                threshold
              }
              totalEvents={
                totalEvents
              }
              events={
                events
              }
            />
          )

        case 'Threats':
          return (
            <ThreatsPage
              anomalyQueue={
                anomalyQueue
              }
              totalIncidents={
                totalIncidents
              }
              currentSeverity={
                currentSeverity
              }
              currentConfidence={
                currentConfidence
              }
              latestScore={
                latestScore
              }
              threshold={
                threshold
              }
              primarySignal={
                primarySignal
              }
              onNavigate={
                setActivePage
              }
            />
          )

        case 'Processes':
          return (
            <ProcessesPage
              processes={
                processSummaries
              }
              loading={
                loading
              }
              totalEvents={
                totalEvents
              }
            />
          )

        case 'Explainability':
          return (
            <ExplainabilityPage
              aiSummary={
                aiSummary
              }
              aiRisk={
                aiRisk
              }
              currentConfidence={
                currentConfidence
              }
              primarySignal={
                primarySignal
              }
              latestAI={
                latestAI
              }
              latestIncident={
                latestIncident
              }
              mitreTechniques={
                mitreTechniques
              }
              onNavigate={
                setActivePage
              }
            />
          )

        case 'Investigation':
          return (
            <InvestigationPage
              latestRecommendations={
                latestRecommendations
              }
              anomalyQueue={
                anomalyQueue
              }
              onNavigate={
                setActivePage
              }
            />
          )

        case 'Settings':
          return (
            <SettingsPage
              pipelineRunning={
                pipelineRunning
              }
              mlStatus={
                mlStatus
              }
              baselineProgress={
                baselineProgress
              }
              eventHistorySize={
                events.length
              }
              totalEvents={
                totalEvents
              }
              totalIncidents={
                totalIncidents
              }
            />
          )

        default:
          return null
      }
    }


  return (
    <section
      id="dashboard"
      className="relative min-h-screen bg-[#050506] px-4 py-10 text-[#f2f2f3] md:px-8 lg:px-12"
    >
      <div className="mx-auto max-w-[1600px]">


        {/* =====================================================
            TOP SYSTEM DIVIDER
            ===================================================== */}

        <div className="mb-8 flex items-center gap-4">

          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/15 to-transparent" />

          <div className="flex items-center gap-3">

            <div
              className={`h-2 w-2 rounded-full shadow-[0_0_12px_rgba(239,68,68,0.9)] ${
                connected
                  ? 'animate-pulse bg-red-500'
                  : 'bg-white/30'
              }`}
            />

            <span className="font-mono text-[10px] uppercase tracking-[0.35em] text-white/40">
              Security Interface
            </span>

          </div>

          <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/15 to-transparent" />

        </div>


        {/* =====================================================
            DASHBOARD SHELL
            ===================================================== */}

        <div className="overflow-hidden border border-white/10 bg-[#0a0a0d]/90 shadow-[0_0_80px_rgba(0,0,0,0.7)] backdrop-blur-xl">


          {/* ===================================================
              TOP BAR
              =================================================== */}

          <header className="flex min-h-20 items-center justify-between border-b border-white/10 px-5 md:px-7">

            <div className="flex items-center gap-5">

              <div className="relative flex h-10 w-10 items-center justify-center border border-red-500/50 bg-red-500/5">

                <span className="font-serif text-xl text-red-400">
                  刀
                </span>

                <div className="absolute inset-0 animate-pulse border border-red-500/20" />

              </div>


              <div>

                <div className="flex items-center gap-3">

                  <h2 className="font-serif text-lg tracking-[0.28em] text-white">
                    KATANA
                  </h2>

                  <span
                    className={`hidden border px-2 py-1 font-mono text-[8px] uppercase tracking-[0.2em] sm:inline-block ${
                      pipelineRunning
                        ? 'border-red-500/30 bg-red-500/10 text-red-400'
                        : 'border-white/10 bg-white/[0.03] text-white/40'
                    }`}
                  >
                    {
                      pipelineRunning
                        ? 'Online'
                        : 'Offline'
                    }
                  </span>

                </div>


                <p className="mt-1 font-mono text-[9px] uppercase tracking-[0.2em] text-white/35">
                  Kernel Anomaly Tracking & Neural Assistant
                </p>

              </div>

            </div>


            <div className="hidden items-center gap-8 md:flex">

              <div className="text-right">

                <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
                  Monitoring
                </p>

                <div className="mt-1 flex items-center justify-end gap-2">

                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      pipelineRunning
                        ? 'animate-pulse bg-emerald-400'
                        : 'bg-red-500'
                    }`}
                  />

                  <span className="font-mono text-xs text-white/80">
                    {
                      pipelineRunning
                        ? 'ACTIVE'
                        : 'STOPPED'
                    }
                  </span>

                </div>

              </div>


              <div className="h-8 w-px bg-white/10" />


              <div className="text-right">

                <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
                  ML State
                </p>

                <p className="mt-1 font-mono text-xs text-white/80">
                  {
                    mlStatus.toUpperCase()
                  }
                </p>

              </div>


              <Bell
                className={`h-4 w-4 ${
                  totalIncidents > 0
                    ? 'text-red-400'
                    : 'text-white/45'
                }`}
              />

            </div>

          </header>


          {/* ===================================================
              MAIN LAYOUT
              =================================================== */}

          <div className="flex min-h-[850px]">


            {/* =================================================
                SIDEBAR
                ================================================= */}

            <aside className="hidden w-[235px] flex-col border-r border-white/10 bg-black/20 lg:flex">

              <div className="flex-1 px-3 py-6">

                <p className="mb-4 px-3 font-mono text-[9px] uppercase tracking-[0.25em] text-white/25">
                  Intelligence
                </p>


                <nav className="space-y-1">

                  {
                    navigation.map(
                      (
                        item,
                      ) => {
                        const Icon =
                          item.icon

                        const active =
                          activePage ===
                          item.label

                        return (
                          <button
                            key={
                              item.label
                            }
                            type="button"
                            onClick={() =>
                              setActivePage(
                                item.label,
                              )
                            }
                            className={`group flex w-full items-center gap-3 border px-3 py-3 text-left transition-all ${
                              active
                                ? 'border-red-500/25 bg-red-500/[0.08] text-white'
                                : 'border-transparent text-white/40 hover:border-white/10 hover:bg-white/[0.025] hover:text-white/80'
                            }`}
                          >

                            <Icon
                              className={`h-4 w-4 ${
                                active
                                  ? 'text-red-400'
                                  : 'text-white/30 group-hover:text-white/70'
                              }`}
                            />

                            <span className="font-mono text-[11px] uppercase tracking-[0.08em]">
                              {
                                item.label
                              }
                            </span>

                            {
                              active && (
                                <ChevronRight className="ml-auto h-3.5 w-3.5 text-red-400" />
                              )
                            }

                          </button>
                        )
                      },
                    )
                  }

                </nav>


                <div className="my-7 h-px bg-white/10" />


                <p className="mb-4 px-3 font-mono text-[9px] uppercase tracking-[0.25em] text-white/25">
                  System
                </p>


                <button
                  type="button"
                  onClick={() =>
                    setActivePage(
                      'Settings',
                    )
                  }
                  className={`group flex w-full items-center gap-3 border px-3 py-3 text-left transition ${
                    activePage ===
                    'Settings'
                      ? 'border-red-500/25 bg-red-500/[0.08] text-white'
                      : 'border-transparent text-white/40 hover:border-white/10 hover:bg-white/[0.025] hover:text-white/80'
                  }`}
                >

                  <Settings
                    className={`h-4 w-4 ${
                      activePage ===
                      'Settings'
                        ? 'text-red-400'
                        : 'text-white/30 group-hover:text-white/70'
                    }`}
                  />

                  <span className="font-mono text-[11px] uppercase tracking-[0.08em]">
                    Settings
                  </span>

                  {
                    activePage ===
                    'Settings' && (
                      <ChevronRight className="ml-auto h-3.5 w-3.5 text-red-400" />
                    )
                  }

                </button>

              </div>


              <div className="border-t border-white/10 p-4">

                <div className="border border-white/10 bg-white/[0.02] p-3">

                  <div className="flex items-center justify-between">

                    <span className="font-mono text-[9px] uppercase tracking-widest text-white/35">
                      Baseline Progress
                    </span>

                    <span className="font-mono text-xs text-emerald-400">
                      {
                        mlStatus ===
                        'learning'
                          ? `${baselineProgress.toFixed(
                              0,
                            )}%`
                          : 'READY'
                      }
                    </span>

                  </div>


                  <div className="mt-3 h-1 bg-white/10">

                    <div
                      className="h-full bg-gradient-to-r from-red-500 to-emerald-400 transition-all duration-500"
                      style={{
                        width:
                          mlStatus ===
                          'learning'
                            ? `${baselineProgress}%`
                            : '100%',
                      }}
                    />

                  </div>

                </div>

              </div>

            </aside>


            {/* =================================================
                CONTENT
                ================================================= */}

            <main className="min-w-0 flex-1 p-5 md:p-7 lg:p-8">


              {/* PAGE TITLE */}

              <div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end">

                <div>

                  <div className="mb-3 flex items-center gap-2">

                    <div
                      className={`h-1.5 w-1.5 ${
                        pipelineRunning
                          ? 'bg-red-500'
                          : 'bg-white/30'
                      }`}
                    />

                    <span className="font-mono text-[10px] uppercase tracking-[0.28em] text-red-400">
                      {
                        currentPage.eyebrow
                      }
                    </span>

                  </div>


                  <h1 className="font-serif text-3xl tracking-[0.08em] text-white md:text-4xl">
                    {
                      currentPage.title
                    }
                  </h1>


                  <p className="mt-3 max-w-2xl font-mono text-xs leading-6 text-white/35">
                    {
                      currentPage.description
                    }
                  </p>


                  {
                    error && (
                      <p className="mt-3 font-mono text-[10px] text-red-400">
                        Backend connection error:{' '}
                        {
                          error
                        }
                      </p>
                    )
                  }

                </div>


                <div className="flex items-center gap-3 border border-white/10 bg-white/[0.02] px-4 py-3">

                  <MonitorCog className="h-4 w-4 text-white/40" />

                  <div>

                    <p className="font-mono text-[8px] uppercase tracking-widest text-white/30">
                      Connection
                    </p>

                    <p className="mt-1 font-mono text-xs text-white/80">
                      {
                        connected
                          ? 'LIVE'
                          : 'DISCONNECTED'
                      }
                    </p>

                  </div>


                  <div className="mx-2 h-7 w-px bg-white/10" />


                  <div>

                    <p className="font-mono text-[8px] uppercase tracking-widest text-white/30">
                      Events
                    </p>

                    <p className="mt-1 font-mono text-xs text-white/80">
                      {
                        formatNumber(
                          totalEvents,
                        )
                      }
                    </p>

                  </div>

                </div>

              </div>


              {/* ACTIVE PAGE */}

              {
                renderPage()
              }

            </main>

          </div>

        </div>


        {/* =====================================================
            BOTTOM LABEL
            ===================================================== */}

        <div className="mt-6 flex items-center justify-between px-2">

          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-white/20">
            KATANA // AI-assisted defensive intelligence
          </span>


          <div className="flex items-center gap-2">

            <Shield className="h-3 w-3 text-red-500/50" />

            <span className="font-mono text-[9px] uppercase tracking-widest text-white/25">
              Human Controlled
            </span>

          </div>

        </div>

      </div>
    </section>
  )
}


// ===============================================================
// OVERVIEW PAGE
// ===============================================================

function OverviewPage({
  connected,
  loading,
  systemStatus,
  totalIncidents,
  totalEvents,
  currentSeverity,
  currentConfidence,
  latestScore,
  threshold,
  events,
  anomalyQueue,
  aiSummary,
  aiRisk,
  primarySignal,
  onNavigate,
}: {
  connected: boolean
  loading: boolean
  systemStatus: {
    value: string
    detail: string
    accent:
      | 'emerald'
      | 'red'
      | 'white'
  }
  totalIncidents: number
  totalEvents: number
  currentSeverity: string | null
  currentConfidence: number | null
  latestScore: number | null
  threshold: number | null
  events: DashboardEvent[]
  anomalyQueue: RecentIncident[]
  aiSummary: string
  aiRisk: string
  primarySignal: string
  onNavigate: (
    page: PageName,
  ) => void
}) {
  return (
    <div>


      {/* METRICS */}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <MetricCard
          icon={ShieldCheck}
          label="System Status"
          value={
            systemStatus.value
          }
          detail={
            systemStatus.detail
          }
          accent={
            systemStatus.accent
          }
        />


        <MetricCard
          icon={CircleAlert}
          label="Incidents"
          value={
            String(
              totalIncidents,
            ).padStart(
              2,
              '0',
            )
          }
          detail={
            currentSeverity
              ? `Current severity: ${currentSeverity}`
              : 'No active incidents'
          }
          accent={
            currentSeverity
              ? 'red'
              : 'emerald'
          }
        />


        <MetricCard
          icon={Layers3}
          label="Kernel Events"
          value={
            formatNumber(
              totalEvents,
            )
          }
          detail={
            events.length > 0
              ? `Frontend history: ${events.length}`
              : 'Waiting for activity'
          }
          accent="white"
        />


        <MetricCard
          icon={BrainCircuit}
          label="AI Confidence"
          value={
            formatPercent(
              currentConfidence,
            )
          }
          detail={
            currentSeverity
              ? `${currentSeverity} incident confidence`
              : 'No active incident'
          }
          accent={
            currentSeverity
              ? 'red'
              : 'white'
          }
        />

      </div>


      {/* OVERVIEW INTELLIGENCE */}

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">


        {/* CURRENT POSTURE */}

        <div className="border border-white/10 bg-black/20">

          <div className="border-b border-white/10 px-5 py-4">

            <div className="flex items-center gap-3">

              <Radar className="h-4 w-4 text-red-400" />

              <div>

                <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/85">
                  Current Security Posture
                </h3>

                <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
                  Condensed behavioral intelligence
                </p>

              </div>

            </div>

          </div>


          <div className="p-5">

            <div className="grid gap-4 md:grid-cols-3">

              <CompactStat
                label="Latest Score"
                value={
                  formatScore(
                    latestScore,
                  )
                }
              />

              <CompactStat
                label="Threshold"
                value={
                  formatScore(
                    threshold,
                  )
                }
              />

              <CompactStat
                label="AI Risk"
                value={
                  normalizeSeverity(
                    aiRisk,
                  )
                }
                danger={
                  normalizeSeverity(
                    aiRisk,
                  ) !==
                  'LOW'
                }
              />

            </div>


            <div className="mt-5 border-l border-red-500/50 pl-4">

              <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
                Current Assessment
              </p>

              <p className="mt-3 text-lg leading-8 text-white/80">
                {
                  aiSummary
                }
              </p>

            </div>


            <div className="mt-6 flex flex-wrap gap-3">

              <button
                type="button"
                onClick={() =>
                  onNavigate(
                    'Live Monitor',
                  )
                }
                className="border border-white/10 bg-white/[0.02] px-4 py-3 font-mono text-[9px] uppercase tracking-[0.18em] text-white/60 transition hover:border-red-500/30 hover:text-white"
              >
                Open Live Monitor
              </button>

              <button
                type="button"
                onClick={() =>
                  onNavigate(
                    'Explainability',
                  )
                }
                className="border border-red-500/30 bg-red-500/10 px-4 py-3 font-mono text-[9px] uppercase tracking-[0.18em] text-red-300 transition hover:bg-red-500 hover:text-black"
              >
                View AI Analysis
              </button>

            </div>

          </div>

        </div>


        {/* ACTIVE SIGNAL */}

        <div className="border border-red-500/20 bg-gradient-to-b from-red-500/[0.05] to-transparent p-5">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center border border-red-500/30 bg-red-500/10">

              <Bot className="h-5 w-5 text-red-400" />

            </div>

            <div>

              <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-red-400">
                KATANA Intelligence
              </p>

              <h3 className="mt-1 font-serif text-lg text-white">
                Active Signal
              </h3>

            </div>

          </div>


          <div className="mt-7">

            <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
              Primary Signal
            </p>

            <p className="mt-3 font-mono text-sm leading-7 text-white/80">
              {
                primarySignal
              }
            </p>

          </div>


          <div className="mt-7 border-t border-white/10 pt-5">

            <div className="flex items-center justify-between">

              <span className="font-mono text-[9px] uppercase tracking-widest text-white/30">
                Monitoring
              </span>

              <span
                className={`font-mono text-[10px] ${
                  connected
                    ? 'text-emerald-400'
                    : 'text-red-400'
                }`}
              >
                {
                  connected
                    ? 'ACTIVE'
                    : 'OFFLINE'
                }
              </span>

            </div>


            <div className="mt-4 flex items-center justify-between">

              <span className="font-mono text-[9px] uppercase tracking-widest text-white/30">
                Stream
              </span>

              <span className="font-mono text-[10px] text-white/70">
                {
                  loading
                    ? 'LOADING'
                    : `${events.length} SNAPSHOTS`
                }
              </span>

            </div>

          </div>

        </div>

      </div>


      {/* RECENT ACTIVITY */}

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">

        <RecentEventsTable
          events={
            events
          }
          loading={
            loading
          }
          limit={
            5
          }
          compact
          onViewAll={() =>
            onNavigate(
              'Live Monitor',
            )
          }
        />


        <ThreatQueue
          anomalyQueue={
            anomalyQueue.slice(
              0,
              3,
            )
          }
          onAnalyze={() =>
            onNavigate(
              'Threats',
            )
          }
          compact
        />

      </div>

    </div>
  )
}


// ===============================================================
// LIVE MONITOR PAGE
// ===============================================================

function LiveMonitorPage({
  connected,
  loading,
  graphPoints,
  graphLine,
  graphArea,
  latestScore,
  threshold,
  totalEvents,
  events,
}: {
  connected: boolean
  loading: boolean
  graphPoints: Array<{
    x: number
    y: number
    normalized: number
    event: DashboardEvent
  }>
  graphLine: string
  graphArea: string
  latestScore: number | null
  threshold: number | null
  totalEvents: number
  events: DashboardEvent[]
}) {
  return (
    <div>

      <div className="border border-white/10 bg-black/20">

        <div className="flex flex-col justify-between gap-4 border-b border-white/10 px-5 py-4 md:flex-row md:items-center">

          <div>

            <div className="flex items-center gap-3">

              <Activity className="h-4 w-4 text-red-400" />

              <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/85">
                Live Kernel Activity
              </h3>

            </div>


            <p className="mt-2 font-mono text-[9px] uppercase tracking-wider text-white/30">
              Frontend behavioral history preserved from dashboard polling
            </p>

          </div>


          <div className="flex items-center gap-2">

            <span
              className={`h-1.5 w-1.5 rounded-full ${
                connected
                  ? 'animate-pulse bg-red-500'
                  : 'bg-white/20'
              }`}
            />

            <span className="font-mono text-[9px] uppercase tracking-widest text-red-400">
              {
                connected
                  ? 'Live'
                  : 'Offline'
              }
            </span>

          </div>

        </div>


        {/* GRAPH */}

        <div className="relative h-[380px] overflow-hidden border-b border-white/10">

          <div className="absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(255,255,255,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.08)_1px,transparent_1px)] [background-size:52px_52px]" />


          {
            graphPoints.length >
            1 ? (
              <svg
                viewBox="0 0 1000 300"
                preserveAspectRatio="none"
                className="relative h-full w-full"
              >

                <defs>

                  <linearGradient
                    id="activityGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >

                    <stop
                      offset="0%"
                      stopColor="#ef4444"
                      stopOpacity="0.35"
                    />

                    <stop
                      offset="100%"
                      stopColor="#ef4444"
                      stopOpacity="0"
                    />

                  </linearGradient>

                </defs>


                <path
                  d={
                    graphArea
                  }
                  fill="url(#activityGradient)"
                />


                <path
                  d={
                    graphLine
                  }
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="3"
                  vectorEffect="non-scaling-stroke"
                />


                {
                  graphPoints.map(
                    (
                      point,
                    ) => (
                      <circle
                        key={
                          point.event.id
                        }
                        cx={
                          point.x
                        }
                        cy={
                          point.y
                        }
                        r="4"
                        fill="#ef4444"
                      />
                    ),
                  )
                }

              </svg>
            ) : (
              <div className="relative flex h-full items-center justify-center">

                <p className="font-mono text-[10px] uppercase tracking-widest text-white/25">
                  {
                    loading
                      ? 'Loading behavioral stream'
                      : 'Collecting live dashboard history'
                  }
                </p>

              </div>
            )
          }


          {
            latestScore !==
            null && (
              <div className="absolute left-5 top-5 border border-red-500/30 bg-black/60 px-3 py-2 backdrop-blur">

                <p className="font-mono text-[8px] uppercase tracking-widest text-red-400">
                  Latest Score
                </p>

                <p className="mt-1 font-mono text-xs text-white">
                  {
                    formatScore(
                      latestScore,
                    )
                  }
                </p>

              </div>
            )
          }


          <div className="absolute bottom-5 right-5 border border-white/10 bg-black/60 px-3 py-2 backdrop-blur">

            <p className="font-mono text-[8px] uppercase tracking-widest text-white/30">
              History
            </p>

            <p className="mt-1 font-mono text-xs text-white/80">
              {
                events.length
              } snapshots
            </p>

          </div>

        </div>


        <div className="grid grid-cols-3 divide-x divide-white/10">

          <ActivityStat
            label="Total Events"
            value={
              formatNumber(
                totalEvents,
              )
            }
          />

          <ActivityStat
            label="Anomaly Score"
            value={
              formatScore(
                latestScore,
              )
            }
          />

          <ActivityStat
            label="Threshold"
            value={
              formatScore(
                threshold,
              )
            }
          />

        </div>

      </div>


      <div className="mt-5">

        <RecentEventsTable
          events={
            events
          }
          loading={
            loading
          }
        />

      </div>

    </div>
  )
}


// ===============================================================
// THREATS PAGE
// ===============================================================

function ThreatsPage({
  anomalyQueue,
  totalIncidents,
  currentSeverity,
  currentConfidence,
  latestScore,
  threshold,
  primarySignal,
  onNavigate,
}: {
  anomalyQueue: RecentIncident[]
  totalIncidents: number
  currentSeverity: string | null
  currentConfidence: number | null
  latestScore: number | null
  threshold: number | null
  primarySignal: string
  onNavigate: (
    page: PageName,
  ) => void
}) {
  return (
    <div>

      <div className="grid gap-4 md:grid-cols-4">

        <MetricCard
          icon={ShieldAlert}
          label="Total Incidents"
          value={
            formatNumber(
              totalIncidents,
            )
          }
          detail="Confirmed behavioral incidents"
          accent={
            totalIncidents > 0
              ? 'red'
              : 'emerald'
          }
        />

        <MetricCard
          icon={Radar}
          label="Current Severity"
          value={
            normalizeSeverity(
              currentSeverity,
            )
          }
          detail="Latest incident classification"
          accent={
            currentSeverity
              ? 'red'
              : 'white'
          }
        />

        <MetricCard
          icon={BrainCircuit}
          label="Confidence"
          value={
            formatPercent(
              currentConfidence,
            )
          }
          detail="Threat engine confidence"
          accent={
            currentConfidence !==
            null
              ? 'red'
              : 'white'
          }
        />

        <MetricCard
          icon={Activity}
          label="Latest Score"
          value={
            formatScore(
              latestScore,
            )
          }
          detail={
            `Threshold: ${formatScore(
              threshold,
            )}`
          }
          accent="white"
        />

      </div>


      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(330px,0.8fr)]">

        <ThreatQueue
          anomalyQueue={
            anomalyQueue
          }
          onAnalyze={() =>
            onNavigate(
              'Investigation',
            )
          }
        />


        <div className="border border-red-500/20 bg-gradient-to-b from-red-500/[0.06] to-transparent p-5">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center border border-red-500/30 bg-red-500/10">

              <CircleAlert className="h-5 w-5 text-red-400" />

            </div>

            <div>

              <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-red-400">
                Current Threat Context
              </p>

              <h3 className="mt-1 font-serif text-lg text-white">
                Primary Detection
              </h3>

            </div>

          </div>


          <div className="mt-8 border-l border-red-500/50 pl-4">

            <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
              Primary Signal
            </p>

            <p className="mt-3 font-mono text-sm leading-7 text-white/80">
              {
                primarySignal
              }
            </p>

          </div>


          <div className="mt-8 space-y-4">

            <IntelligenceRow
              label="Severity"
              value={
                normalizeSeverity(
                  currentSeverity,
                )
              }
              danger={
                Boolean(
                  currentSeverity,
                )
              }
            />

            <IntelligenceRow
              label="Confidence"
              value={
                formatPercent(
                  currentConfidence,
                )
              }
              danger={
                currentConfidence !==
                null
              }
            />

            <IntelligenceRow
              label="Anomaly Score"
              value={
                formatScore(
                  latestScore,
                )
              }
            />

            <IntelligenceRow
              label="Threshold"
              value={
                formatScore(
                  threshold,
                )
              }
            />

          </div>


          <button
            type="button"
            onClick={() =>
              onNavigate(
                'Investigation',
              )
            }
            className="mt-7 flex w-full items-center justify-center gap-2 border border-red-500/40 bg-red-500/10 px-4 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-red-300 transition hover:bg-red-500 hover:text-black"
          >
            Open Investigation

            <ChevronRight className="h-3.5 w-3.5" />

          </button>

        </div>

      </div>

    </div>
  )
}


// ===============================================================
// PROCESSES PAGE
// ===============================================================

function ProcessesPage({
  processes,
  loading,
  totalEvents,
}: {
  processes: ProcessSummary[]
  loading: boolean
  totalEvents: number
}) {
  return (
    <div>

      <div className="grid gap-4 md:grid-cols-3">

        <MetricCard
          icon={Cpu}
          label="Observed Processes"
          value={
            formatNumber(
              processes.length,
            )
          }
          detail="Unique names in frontend history"
          accent="white"
        />

        <MetricCard
          icon={Layers3}
          label="Frontend Events"
          value={
            formatNumber(
              totalEvents,
            )
          }
          detail="Total events reported by backend"
          accent="white"
        />

        <MetricCard
          icon={ShieldAlert}
          label="Processes Flagged"
          value={
            formatNumber(
              processes.filter(
                (
                  process,
                ) =>
                  process.anomalyCount >
                  0,
              ).length,
            )
          }
          detail="Processes associated with anomaly snapshots"
          accent={
            processes.some(
              (
                process,
              ) =>
                process.anomalyCount >
                0,
            )
              ? 'red'
              : 'emerald'
          }
        />

      </div>


      <div className="mt-5 border border-white/10 bg-black/20">

        <div className="border-b border-white/10 px-5 py-4">

          <div className="flex items-center gap-3">

            <Cpu className="h-4 w-4 text-red-400" />

            <div>

              <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/85">
                Process Intelligence
              </h3>

              <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
                Derived from current frontend behavioral history
              </p>

            </div>

          </div>

        </div>


        <div className="overflow-x-auto">

          <table className="w-full min-w-[800px] text-left">

            <thead>

              <tr className="border-b border-white/10">

                <TableHead>
                  Process
                </TableHead>

                <TableHead>
                  Observations
                </TableHead>

                <TableHead>
                  Anomalies
                </TableHead>

                <TableHead>
                  Latest Score
                </TableHead>

                <TableHead>
                  Last Seen
                </TableHead>

                <TableHead>
                  Status
                </TableHead>

              </tr>

            </thead>


            <tbody>

              {
                processes.length >
                0 ? (
                  processes.map(
                    (
                      process,
                    ) => (
                      <tr
                        key={
                          process.name
                        }
                        className="border-b border-white/[0.06] transition hover:bg-white/[0.025]"
                      >

                        <td className="px-5 py-4 font-mono text-[11px] text-white/80">
                          {
                            process.name
                          }
                        </td>


                        <td className="px-5 py-4 font-mono text-[10px] text-white/55">
                          {
                            process.events
                          }
                        </td>


                        <td className="px-5 py-4 font-mono text-[10px] text-white/55">
                          {
                            process.anomalyCount
                          }
                        </td>


                        <td className="px-5 py-4 font-mono text-[10px] text-white/70">
                          {
                            formatScore(
                              process.latestScore,
                            )
                          }
                        </td>


                        <td className="px-5 py-4 font-mono text-[10px] text-white/40">
                          {
                            formatRelativeTime(
                              process.latestTimestamp,
                            )
                          }
                        </td>


                        <td className="px-5 py-4">

                          <EventStatus
                            status={
                              process.status
                            }
                          />

                        </td>

                      </tr>
                    ),
                  )
                ) : (
                  <tr>

                    <td
                      colSpan={
                        6
                      }
                      className="px-5 py-16 text-center font-mono text-[10px] uppercase tracking-widest text-white/25"
                    >
                      {
                        loading
                          ? 'Loading process intelligence...'
                          : 'No process information has been observed yet'
                      }
                    </td>

                  </tr>
                )
              }

            </tbody>

          </table>

        </div>

      </div>


      <div className="mt-4 border border-amber-500/10 bg-amber-500/[0.025] px-4 py-3">

        <p className="font-mono text-[9px] leading-6 text-white/35">
          Process data is currently derived from the frontend event history.
          KATANA is not claiming these are complete operating-system process
          records. Dedicated process telemetry can be added later when the
          backend exposes real process-level data.
        </p>

      </div>

    </div>
  )
}


// ===============================================================
// EXPLAINABILITY PAGE
// ===============================================================

function ExplainabilityPage({
  aiSummary,
  aiRisk,
  currentConfidence,
  primarySignal,
  latestAI,
  latestIncident,
  mitreTechniques,
  onNavigate,
}: {
  aiSummary: string
  aiRisk: string
  currentConfidence: number | null
  primarySignal: string
  latestAI: {
    risk?: string
    summary?: string
    analysis?: string
    mitre_attack?: string[]
  } | null
  latestIncident: RecentIncident | null
  mitreTechniques: string[]
  onNavigate: (
    page: PageName,
  ) => void
}) {
  const explanation =
    latestAI?.analysis ??
    latestIncident
      ?.ai_analysis
      ?.analysis ??
    latestIncident
      ?.evidence
      ?.join(
        ' ',
      ) ??
    'No AI escalation has been required for the current system state.'


  const evidence =
    latestIncident
      ?.evidence ??
    []


  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(330px,0.8fr)]">


      {/* AI ASSESSMENT */}

      <div className="relative overflow-hidden border border-red-500/20 bg-gradient-to-b from-red-500/[0.06] to-transparent">

        <div className="absolute right-0 top-0 h-52 w-52 rounded-full bg-red-500/10 blur-[90px]" />


        <div className="relative border-b border-white/10 p-6">

          <div className="flex items-center gap-4">

            <div className="flex h-12 w-12 items-center justify-center border border-red-500/30 bg-red-500/10">

              <Bot className="h-6 w-6 text-red-400" />

            </div>


            <div>

              <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-red-400">
                KATANA Intelligence
              </p>

              <h3 className="mt-1 font-serif text-xl text-white">
                Neural Assessment
              </h3>

            </div>

          </div>

        </div>


        <div className="relative p-6">

          <div className="border-l border-red-500/50 pl-5">

            <p className="font-mono text-[10px] uppercase tracking-widest text-white/35">
              Current Assessment
            </p>

            <h4 className="mt-4 text-xl font-medium leading-9 text-white">
              {
                aiSummary
              }
            </h4>

          </div>


          <div className="mt-8 border border-white/10 bg-black/30 p-5">

            <div className="mb-4 flex items-center gap-2">

              <BrainCircuit className="h-4 w-4 text-red-400" />

              <span className="font-mono text-[9px] uppercase tracking-widest text-white/40">
                Why KATANA Flagged This
              </span>

            </div>


            <p className="font-mono text-xs leading-7 text-white/60">
              {
                explanation
              }
            </p>

          </div>


          <div className="mt-6">

            <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
              Evidence
            </p>


            <div className="mt-4 space-y-3">

              {
                evidence.length >
                0 ? (
                  evidence.map(
                    (
                      item,
                      index,
                    ) => (
                      <div
                        key={
                          `${item}-${index}`
                        }
                        className="border border-white/10 bg-black/20 px-4 py-4"
                      >

                        <div className="flex gap-3">

                          <span className="font-mono text-[9px] text-red-400">
                            {
                              String(
                                index + 1,
                              ).padStart(
                                2,
                                '0',
                              )
                            }
                          </span>

                          <p className="font-mono text-xs leading-6 text-white/65">
                            {
                              item
                            }
                          </p>

                        </div>

                      </div>
                    ),
                  )
                ) : (
                  <div className="border border-white/10 bg-black/20 px-4 py-8 text-center">

                    <p className="font-mono text-[10px] uppercase tracking-widest text-white/25">
                      No active evidence available
                    </p>

                  </div>
                )
              }

            </div>

          </div>

        </div>

      </div>


      {/* AI CONTEXT */}

      <div className="space-y-5">

        <div className="border border-white/10 bg-black/20 p-5">

          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
            Intelligence Context
          </h3>


          <div className="mt-6 space-y-4">

            <IntelligenceRow
              label="Primary Signal"
              value={
                primarySignal
              }
            />

            <IntelligenceRow
              label="AI Risk"
              value={
                normalizeSeverity(
                  aiRisk,
                )
              }
              danger={
                normalizeSeverity(
                  aiRisk,
                ) !==
                'LOW'
              }
            />

            <IntelligenceRow
              label="Confidence"
              value={
                formatPercent(
                  currentConfidence,
                )
              }
              danger={
                currentConfidence !==
                null
              }
            />

          </div>

        </div>


        <div className="border border-white/10 bg-black/20 p-5">

          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
            MITRE ATT&CK Context
          </h3>


          <div className="mt-5 flex flex-wrap gap-2">

            {
              mitreTechniques.length >
              0 ? (
                mitreTechniques.map(
                  (
                    technique,
                    index,
                  ) => (
                    <span
                      key={
                        `${technique}-${index}`
                      }
                      className="border border-red-500/20 bg-red-500/[0.06] px-3 py-2 font-mono text-[9px] text-red-300"
                    >
                      {
                        technique
                      }
                    </span>
                  ),
                )
              ) : (
                <p className="font-mono text-[10px] text-white/30">
                  No MITRE mapping available for the latest analysis.
                </p>
              )
            }

          </div>

        </div>


        <button
          type="button"
          onClick={() =>
            onNavigate(
              'Investigation',
            )
          }
          className="flex w-full items-center justify-center gap-2 border border-red-500/40 bg-red-500/10 px-4 py-4 font-mono text-[10px] uppercase tracking-[0.2em] text-red-300 transition hover:bg-red-500 hover:text-black"
        >
          Continue Investigation

          <ChevronRight className="h-3.5 w-3.5" />

        </button>

      </div>

    </div>
  )
}


// ===============================================================
// INVESTIGATION PAGE
// ===============================================================

function InvestigationPage({
  latestRecommendations,
  anomalyQueue,
  onNavigate,
}: {
  latestRecommendations: Array<{
    category?: string
    reason?: string
    command?: string
  }>
  anomalyQueue: RecentIncident[]
  onNavigate: (
    page: PageName,
  ) => void
}) {
  return (
    <div className="space-y-5">


      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(330px,0.8fr)]">


        {/* RECOMMENDATIONS */}

        <div className="border border-white/10 bg-black/20">

          <div className="border-b border-white/10 px-5 py-4">

            <div className="flex items-center gap-3">

              <FileSearch className="h-4 w-4 text-red-400" />

              <div>

                <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
                  Investigation Recommendations
                </h3>

                <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
                  Deterministic commands — never executed automatically
                </p>

              </div>

            </div>

          </div>


          {
            latestRecommendations.length >
            0 ? (
              <div className="divide-y divide-white/[0.07]">

                {
                  latestRecommendations.map(
                    (
                      recommendation,
                      index,
                    ) => (
                      <div
                        key={
                          `${recommendation.command}-${index}`
                        }
                        className="p-5"
                      >

                        <div className="flex flex-col gap-4">

                          <div>

                            <span className="font-mono text-[9px] uppercase tracking-widest text-red-400">
                              {
                                recommendation.category ??
                                'Investigation'
                              }
                            </span>

                            <p className="mt-3 font-mono text-xs leading-6 text-white/55">
                              {
                                recommendation.reason ??
                                'No reason provided.'
                              }
                            </p>

                          </div>


                          <div className="border border-white/10 bg-black/40 px-4 py-4 font-mono text-xs text-white/75">

                            <span className="text-white/25">
                              $
                            </span>

                            {' '}

                            {
                              recommendation.command ??
                              '—'
                            }

                          </div>

                        </div>

                      </div>
                    ),
                  )
                }

              </div>
            ) : (
              <div className="px-5 py-16 text-center">

                <FileSearch className="mx-auto h-6 w-6 text-white/20" />

                <p className="mt-4 font-mono text-[10px] uppercase tracking-widest text-white/25">
                  No active investigation recommendations
                </p>

              </div>
            )
          }

        </div>


        {/* INVESTIGATION QUEUE */}

        <div className="border border-white/10 bg-black/20">

          <div className="border-b border-white/10 px-5 py-4">

            <div className="flex items-center gap-3">

              <Radar className="h-4 w-4 text-red-400" />

              <div>

                <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
                  Incident Queue
                </h3>

                <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
                  Recent anomalies requiring analysis
                </p>

              </div>

            </div>

          </div>


          <div className="divide-y divide-white/[0.07]">

            {
              anomalyQueue.length >
              0 ? (
                anomalyQueue.map(
                  (
                    anomaly,
                    index,
                  ) => {
                    const severity =
                      normalizeSeverity(
                        anomaly.severity,
                      )

                    const title =
                      anomaly
                        .evidence
                        ?.[0] ??
                      'Behavioral anomaly detected'

                    return (
                      <div
                        key={
                          `${anomaly.timestamp}-${index}`
                        }
                        className="p-5"
                      >

                        <div className="flex items-start justify-between gap-4">

                          <p className="font-mono text-xs leading-6 text-white/75">
                            {
                              title
                            }
                          </p>

                          <SeverityBadge
                            severity={
                              severity
                            }
                          />

                        </div>


                        <div className="mt-4 space-y-2">

                          <IntelligenceRow
                            label="Score"
                            value={
                              formatScore(
                                anomaly.score,
                              )
                            }
                          />

                          <IntelligenceRow
                            label="Confidence"
                            value={
                              formatPercent(
                                anomaly.confidence,
                              )
                            }
                          />

                        </div>


                        <p className="mt-4 font-mono text-[9px] text-white/25">
                          {
                            formatRelativeTime(
                              anomaly.timestamp,
                            )
                          }
                        </p>

                      </div>
                    )
                  },
                )
              ) : (
                <div className="p-10 text-center">

                  <p className="font-mono text-[10px] uppercase tracking-widest text-white/25">
                    No anomalies in queue
                  </p>

                </div>
              )
            }

          </div>

        </div>

      </div>


      <button
        type="button"
        onClick={() =>
          onNavigate(
            'Threats',
          )
        }
        className="border border-white/10 bg-white/[0.02] px-4 py-3 font-mono text-[9px] uppercase tracking-[0.18em] text-white/50 transition hover:border-white/20 hover:text-white"
      >
        Return to Threats
      </button>

    </div>
  )
}


// ===============================================================
// SETTINGS PAGE
// ===============================================================

function SettingsPage({
  pipelineRunning,
  mlStatus,
  baselineProgress,
  eventHistorySize,
  totalEvents,
  totalIncidents,
}: {
  pipelineRunning: boolean
  mlStatus: string
  baselineProgress: number
  eventHistorySize: number
  totalEvents: number
  totalIncidents: number
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(330px,0.7fr)]">


      <div className="space-y-5">

        <div className="border border-white/10 bg-black/20">

          <div className="border-b border-white/10 px-5 py-4">

            <div className="flex items-center gap-3">

              <Settings className="h-4 w-4 text-red-400" />

              <div>

                <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
                  Runtime State
                </h3>

                <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
                  Current backend and ML runtime visibility
                </p>

              </div>

            </div>

          </div>


          <div className="divide-y divide-white/[0.07]">

            <SettingRow
              label="Pipeline"
              value={
                pipelineRunning
                  ? 'ACTIVE'
                  : 'STOPPED'
              }
              valueClass={
                pipelineRunning
                  ? 'text-emerald-400'
                  : 'text-red-400'
              }
            />

            <SettingRow
              label="ML State"
              value={
                mlStatus.toUpperCase()
              }
            />

            <SettingRow
              label="Baseline"
              value={
                mlStatus ===
                'learning'
                  ? `${baselineProgress.toFixed(
                      1,
                    )}%`
                  : 'READY'
              }
              valueClass="text-emerald-400"
            />

          </div>

        </div>


        <div className="border border-white/10 bg-black/20">

          <div className="border-b border-white/10 px-5 py-4">

            <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
              Frontend Monitoring
            </h3>

          </div>


          <div className="divide-y divide-white/[0.07]">

            <SettingRow
              label="Dashboard Polling"
              value="2 SECONDS"
            />

            <SettingRow
              label="Maximum Event History"
              value={`${MAX_EVENT_HISTORY} SNAPSHOTS`}
            />

            <SettingRow
              label="Graph Window"
              value={`${MAX_GRAPH_POINTS} POINTS`}
            />

            <SettingRow
              label="Current Local History"
              value={`${eventHistorySize} SNAPSHOTS`}
            />

          </div>

        </div>

      </div>


      <div className="border border-white/10 bg-black/20 p-5">

        <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
          Session Statistics
        </h3>


        <div className="mt-6 space-y-4">

          <CompactStat
            label="Backend Events"
            value={
              formatNumber(
                totalEvents,
              )
            }
          />

          <CompactStat
            label="Confirmed Incidents"
            value={
              formatNumber(
                totalIncidents,
              )
            }
          />

          <CompactStat
            label="Local History"
            value={
              formatNumber(
                eventHistorySize,
              )
            }
          />

        </div>


        <div className="mt-8 border-t border-white/10 pt-6">

          <p className="font-mono text-[9px] uppercase tracking-widest text-white/30">
            Safety Model
          </p>

          <p className="mt-3 font-mono text-xs leading-7 text-white/45">
            KATANA can recommend investigation actions, but commands are
            presented for human review and are not executed automatically.
          </p>

        </div>

      </div>

    </div>
  )
}


// ===============================================================
// RECENT EVENTS TABLE
// ===============================================================

function RecentEventsTable({
  events,
  loading,
  limit,
  compact = false,
  onViewAll,
}: {
  events: DashboardEvent[]
  loading: boolean
  limit?: number
  compact?: boolean
  onViewAll?: () => void
}) {
  const displayedEvents =
    limit
      ? events
          .slice(
            -limit,
          )
          .reverse()
      : [
          ...events,
        ].reverse()


  return (
    <div className="border border-white/10 bg-black/20">

      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">

        <div className="flex items-center gap-3">

          <Terminal className="h-4 w-4 text-white/50" />

          <div>

            <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
              Recent Events
            </h3>

            <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
              Frontend dashboard history
            </p>

          </div>

        </div>


        {
          compact &&
          onViewAll && (
            <button
              type="button"
              onClick={
                onViewAll
              }
              className="font-mono text-[9px] uppercase tracking-widest text-red-400 transition hover:text-red-300"
            >
              View All
            </button>
          )
        }

      </div>


      <div className="overflow-x-auto">

        <table className="w-full min-w-[700px] text-left">

          <thead>

            <tr className="border-b border-white/10">

              <TableHead>
                Time
              </TableHead>

              <TableHead>
                Event
              </TableHead>

              <TableHead>
                Process
              </TableHead>

              <TableHead>
                Score
              </TableHead>

              <TableHead>
                Status
              </TableHead>

            </tr>

          </thead>


          <tbody>

            {
              displayedEvents.length >
              0 ? (
                displayedEvents.map(
                  (
                    event,
                  ) => (
                    <tr
                      key={
                        event.id
                      }
                      className="border-b border-white/[0.06] transition hover:bg-white/[0.025]"
                    >

                      <td className="px-5 py-4 font-mono text-[10px] text-white/40">
                        {
                          formatTime(
                            event.timestamp,
                          )
                        }
                      </td>


                      <td className="px-5 py-4 font-mono text-[10px] text-white/75">
                        {
                          event.event_type
                        }
                      </td>


                      <td className="px-5 py-4 font-mono text-[10px] text-white/50">
                        {
                          event.process_name
                        }
                      </td>


                      <td className="px-5 py-4 font-mono text-[10px] text-white/70">
                        {
                          formatScore(
                            event.score ??
                              event.anomaly_score,
                          )
                        }
                      </td>


                      <td className="px-5 py-4">

                        <EventStatus
                          status={
                            event.status
                          }
                        />

                      </td>

                    </tr>
                  ),
                )
              ) : (
                <tr>

                  <td
                    colSpan={
                      5
                    }
                    className="px-5 py-10 text-center font-mono text-[10px] uppercase tracking-widest text-white/25"
                  >
                    {
                      loading
                        ? 'Loading event stream...'
                        : 'Collecting dashboard history...'
                    }
                  </td>

                </tr>
              )
            }

          </tbody>

        </table>

      </div>

    </div>
  )
}


// ===============================================================
// THREAT QUEUE
// ===============================================================

function ThreatQueue({
  anomalyQueue,
  onAnalyze,
  compact = false,
}: {
  anomalyQueue: RecentIncident[]
  onAnalyze: () => void
  compact?: boolean
}) {
  return (
    <div className="border border-white/10 bg-black/20">

      <div className="flex items-center gap-3 border-b border-white/10 px-5 py-4">

        <Radar className="h-4 w-4 text-red-400" />

        <div>

          <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-white/80">
            Anomaly Queue
          </h3>

          <p className="mt-1 font-mono text-[9px] uppercase tracking-wider text-white/30">
            Requires attention
          </p>

        </div>

      </div>


      <div className="divide-y divide-white/[0.07]">

        {
          anomalyQueue.length >
          0 ? (
            anomalyQueue.map(
              (
                anomaly,
                index,
              ) => {
                const severity =
                  normalizeSeverity(
                    anomaly.severity,
                  )

                const title =
                  anomaly
                    .evidence
                    ?.[0] ??
                  'Behavioral anomaly detected'

                return (
                  <div
                    key={
                      `${anomaly.timestamp}-${index}`
                    }
                    className="p-5 transition hover:bg-white/[0.025]"
                  >

                    <div className="flex items-start justify-between gap-4">

                      <div>

                        <p className="font-mono text-xs leading-6 text-white/80">
                          {
                            title
                          }
                        </p>

                        <p className="mt-2 font-mono text-[10px] text-white/35">
                          Score:{' '}
                          {
                            formatScore(
                              anomaly.score,
                            )
                          }
                        </p>

                      </div>


                      <SeverityBadge
                        severity={
                          severity
                        }
                      />

                    </div>


                    <div className="mt-4 flex items-center justify-between">

                      <span className="font-mono text-[9px] text-white/25">
                        {
                          formatRelativeTime(
                            anomaly.timestamp,
                          )
                        }
                      </span>


                      <button
                        type="button"
                        onClick={
                          onAnalyze
                        }
                        className="font-mono text-[9px] uppercase tracking-widest text-red-400 hover:text-red-300"
                      >
                        {
                          compact
                            ? 'View →'
                            : 'Analyze →'
                        }
                      </button>

                    </div>

                  </div>
                )
              },
            )
          ) : (
            <div className="p-10 text-center">

              <p className="font-mono text-[10px] uppercase tracking-widest text-white/25">
                No anomalies in queue
              </p>

            </div>
          )
        }

      </div>

    </div>
  )
}


// ===============================================================
// METRIC CARD
// ===============================================================

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  accent,
}: {
  icon: typeof ShieldCheck
  label: string
  value: string
  detail: string
  accent:
    | 'emerald'
    | 'red'
    | 'white'
}) {
  const accentClass = {
    emerald:
      'text-emerald-400',

    red:
      'text-red-400',

    white:
      'text-white',
  }[
    accent
  ]


  return (
    <div className="group relative overflow-hidden border border-white/10 bg-white/[0.02] p-5 transition hover:border-white/20 hover:bg-white/[0.035]">

      <div className="absolute right-0 top-0 h-16 w-16 bg-gradient-to-bl from-white/[0.04] to-transparent" />


      <div className="relative flex items-start justify-between">

        <div>

          <p className="font-mono text-[9px] uppercase tracking-[0.18em] text-white/35">
            {
              label
            }
          </p>


          <p className={`mt-4 font-mono text-2xl ${accentClass}`}>
            {
              value
            }
          </p>


          <p className="mt-3 font-mono text-[9px] text-white/30">
            {
              detail
            }
          </p>

        </div>


        <div className="border border-white/10 bg-black/20 p-2.5">

          <Icon
            className={`h-4 w-4 ${accentClass}`}
          />

        </div>

      </div>

    </div>
  )
}


// ===============================================================
// COMPACT STAT
// ===============================================================

function CompactStat({
  label,
  value,
  danger = false,
}: {
  label: string
  value: string
  danger?: boolean
}) {
  return (
    <div className="border border-white/10 bg-black/20 p-4">

      <p className="font-mono text-[8px] uppercase tracking-widest text-white/30">
        {
          label
        }
      </p>

      <p
        className={`mt-3 font-mono text-sm ${
          danger
            ? 'text-red-400'
            : 'text-white/80'
        }`}
      >
        {
          value
        }
      </p>

    </div>
  )
}


// ===============================================================
// ACTIVITY STAT
// ===============================================================

function ActivityStat({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="px-5 py-4">

      <p className="font-mono text-[8px] uppercase tracking-widest text-white/30">
        {
          label
        }
      </p>


      <p className="mt-2 font-mono text-sm text-white/80">
        {
          value
        }
      </p>

    </div>
  )
}


// ===============================================================
// INTELLIGENCE ROW
// ===============================================================

function IntelligenceRow({
  label,
  value,
  danger = false,
}: {
  label: string
  value: string
  danger?: boolean
}) {
  return (
    <div className="flex items-center justify-between gap-5 border-b border-white/[0.07] pb-3">

      <span className="font-mono text-[9px] uppercase tracking-widest text-white/30">
        {
          label
        }
      </span>


      <span
        className={`text-right font-mono text-[10px] ${
          danger
            ? 'text-red-400'
            : 'text-white/75'
        }`}
      >
        {
          value
        }
      </span>

    </div>
  )
}


// ===============================================================
// SETTING ROW
// ===============================================================

function SettingRow({
  label,
  value,
  valueClass = 'text-white/75',
}: {
  label: string
  value: string
  valueClass?: string
}) {
  return (
    <div className="flex items-center justify-between gap-5 px-5 py-4">

      <span className="font-mono text-[10px] uppercase tracking-widest text-white/35">
        {
          label
        }
      </span>


      <span
        className={`font-mono text-[10px] ${valueClass}`}
      >
        {
          value
        }
      </span>

    </div>
  )
}


// ===============================================================
// SEVERITY BADGE
// ===============================================================

function SeverityBadge({
  severity,
}: {
  severity: string
}) {
  const styles:
    Record<
      string,
      string
    > = {
      CRITICAL:
        'border-red-500/40 bg-red-500/20 text-red-300',

      HIGH:
        'border-red-500/30 bg-red-500/10 text-red-400',

      MEDIUM:
        'border-amber-500/30 bg-amber-500/10 text-amber-300',

      LOW:
        'border-emerald-500/20 bg-emerald-500/5 text-emerald-400',
    }


  const style =
    styles[
      severity
    ] ??
    styles.LOW


  return (
    <span
      className={`shrink-0 border px-2 py-1 font-mono text-[8px] tracking-widest ${style}`}
    >
      {
        severity
      }
    </span>
  )
}


// ===============================================================
// TABLE HEAD
// ===============================================================

function TableHead({
  children,
}: {
  children: ReactNode
}) {
  return (
    <th className="px-5 py-3 font-mono text-[8px] font-normal uppercase tracking-[0.15em] text-white/25">
      {
        children
      }
    </th>
  )
}


// ===============================================================
// EVENT STATUS
// ===============================================================

function EventStatus({
  status,
}: {
  status: string
}) {
  const normalized =
    status.toUpperCase()


  const styles:
    Record<
      string,
      string
    > = {
      ANOMALY:
        'border-red-500/30 bg-red-500/10 text-red-400',

      CRITICAL:
        'border-red-500/40 bg-red-500/20 text-red-300',

      HIGH:
        'border-red-500/30 bg-red-500/10 text-red-400',

      WATCH:
        'border-amber-500/30 bg-amber-500/10 text-amber-300',

      MEDIUM:
        'border-amber-500/30 bg-amber-500/10 text-amber-300',

      NORMAL:
        'border-emerald-500/20 bg-emerald-500/5 text-emerald-400',

      LOW:
        'border-emerald-500/20 bg-emerald-500/5 text-emerald-400',
    }


  const style =
    styles[
      normalized
    ] ??
    styles.NORMAL


  return (
    <span
      className={`border px-2 py-1 font-mono text-[8px] tracking-widest ${style}`}
    >
      {
        normalized
      }
    </span>
  )
}