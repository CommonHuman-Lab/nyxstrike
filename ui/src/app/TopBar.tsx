import { useEffect, useRef, useState } from 'react'
import faviconUrl from '../favicon-16x16.png'
import {
  RefreshCw, Lock, Github, Copy, Check,
  LayoutDashboard, Terminal, Play,
  Settings as SettingsIcon, HelpCircle,
  ListTodo, Wrench, FileText, Layers, Palette, PanelBottomOpen, X, Puzzle,
} from 'lucide-react'
import { clearToken, hasToken, type WebDashboardResponse } from '../api'
import type { Page } from './routing'
import { THEME_OPTIONS, type ThemeId } from './themes'
import { InformationModal } from '../components/InformationModal'

interface TopBarProps {
  page: Page
  setPage: (page: Page) => void
  lastRefresh: Date | null
  demo: boolean
  isStreaming: boolean
  streamingError: string | null
  health: WebDashboardResponse | null
  error: string | null
  loading: boolean
  fetchAll: () => Promise<void>
  themeId: ThemeId
  setThemeId: (theme: ThemeId) => void
  reduceTextureEffects: boolean
  setReduceTextureEffects: (value: boolean) => void
  onOpenCommandPalette: () => void
  onSignOut: () => void
}

const MOBILE_PAGE_OPTIONS: Array<{ value: Exclude<Page, 'session-detail'>; label: string }> = [
  { value: 'dashboard', label: 'Home' },
  { value: 'run', label: 'Run' },
  { value: 'logs', label: 'Logs' },
  { value: 'settings', label: 'Settings' },
  { value: 'help', label: 'Help' },
  { value: 'tasks', label: 'Tasks' },
  { value: 'tools', label: 'Tools' },
  { value: 'plugins', label: 'Plugins' },
  { value: 'reports', label: 'Reports' },
  { value: 'sessions', label: 'Sessions' },
]

function DiscordIcon({ size = 14 }: { size?: number }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 245 240" width={size} height={size}>
      <g>
        <path d="M216.856339,16.5966031 C200.285002,8.84328665 182.566144,3.2084988 164.041564,0 C161.766523,4.11318106 159.108624,9.64549908 157.276099,14.0464379 C137.583995,11.0849896 118.072967,11.0849896 98.7430163,14.0464379 C96.9108417,9.64549908 94.1925838,4.11318106 91.8971895,0 C73.3526068,3.2084988 55.6133949,8.86399117 39.0420583,16.6376612 C5.61752293,67.146514 -3.4433191,116.400813 1.08711069,164.955721 C23.2560196,181.510915 44.7403634,191.567697 65.8621325,198.148576 C71.0772151,190.971126 75.7283628,183.341335 79.7352139,175.300261 C72.104019,172.400575 64.7949724,168.822202 57.8887866,164.667963 C59.7209612,163.310589 61.5131304,161.891452 63.2445898,160.431257 C105.36741,180.133187 151.134928,180.133187 192.754523,160.431257 C194.506336,161.891452 196.298154,163.310589 198.110326,164.667963 C191.183787,168.842556 183.854737,172.420929 176.223542,175.320965 C180.230393,183.341335 184.861538,190.991831 190.096624,198.16893 C211.238746,191.588051 232.743023,181.531619 254.911949,164.955721 C260.227747,108.668201 245.831087,59.8662432 216.856339,16.5966031 Z M85.4738752,135.09489 C72.8290281,135.09489 62.4592217,123.290155 62.4592217,108.914901 C62.4592217,94.5396472 72.607595,82.7145587 85.4738752,82.7145587 C98.3405064,82.7145587 108.709962,94.5189427 108.488529,108.914901 C108.508531,123.290155 98.3405064,135.09489 85.4738752,135.09489 Z M170.525237,135.09489 C157.88039,135.09489 147.510584,123.290155 147.510584,108.914901 C147.510584,94.5396472 157.658606,82.7145587 170.525237,82.7145587 C183.391518,82.7145587 193.761324,94.5189427 193.539891,108.914901 C193.539891,123.290155 183.391518,135.09489 170.525237,135.09489 Z" fill="#5865F2" fillRule="nonzero" />
      </g>
    </svg>
  )
}

