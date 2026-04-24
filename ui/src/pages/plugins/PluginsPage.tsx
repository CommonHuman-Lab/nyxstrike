import { useEffect, useState } from 'react'
import { Puzzle, RefreshCw, XCircle } from 'lucide-react'
import { api, type Plugin } from '../../api'
import { StatCard } from '../../components/StatCard'
import './PluginsPage.css'

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([])
  const [byCategory, setByCategory] = useState<Record<string, Plugin[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [listRes, catRes] = await Promise.all([
          api.pluginList(),
          api.pluginsByCategory(),
        ])
        setPlugins(listRes.plugins ?? [])
        setByCategory(catRes.categories ?? {})
      } catch (e) {
        setError(String(e))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

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
          sub="registered"
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
                    <span className={`registry-cat plugins-page__status${plugin.enabled ? ' plugins-page__status--enabled' : ''}`}>
                      {plugin.enabled ? 'enabled' : 'disabled'}
                    </span>
                  </div>
                  <p className="registry-desc">{plugin.description}</p>
                  <div className="registry-footer">
                    <span className="registry-cat">{plugin.category.replace(/_/g, ' ')}</span>
                    <span className="registry-eff" title="Effectiveness">
                      {'█'.repeat(Math.round(plugin.effectiveness * 5))}{'░'.repeat(5 - Math.round(plugin.effectiveness * 5))}
                    </span>
                  </div>
                  <div className="registry-endpoint mono plugins-page__endpoint">
                    {plugin.endpoint}
                  </div>
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
