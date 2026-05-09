import { CheckCircle, XCircle } from 'lucide-react'
import type { ManifestPlugin } from '../api'
import { useEscapeClose } from '../hooks/useEscapeClose'

export function PluginModal({ plugin, onClose }: {
  plugin: ManifestPlugin
  onClose: () => void
}) {
  const eff = Math.round(plugin.effectiveness * 100)
  const effColor = eff >= 90 ? 'var(--green)' : eff >= 75 ? 'var(--amber)' : 'var(--red)'
  const category = (plugin.category || plugin.type || 'plugin').replace(/_/g, ' ')
  const tags: string[] = Array.isArray(plugin.tags) ? plugin.tags : []

  function onBackdrop(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  useEscapeClose(true, onClose)

  return (
    <div className="modal-backdrop" onClick={onBackdrop}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name mono">{plugin.name}</span>
            <span className="modal-cat">{category}</span>
            {plugin.loaded
              ? (
                <span className="modal-status modal-status--installed">
                  <CheckCircle size={11} /> loaded
                </span>
              ) : (
                <span className="modal-status modal-status--missing">
                  <XCircle size={11} /> not loaded
                </span>
              )
            }
          </div>
          <button className="modal-close" onClick={onClose}><XCircle size={18} /></button>
        </div>

        <div className="modal-body">
          <p className="modal-desc">{plugin.description || '—'}</p>

          {/* Effectiveness */}
          <div className="modal-eff-row">
            <span className="modal-label">Effectiveness</span>
            <div className="modal-eff-bar">
              <div className="modal-eff-fill" style={{ width: `${eff}%`, background: effColor }} />
            </div>
            <span className="modal-eff-pct" style={{ color: effColor }}>{eff}%</span>
          </div>

          {/* Version & Author */}
          <div className="modal-section">
            <div className="modal-meta-grid">
              {plugin.version && (
                <div className="modal-meta-item">
                  <span className="modal-label">Version</span>
                  <span className="mono">{plugin.version}</span>
                </div>
              )}
              {plugin.author && (
                <div className="modal-meta-item">
                  <span className="modal-label">Author</span>
                  <span className="mono">{plugin.author}</span>
                </div>
              )}
              {plugin.plugin_type && (
                <div className="modal-meta-item">
                  <span className="modal-label">Plugin Type</span>
                  <span className="mono">{plugin.plugin_type}</span>
                </div>
              )}
              <div className="modal-meta-item">
                <span className="modal-label">Status</span>
                <span className="mono">{plugin.enabled ? 'enabled' : 'disabled'}</span>
              </div>
            </div>
          </div>

          {/* Endpoint */}
          {plugin.endpoint && (
            <div className="modal-section">
              <span className="modal-label">API Endpoint</span>
              <div className="modal-code mono">{plugin.endpoint}</div>
            </div>
          )}

          {/* MCP Tool Name */}
          {plugin.mcp_tool_name && (
            <div className="modal-section">
              <span className="modal-label">MCP Tool Name</span>
              <div className="modal-code mono">{plugin.mcp_tool_name}</div>
            </div>
          )}

          {/* Tags */}
          {tags.length > 0 && (
            <div className="modal-section">
              <span className="modal-label">Tags</span>
              <div className="modal-params">
                {tags.map(tag => (
                  <span key={tag} className="modal-param mono">{tag}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