export function TopBar({
  page,
  setPage,
  lastRefresh,
  demo,
  isStreaming,
  streamingError,
  health,
  error,
  loading,
  fetchAll,
  themeId,
  setThemeId,
  reduceTextureEffects,
  setReduceTextureEffects,
  onOpenCommandPalette,
  onSignOut,
}: TopBarProps) {
  const REFRESH_BUTTON_DELAY_MS = 3500
  const [themeModalOpen, setThemeModalOpen] = useState(false)
  const [themePreviewId, setThemePreviewId] = useState<ThemeId>(themeId)
  const [themeSelectionId, setThemeSelectionId] = useState<ThemeId>(themeId)
  const [updateModalOpen, setUpdateModalOpen] = useState(false)
  const [updateCmdCopied, setUpdateCmdCopied] = useState(false)
  const [quickActionsOpen, setQuickActionsOpen] = useState(false)
  const [showRefreshButton, setShowRefreshButton] = useState(false)
  const [statusPulse, setStatusPulse] = useState(false)
  const quickActionsRef = useRef<HTMLDivElement | null>(null)
  const firstRefreshIsoRef = useRef<string | null>(null)
  const statusPulseIsoRef = useRef<string | null>(null)
  const [showRefreshInTooltip, setShowRefreshInTooltip] = useState(demo)

  function copyUpdateCommand() {
    navigator.clipboard.writeText('git pull').then(() => {
      setUpdateCmdCopied(true)
      window.setTimeout(() => setUpdateCmdCopied(false), 2000)
    }).catch(() => {})
  }

  useEffect(() => {
    if (!themeModalOpen) {
      setThemePreviewId(themeId)
      setThemeSelectionId(themeId)
      return
    }
    document.documentElement.setAttribute('data-theme', themePreviewId)
  }, [themeModalOpen, themePreviewId, themeId])

  useEffect(() => {
    if (demo) {
      setShowRefreshInTooltip(true)
      return
    }
    if (!lastRefresh) return
    const iso = lastRefresh.toISOString()
    if (!firstRefreshIsoRef.current) {
      firstRefreshIsoRef.current = iso
      return
    }
    if (firstRefreshIsoRef.current !== iso) {
      setShowRefreshInTooltip(true)
      firstRefreshIsoRef.current = iso
    }
  }, [demo, lastRefresh])

  useEffect(() => {
    if (!lastRefresh || health?.status !== 'healthy') return
    const iso = lastRefresh.toISOString()
    if (!statusPulseIsoRef.current) {
      statusPulseIsoRef.current = iso
      return
    }
    if (statusPulseIsoRef.current === iso) return

    statusPulseIsoRef.current = iso
    setStatusPulse(true)
    const timerId = window.setTimeout(() => setStatusPulse(false), 700)
    return () => window.clearTimeout(timerId)
  }, [lastRefresh, health?.status])

  useEffect(() => {
    function onPointerDown(e: MouseEvent) {
      if (!quickActionsRef.current) return
      if (!quickActionsRef.current.contains(e.target as Node)) setQuickActionsOpen(false)
    }

    function onEscClose(e: KeyboardEvent) {
      if (e.key === 'Escape') setQuickActionsOpen(false)
    }

    if (quickActionsOpen) {
      window.addEventListener('mousedown', onPointerDown)
      window.addEventListener('keydown', onEscClose)
    }

    return () => {
      window.removeEventListener('mousedown', onPointerDown)
      window.removeEventListener('keydown', onEscClose)
    }
  }, [quickActionsOpen])

  useEffect(() => {
    if (demo || isStreaming) {
      setShowRefreshButton(false)
      return
    }

    const timerId = window.setTimeout(() => {
      setShowRefreshButton(true)
    }, REFRESH_BUTTON_DELAY_MS)

    return () => {
      window.clearTimeout(timerId)
    }
  }, [demo, isStreaming])

  function openThemeModal() {
    setQuickActionsOpen(false)
    setThemePreviewId(themeId)
    setThemeSelectionId(themeId)
    setThemeModalOpen(true)
  }

  function closeThemeModal() {
    document.documentElement.setAttribute('data-theme', themeId)
    setThemePreviewId(themeId)
    setThemeSelectionId(themeId)
    setThemeModalOpen(false)
  }

  function applyThemeSelection() {
    setThemeId(themeSelectionId)
    setThemeModalOpen(false)
  }

  const healthLabel = health?.status
    ? health.status.charAt(0).toUpperCase() + health.status.slice(1)
    : (loading ? 'Connecting…' : error ?? 'Unknown')
  const streamLabel = isStreaming ? 'Live' : streamingError ? 'Polling' : 'N/A'
  const refreshPart = showRefreshInTooltip && lastRefresh
    ? ` | Last refresh: ${lastRefresh.toLocaleTimeString('en-GB')}`
    : ''
  const statusTooltip = demo
    ? `System: ${healthLabel}${refreshPart}`
    : `System: ${healthLabel} | Updates: ${streamLabel}${refreshPart}${streamingError ? ` (${streamingError})` : ''}`

  const mobilePage = page === 'session-detail' ? 'sessions' : page

  return (
    <>
      <InformationModal
        isOpen={updateModalOpen}
        title="Update Available"
        description={health?.update?.latest_version
          ? `A newer release (${health.update.latest_version}) is available.`
          : 'A newer release is available.'}
        primaryLabel="Open GitHub"
        secondaryLabel="Close"
        onPrimary={() => {
          window.open('https://github.com/CommonHuman-Lab/nyxstrike', '_blank', 'noopener,noreferrer')
        }}
        onSecondary={() => setUpdateModalOpen(false)}
        onClose={() => setUpdateModalOpen(false)}
      >
        <div className="modal-section">
          <span className="modal-label">Update command</span>
          <div className="modal-code-wrap">
            <div className="modal-code mono">git pull</div>
            <button
              className="modal-copy-btn"
              onClick={copyUpdateCommand}
              title="Copy update command"
            >
              {updateCmdCopied ? <Check size={13} /> : <Copy size={13} />}
              {updateCmdCopied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
        <p className="modal-desc">Run <span className="mono">git pull</span> in your project folder, then restart NyxStrike.</p>
      </InformationModal>

      <InformationModal
        isOpen={themeModalOpen}
        title="Choose Theme"
        description="Preview themes live, then apply your selection."
        className="theme-picker-modal"
        primaryLabel="Apply Theme"
        primaryVariant="success"
        secondaryLabel="Cancel"
        onPrimary={applyThemeSelection}
        onSecondary={closeThemeModal}
        onClose={closeThemeModal}
      >
        <label className="theme-picker-toggle-row">
          <input
            type="checkbox"
            checked={reduceTextureEffects}
            onChange={e => setReduceTextureEffects(e.target.checked)}
          />
          <span className="theme-picker-toggle-text">Reduce background texture effects</span>
        </label>
        <div className="theme-picker-grid">
          {THEME_OPTIONS.map(option => (
            <button
              key={option.id}
              className={`theme-picker-card${themeSelectionId === option.id ? ' active' : ''}`}
              onClick={() => {
                setThemeSelectionId(option.id)
                setThemePreviewId(option.id)
              }}
              type="button"
            >
              <span className="theme-picker-card-label">{option.label}</span>
              <span className="theme-picker-card-hint">{option.hint}</span>
            </button>
          ))}
        </div>
      </InformationModal>

      <header className="topbar">
        <div className="topbar-brand">
          <img src={faviconUrl} width={18} height={18} alt="" />
          <span
            className="brand-text"
            title={`Version: ${health?.version ?? 'unknown'}`}
            aria-label={`NyxStrike version ${health?.version ?? 'unknown'}`}
          >
            NyxStrike
          </span>
          {health?.update?.update_available && (
            <button
              type="button"
              className="brand-update-chip mono"
              onClick={() => setUpdateModalOpen(true)}
              title={`New version available: ${health.update.latest_version}`}
            >
              Update available
            </button>
          )}
        </div>

      <nav className="topbar-nav">
        <button className={`nav-tab ${page === 'dashboard' ? 'active' : ''}`} onClick={() => setPage('dashboard')}>
          <LayoutDashboard size={13} /> Home
        </button>
        <button className={`nav-tab ${page === 'run' ? 'active' : ''}`} onClick={() => setPage('run')}>
          <Play size={13} /> Run
        </button>
        <button className={`nav-tab ${page === 'logs' ? 'active' : ''}`} onClick={() => setPage('logs')}>
          <Terminal size={13} /> Logs
        </button>
        <button className={`nav-tab ${page === 'settings' ? 'active' : ''}`} onClick={() => setPage('settings')}>
          <SettingsIcon size={13} /> Settings
        </button>
        <button className={`nav-tab ${page === 'help' ? 'active' : ''}`} onClick={() => setPage('help')}>
          <HelpCircle size={13} /> Help
        </button>
        <button className={`nav-tab ${page === 'tasks' ? 'active' : ''}`} onClick={() => setPage('tasks')}>
          <ListTodo size={13} /> Tasks
        </button>
        <button className={`nav-tab ${page === 'tools' ? 'active' : ''}`} onClick={() => setPage('tools')}>
          <Wrench size={13} /> Tools
        </button>
        <button className={`nav-tab ${page === 'plugins' ? 'active' : ''}`} onClick={() => setPage('plugins')}>
          <Puzzle size={13} /> Plugins
        </button>
        <button className={`nav-tab ${page === 'reports' ? 'active' : ''}`} onClick={() => setPage('reports')}>
          <FileText size={13} /> Reports
        </button>
        <button className={`nav-tab ${page === 'sessions' || page === 'session-detail' ? 'active' : ''}`} onClick={() => setPage('sessions')}>
          <Layers size={13} /> Sessions
        </button>
      </nav>

        <div className="topbar-right">
          <label className="topbar-mobile-nav" aria-label="Navigate page">
            <span className="topbar-mobile-nav-label">Page</span>
          <select
            className="topbar-mobile-nav-select"
            value={mobilePage}
            onChange={e => setPage(e.target.value as Exclude<Page, 'session-detail'>)}
          >
            {MOBILE_PAGE_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>
        <div
          className={`status-dot ${health?.status === 'healthy' ? 'online' : error ? 'error' : 'loading'}${statusPulse ? ' status-dot--pulse' : ''}`}
          title={statusTooltip}
          aria-label={statusTooltip}
        />
        {showRefreshButton && (
          <button className="icon-btn" onClick={fetchAll} title="Refresh now">
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
          </button>
        )}
        <a
          className="icon-btn topbar-link-btn topbar-action-desktop"
          href="https://github.com/CommonHuman-Lab/nyxstrike"
          target="_blank"
          rel="noreferrer"
          title="View on GitHub"
        >
          <Github size={14} />
        </a>
        <a
          className="icon-btn topbar-link-btn topbar-action-desktop"
          href="https://discord.gg/aC8Q2xJFgp"
          target="_blank"
          rel="noreferrer"
          title="Join Discord community"
        >
          <DiscordIcon />
        </a>
        <button
          className="icon-btn topbar-action-desktop"
          title="Command palette (Ctrl/Cmd+K)"
          onClick={onOpenCommandPalette}
        >
          <span className="palette-icon-k mono">K</span>
        </button>
        <button
          className="icon-btn topbar-action-desktop"
          title="Change theme"
          onClick={openThemeModal}
        >
          <Palette size={14} />
        </button>
        {hasToken() && (
          <button className="icon-btn" onClick={() => { clearToken(); onSignOut() }} title="Sign out">
            <Lock size={14} />
          </button>
        )}
      </div>
    </header>

      <div
        ref={quickActionsRef}
        className={`quick-actions-fab${quickActionsOpen ? ' open' : ''}`}
      >
        <div className="quick-actions-panel" aria-hidden={!quickActionsOpen}>
          <button
            className="quick-actions-item"
            onClick={() => {
              onOpenCommandPalette()
              setQuickActionsOpen(false)
            }}
            title="Open command palette"
          >
            <span className="quick-actions-item-icon mono">K</span>
            <span>Command Palette</span>
          </button>
          <button
            className="quick-actions-item"
            onClick={() => {
              openThemeModal()
            }}
            title="Choose theme"
          >
            <Palette size={14} />
            <span>Theme Picker</span>
          </button>
          <button
            className="quick-actions-item"
            onClick={() => {
              window.open('https://github.com/CommonHuman-Lab/nyxstrike', '_blank', 'noopener,noreferrer')
              setQuickActionsOpen(false)
            }}
            title="Open GitHub"
          >
            <Github size={14} />
            <span>GitHub</span>
          </button>
          <button
            className="quick-actions-item"
            onClick={() => {
              window.open('https://discord.gg/aC8Q2xJFgp', '_blank', 'noopener,noreferrer')
              setQuickActionsOpen(false)
            }}
            title="Join Discord community"
          >
            <DiscordIcon size={14} />
            <span>Discord</span>
          </button>
        </div>

        <button
          className="quick-actions-trigger"
          onClick={() => setQuickActionsOpen(v => !v)}
          aria-expanded={quickActionsOpen}
          aria-label={quickActionsOpen ? 'Close quick actions' : 'Open quick actions'}
          title={quickActionsOpen ? 'Close quick actions' : 'Open quick actions'}
        >
          {quickActionsOpen ? <X size={16} /> : <PanelBottomOpen size={16} />}
        </button>
      </div>
    </>
  )
}
