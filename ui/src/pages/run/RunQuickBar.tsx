import { Sparkles, Target, X } from 'lucide-react'

interface RunQuickBarProps {
  favorites: string[]
  onPickFavorite: (toolName: string) => void
  recentTargets: string[]
  onPickTarget: (target: string) => void
  onClearRecentTargets: () => void
}

export function RunQuickBar({
  favorites,
  onPickFavorite,
  recentTargets,
  onPickTarget,
  onClearRecentTargets,
}: RunQuickBarProps) {
  return (
    <div className="run-quickbar">
      <div className="run-quickbar-block">
        <div className="run-quickbar-title">
          <Sparkles size={12} /> Favorites
        </div>
        <div className="run-quickbar-items">
          {favorites.map(name => (
            <button key={name} className="run-quick-chip" onClick={() => onPickFavorite(name)}>
              {name}
            </button>
          ))}
          {favorites.length === 0 && <span className="run-quick-empty">No favorites yet</span>}
        </div>
      </div>

      <div className="run-quickbar-block">
        <div className="run-quickbar-title">
          <Target size={12} /> Recent Targets
          {recentTargets.length > 0 && (
            <button className="run-quick-clear" onClick={onClearRecentTargets} title="Clear recent targets">
              <X size={11} />
            </button>
          )}
        </div>
        <div className="run-quickbar-items">
          {recentTargets.map(target => (
            <button key={target} className="run-quick-chip" onClick={() => onPickTarget(target)}>
              {target}
            </button>
          ))}
          {recentTargets.length === 0 && <span className="run-quick-empty">No recent targets</span>}
        </div>
      </div>
    </div>
  )
}
