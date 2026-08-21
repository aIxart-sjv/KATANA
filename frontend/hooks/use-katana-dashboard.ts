'use client'

import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  getDashboard,
  type KatanaDashboard,
} from '@/lib/katana-api'


const REFRESH_INTERVAL = 2000

const MAX_SCORE_HISTORY = 60


export type ScoreHistoryPoint = {
  timestamp: string
  score: number
  threshold: number | null
}


export function useKatanaDashboard() {
  const [data, setData] =
    useState<KatanaDashboard | null>(null)

  const [scoreHistory, setScoreHistory] =
    useState<ScoreHistoryPoint[]>([])

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(null)


  const refresh = useCallback(
    async () => {
      try {
        const dashboard =
          await getDashboard()

        setData(dashboard)

        const score =
          dashboard.ml.latest_anomaly_score

        if (score !== null) {
          setScoreHistory(
            (previous) => [
              ...previous.slice(
                -(MAX_SCORE_HISTORY - 1),
              ),
              {
                timestamp:
                  new Date().toISOString(),

                score,

                threshold:
                  dashboard.ml.threshold,
              },
            ],
          )
        }

        setError(null)
      } catch (error) {
        console.error(
          'Failed to fetch KATANA dashboard:',
          error,
        )

        setError(
          'Unable to connect to KATANA backend',
        )
      } finally {
        setLoading(false)
      }
    },
    [],
  )


  useEffect(
    () => {
      refresh()

      const interval =
        window.setInterval(
          refresh,
          REFRESH_INTERVAL,
        )

      return () => {
        window.clearInterval(
          interval,
        )
      }
    },
    [
      refresh,
    ],
  )


  return {
    data,
    scoreHistory,
    loading,
    error,
    refresh,
  }
}