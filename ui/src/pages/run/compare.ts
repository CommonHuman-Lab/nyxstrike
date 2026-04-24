import type { RunHistoryEntry } from '../../shared/types'
import { safeFixed } from '../../shared/utils'

export function buildRunDiff(current: RunHistoryEntry, previous: RunHistoryEntry): string {
  const lines: string[] = []
  lines.push(`Comparing ${current.tool}`)
  lines.push('')
  lines.push(`Current:  exit=${current.result.return_code}, success=${current.result.success}, time=${safeFixed(current.result.execution_time, 2)}s`)
  lines.push(`Previous: exit=${previous.result.return_code}, success=${previous.result.success}, time=${safeFixed(previous.result.execution_time, 2)}s`)
  lines.push('')

  const currentOutput = (current.result.stdout || current.result.stderr || '').trim()
  const previousOutput = (previous.result.stdout || previous.result.stderr || '').trim()

  if (!currentOutput && !previousOutput) {
    lines.push('No output in either run.')
    return lines.join('\n')
  }

  if (currentOutput === previousOutput) {
    lines.push('Output is identical.')
    return lines.join('\n')
  }

  const currentLines = currentOutput.split('\n')
  const previousSet = new Set(previousOutput.split('\n'))
  const added = currentLines.filter(line => !previousSet.has(line)).slice(0, 40)

  const previousLines = previousOutput.split('\n')
  const currentSet = new Set(currentLines)
  const removed = previousLines.filter(line => !currentSet.has(line)).slice(0, 40)

  if (added.length > 0) {
    lines.push('Added lines:')
    for (const line of added) lines.push(`+ ${line}`)
    lines.push('')
  }

  if (removed.length > 0) {
    lines.push('Removed lines:')
    for (const line of removed) lines.push(`- ${line}`)
  }

  return lines.join('\n')
}
