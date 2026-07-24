import { useEffect, useState } from 'react'
import type { Tool } from '../api'
import type { Page } from './routing'

const PALETTE_HINT_SEEN_KEY = 'nyxstrike_palette_hint_seen'

export interface CommandToolRequest {
  toolName: string
  requestId: number
}

export function useCommandPalette(setPage: (page: Page) => void) {
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [commandToolRequest, setCommandToolRequest] = useState<CommandToolRequest | null>(null)
  const [showPaletteHint, setShowPaletteHint] = useState(() => {
    try {
      return localStorage.getItem(PALETTE_HINT_SEEN_KEY) !== '1'
    } catch {
      return true
    }
  })

  useEffect(() => {
    function onGlobalKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setPaletteOpen(true)
      }
    }
    window.addEventListener('keydown', onGlobalKeyDown)
    return () => window.removeEventListener('keydown', onGlobalKeyDown)
  }, [])

  function handleCommandSelectTool(tool: Tool) {
    setPage('run')
    setCommandToolRequest({ toolName: tool.name, requestId: Date.now() })
  }

  function dismissPaletteHint() {
    setShowPaletteHint(false)
    try {
      localStorage.setItem(PALETTE_HINT_SEEN_KEY, '1')
    } catch {
      // ignore storage failures
    }
  }

  function openCommandPalette() {
    setPaletteOpen(true)
    if (showPaletteHint) dismissPaletteHint()
  }

  function clearCommandToolRequest() {
    setCommandToolRequest(null)
  }

  return {
    paletteOpen,
    setPaletteOpen,
    commandToolRequest,
    clearCommandToolRequest,
    showPaletteHint,
    dismissPaletteHint,
    openCommandPalette,
    handleCommandSelectTool,
  }
}
