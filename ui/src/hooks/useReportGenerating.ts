import { useEffect, useState } from 'react'
import {
  type ReportGenState,
  getReportGenState,
  subscribeReportGen,
  isReportGenerating,
} from '../app/reportGeneration'

/** Returns the full report generation state from the module-level store. */
export function useReportGenState(): ReportGenState {
  const [state, setState] = useState<ReportGenState>(getReportGenState)

  useEffect(() => {
    setState(getReportGenState())
    return subscribeReportGen(setState)
  }, [])

  return state
}

/** Convenience: returns true while generating (back-compat for the button badge). */
export function useReportGenerating(): boolean {
  const [generating, setGenerating] = useState(isReportGenerating)

  useEffect(() => {
    setGenerating(isReportGenerating())
    return subscribeReportGen(s => setGenerating(s.status === 'generating'))
  }, [])

  return generating
}
