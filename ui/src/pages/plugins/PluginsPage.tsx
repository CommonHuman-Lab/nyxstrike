import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, Puzzle, RefreshCw, RotateCcw, XCircle } from 'lucide-react'
import { api } from '../../api'
import type { ManifestPlugin } from '../../api'
import { StatCard } from '../../components/StatCard'
import './PluginsPage.css'

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<ManifestPlugin[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [search, setSearch] = useState('')

  /** Names that have been toggled but server not yet restarted. */
  const [pendingChanges, setPendingChanges] = useState<Set<string>>(new Set())
  /** Whether a restart is in progress. */
  const [restarting, setRestarting] = useState(false)
  const [restartMsg, setRestartMsg] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.pluginsManifest()
      setPlugins(res.plugins ?? [])
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleToggle = async (plugin: ManifestPlugin) => {
    const newEnabled = !plugin.enabled
    // Optimistic update
    setPlugins(prev =>
      prev.map(p => p.name === plugin.name ? { ...p, enabled: newEnabled } : p)
    )
    try {
      await api.pluginToggle(plugin.name, newEnabled)
      setPendingChanges(prev => new Set(prev).add(plugin.name))
    } catch (e) {
      // Revert on failure
      setPlugins(prev =>
        prev.map(p => p.name === plugin.name ? { ...p, enabled: plugin.enabled } : p)
      )
      setError(`Failed to update '${plugin.name}': ${e}`)
    }
  }

  const handleRestart = async () => {
    setRestarting(true)
    setRestartMsg('Restarting server…')
    try {
      await api.serverRestart()
      setRestartMsg('Server restarting — reconnecting in 5 s…')
      setPendingChanges(new Set())
      // Poll until the server is back up, then reload
      let attempts = 0
      const poll = setInterval(async () => {
        attempts++
        try {
          await api.pluginsManifest()
          clearInterval(poll)
          setRestarting(false)
          setRestartMsg(null)
          load()
        } catch {
          if (attempts >= 30) {
            clearInterval(poll)
            setRestarting(false)
            setRestartMsg('Server did not come back in time — please refresh manually.')
          }
        }
      }, 1000)
    } catch (e) {
      setRestarting(false)
      setRestartMsg(`Restart request failed: ${e}`)
    }
  }

  const byCategory: Record<string, ManifestPlugin[]> = {}
  for (const p of plugins) {
    const cat = p.category || p.type || 'other'
    ;(byCategory[cat] ??= []).push(p)
  }

  const allCategories = ['all', ...Object.keys(byCategory).sort()]

  const inCategory = activeCategory === 'all'
    ? plugins
    : (byCategory[activeCategory] ?? [])

  const filtered = search.trim()
    ? inCategory.filter(p =>
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.description.toLowerCase().includes(search.toLowerCase())
      )
    : inCategory

  const enabledCount = plugins.filter(p => p.enabled).length

  return (
    <div className="page-content plugins-page">
      <div className="kpi-row">
        <StatCard
          icon={<Puzzle size={20} />}
          label="Total Plugins"
          value={plugins.length}
          sub="in manifest"
          accent="var(--purple)"
        />
        <StatCard
          icon={<Puzzle size={20} />}
          label="Enabled"
          value={enabledCount}
          sub={`${plugins.length - enabledCount} disabled`}
          accent="var(--green)"
        />
        <StatCard
          icon={<Puzzle size={20} />}
          label="Categories"
          value={Object.keys(byCategory).length}
          sub="plugin categories"
          accent="var(--blue)"
        />
      </div>

      {/* Pending restart banner */}
      {(pendingChanges.size > 0 || restarting || restartMsg) && (
        <div className="plugins-restart-banner">
          <AlertTriangle size={14} />
          {restartMsg
            ? restartMsg
            : `${pendingChanges.size} pending change${pendingChanges.size !== 1 ? 's' : ''} — restart the server to apply.`
          }
          {!restarting && (
            <button onClick={handleRestart} disabled={restarting}>
              <RotateCcw size={12} style={{ marginRight: 4 }} />
              Restart now
            </button>
          )}
          {restarting && <RefreshCw size={12} className="spin" />}
        </div>
      )}

      <section className="section">
        <div className="section-header">
          <h3>
            <Puzzle size={14} />
            Plugin Registry
            <span className="badge">{filtered.length} / {plugins.length}</span>
          </h3>
        </div>

        {loading && (
          <div className="loading-state">
            <RefreshCw size={20} className="spin" color="var(--green)" />
          </div>
        )}
        {error && (
          <div className="error-banner">Failed to load plugins: {error}</div>
        )}

        {!loading && !error && (
          <>
            <div className="registry-controls">
              <div className="registry-controls-top">
                <div className="search-input-wrap">
                  <input
                    className="search-input mono"
                    placeholder="Search plugins…"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                  />
                  {search.trim().length > 0 && (
                    <button
                      className="search-clear-btn"
                      onClick={() => setSearch('')}
                      title="Clear search"
                      aria-label="Clear search"
                    >
                      <XCircle size={12} />
                    </button>
                  )}
                </div>
              </div>
              <div className="cat-tabs">
                {allCategories.map(cat => (
                  <button
                    key={cat}
                    className={`cat-tab${activeCategory === cat ? ' active' : ''}`}
                    onClick={() => setActiveCategory(activeCategory === cat && cat !== 'all' ? 'all' : cat)}
                  >
                    {cat === 'all' ? 'all' : cat.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="registry-grid registry-grid--wide">
              {filtered.map(plugin => (
                <div
                  key={plugin.name}
                  className={`registry-card${plugin.enabled ? '' : ' plugins-page__card--disabled'}`}
                >
                  <div className="registry-card-top">
                    <span className="registry-name mono">{plugin.name}</span>
                    <label className="plugin-toggle" title={plugin.enabled ? 'Disable plugin' : 'Enable plugin'}>
                      <input
                        type="checkbox"
                        checked={plugin.enabled}
                        onChange={() => handleToggle(plugin)}
                      />
                      <span className="plugin-toggle-track">
                        <span className="plugin-toggle-thumb" />
                      </span>
                      <span className="plugin-toggle-label">
                        {plugin.loaded
                          ? (plugin.enabled ? 'loaded' : 'disabled')
                          : (plugin.enabled ? 'will load' : 'disabled')
                        }
                      </span>
                    </label>
                  </div>
                  <p className="registry-desc">{plugin.description || '—'}</p>
                  <div className="registry-footer">
                    <span className="registry-cat">{(plugin.category || plugin.type || 'plugin').replace(/_/g, ' ')}</span>
                    <span className="registry-eff" title="Effectiveness">
                      {'█'.repeat(Math.round(plugin.effectiveness * 5))}{'░'.repeat(5 - Math.round(plugin.effectiveness * 5))}
                    </span>
                  </div>
                  {plugin.endpoint && (
                    <div className="registry-endpoint mono plugins-page__endpoint">
                      {plugin.endpoint}
                    </div>
                  )}
                </div>
              ))}
              {filtered.length === 0 && (
                <p className="empty-state">No plugins match your filter.</p>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  )
}
