import type { ToolExecResponse } from '../api'

export interface HistoryPoint {
  t: number
  cpu: number
  mem: number
  network_bytes_sent: number
  network_bytes_recv: number
}

export interface RunHistoryEntry {
  id: number
  tool: string
  params: Record<string, unknown>
  result: ToolExecResponse
  ts: Date
  source?: 'browser' | 'server'
  serverId?: number
}
