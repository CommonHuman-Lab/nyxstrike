import type { SessionSummary, SessionEvent } from '../../api'

const EVENT_ICONS: Record<string, string> = {
  session_created: '🟢',
  status_changed: '🔄',
  handover: '🤖',
  finding_added: '🔍',
  report_generated: '📄',
  ai_report_generated: '🧠',
  note_added: '📝',
  tool_run: '⚙️',
}

function fmtTs(ts: number): string {
  if (!ts) return '—'
  try {
    return new Date(ts * 1000).toLocaleString()
  } catch {
    return String(ts)
  }
}

function EventRow({ evt }: { evt: SessionEvent }) {
  const icon = EVENT_ICONS[evt.type] ?? '•'
  const label = evt.type.replace(/_/g, ' ')
  return (
    <div className="timeline-event">
      <span className="timeline-event-icon">{icon}</span>
      <div className="timeline-event-body">
        <div className="timeline-event-header">
          <span className="timeline-event-type">{label}</span>
          <span className="timeline-event-ts section-meta">{fmtTs(evt.timestamp)}</span>
        </div>
        {evt.message && <p className="timeline-event-message">{evt.message}</p>}
      </div>
    </div>
  )
}

export function SessionTimeline({ session }: { session: SessionSummary }) {
  const eventLog: SessionEvent[] = session.event_log ?? []
  const handovers = session.handover_history ?? []

  // Merge event_log + handovers into a unified, sorted timeline
  const events: Array<{ ts: number; el: React.ReactNode }> = []

  for (const evt of eventLog) {
    events.push({
      ts: evt.timestamp ?? 0,
      el: <EventRow key={`evt-${evt.timestamp}-${evt.type}`} evt={evt} />,
    })
  }

  for (const h of handovers) {
    const ts = h.timestamp ? new Date(h.timestamp).getTime() / 1000 : 0
    events.push({
      ts,
      el: (
        <div key={`handover-${h.timestamp}`} className="timeline-event">
          <span className="timeline-event-icon">🤖</span>
          <div className="timeline-event-body">
            <div className="timeline-event-header">
              <span className="timeline-event-type">handover — {h.category}</span>
              <span className="timeline-event-ts section-meta">
                {h.timestamp ? new Date(h.timestamp).toLocaleString() : '—'}
              </span>
            </div>
            <p className="timeline-event-message">
              Confidence: {Math.round((h.confidence ?? 0) * 100)}%
              {h.note ? ` — ${h.note}` : ''}
            </p>
          </div>
        </div>
      ),
    })
  }

  events.sort((a, b) => b.ts - a.ts)

  if (events.length === 0) {
    return (
      <div className="session-timeline">
        <p className="section-meta">No timeline events recorded yet.</p>
      </div>
    )
  }

  return (
    <div className="session-timeline">
      <div className="timeline-list">
        {events.map((e, i) => (
          <div key={i}>{e.el}</div>
        ))}
      </div>
    </div>
  )
}
