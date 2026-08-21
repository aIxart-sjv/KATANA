export type KatanaDashboard = {
  system: {
    pipeline_running: boolean
    started_at: string | null
  }

  ml: {
    status: 'learning' | 'monitoring' | string
    baseline_samples: number
    baseline_required: number
    latest_anomaly_score: number | null
    threshold: number | null
  }

  events: {
    total: number
    last_event_at: string | null
  }

  incidents: {
    total: number
    current_severity: string | null
    current_confidence: number | null

    recent: Array<{
      timestamp: string
      severity: string | null
      confidence: number | null
      score: number | null
      evidence: string[]
      recommended_actions: string[]
      ai_analysis: AiAnalysis | null
    }>
  }

  analysis: {
    latest_ai_analysis: AiAnalysis | null

    latest_recommendations: Array<{
      category: string
      reason: string
      command: string
    }>
  }
}

export type AiAnalysis = {
  risk?: string
  summary?: string
  analysis?: string
  mitre_attack?: string[]
  [key: string]: unknown
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_KATANA_API_URL ||
  'http://localhost:8000'

export async function getDashboard(): Promise<KatanaDashboard> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/dashboard`,
      {
        method: 'GET',
        cache: 'no-store',
        headers: {
          Accept: 'application/json',
        },
      },
    )

    if (!response.ok) {
      throw new Error(
        `KATANA API returned ${response.status} ${response.statusText}`,
      )
    }

    return await response.json()
  } catch (error) {
    console.error(
      'Failed to fetch KATANA dashboard:',
      error,
    )

    throw error
  }
}