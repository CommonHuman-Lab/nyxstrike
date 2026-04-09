import { useState } from 'react'
import { CheckCircle, XCircle, Copy, Check } from 'lucide-react'
import { installHint } from '../constants/installHints'
import type { Tool } from '../api'
import { useEscapeClose } from '../hooks/useEscapeClose'

export function ToolModal({ tool, onClose, installed }: {
  tool: Tool
  onClose: () => void
  installed: boolean | undefined
}) {
  const eff = Math.round(tool.effectiveness * 100)
  const effColor = eff >= 90 ? 'var(--green)' : eff >= 75 ? 'var(--amber)' : 'var(--red)'
  const requiredParams = Object.entries(tool.params).filter(([, v]) => v.required)
  const optionalParams = Object.entries(tool.optional)
  const [copied, setCopied] = useState(false)

  function copyInstall() {
    navigator.clipboard.writeText(installHint(tool.name)).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function onBackdrop(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  useEscapeClose(true, onClose)

  return (
    <div className="modal-backdrop" onClick={onBackdrop}>
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-name mono">{tool.name}</span>
            <span className="modal-cat">{tool.category.replace(/_/g, ' ')}</span>
            {installed === true && (
              <span className="modal-status modal-status--installed">
                <CheckCircle size={11} /> installed
              </span>
            )}
            {installed === false && (
              <span className="modal-status modal-status--missing">
                <XCircle size={11} /> not installed
              </span>
            )}
            { tool.parent_tool && (
              <span className="modal-cat" title={`Based on ${tool.parent_tool}`}>
                {tool.parent_tool}
              </span>
            )}
          </div>
          <button className="modal-close" onClick={onClose}><XCircle size={18} /></button>
        </div>

        <div className="modal-body">
          <p className="modal-desc">{tool.desc}</p>

          {/* Effectiveness */}
          <div className="modal-eff-row">
            <span className="modal-label">Effectiveness</span>
            <div className="modal-eff-bar">
              <div className="modal-eff-fill" style={{ width: `${eff}%`, background: effColor }} />
            </div>
            <span className="modal-eff-pct" style={{ color: effColor }}>{eff}%</span>
          </div>

          {/* Install — only shown when tool is not installed (or status unknown) */}
          {installed !== true && (
            <div className="modal-section">
              <span className="modal-label">Install</span>
              <div className="modal-code-wrap">
                <div className="modal-code mono">{installHint(tool.name)}</div>
                <button
                  className="modal-copy-btn"
                  onClick={copyInstall}
                  title="Copy to clipboard"
                >
                  {copied ? <Check size={13} /> : <Copy size={13} />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
          )}

          {/* API Endpoint */}
          <div className="modal-section">
            <span className="modal-label">API Endpoint</span>
            <div className="modal-code mono">{tool.method} {tool.endpoint}</div>
          </div>

          {/* Required params */}
          {requiredParams.length > 0 && (
            <div className="modal-section">
              <span className="modal-label">Required Parameters</span>
              <div className="modal-params">
                {requiredParams.map(([k]) => (
                  <span key={k} className="modal-param modal-param--required mono">{k}</span>
                ))}
              </div>
            </div>
          )}

          {/* Optional params */}
          {optionalParams.length > 0 && (
            <div className="modal-section">
              <span className="modal-label">Optional Parameters</span>
              <table className="modal-table">
                <thead>
                  <tr><th>Parameter</th><th>Default</th></tr>
                </thead>
                <tbody>
                  {optionalParams.map(([k, v]) => (
                    <tr key={k}>
                      <td className="mono">{k}</td>
                      <td className="mono">{String(v) || <em>—</em>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
