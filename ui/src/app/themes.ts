export type ThemeId =
  | 'dark'
  | 'unicorn'
  | 'forest'
  | 'solarized'
  | 'ocean-glass'
  | 'crimson-night'
  | 'retro-crt'
  | 'nord'
  | 'dracula'
  | 'gruvbox'
  | 'folio'
  | 'tokyo'
  | 'catppuccin'
  | 'synthwave'
  | 'rose'
  | 'frost'

export interface ThemeOption {
  id: ThemeId
  label: string
  hint: string
}

export const THEME_STORAGE_KEY = 'nyxstrike_theme'

export const THEME_OPTIONS: ThemeOption[] = [
  { id: 'dark', label: 'Dark Ops', hint: 'Default tactical dark' },
  { id: 'unicorn', label: 'Unicorn Dream', hint: 'Pastel neon fantasy glow' },
  { id: 'forest', label: 'Forest Canopy', hint: 'Moss, pine, bark, and misty sky' },
  { id: 'solarized', label: 'Solarized Terminal', hint: 'Muted tan and navy readability' },
  { id: 'ocean-glass', label: 'Ocean Glass', hint: 'Deep sea blues with clean contrast' },
  { id: 'crimson-night', label: 'Crimson Night', hint: 'Dark steel with alert red accents' },
  { id: 'retro-crt', label: 'Retro CRT', hint: 'Old-school phosphor monitor vibe' },
  { id: 'nord', label: 'Nord Calm', hint: 'Cool balanced blue-gray palette' },
  { id: 'dracula', label: 'Dracula', hint: 'Slate purple · Lavender · Classic vampire' },
  { id: 'gruvbox', label: 'Gruvbox', hint: 'Warm olive · Burnt orange · Retro terminal' },
  { id: 'folio', label: 'Folio', hint: 'Warm cream · Forest emerald · Paper & ink' },
  { id: 'tokyo', label: 'Tokyo', hint: 'Deep navy · Electric blue · Pro editor' },
  { id: 'catppuccin', label: 'Catppuccin', hint: 'Warm dark · Pastel mauve · Soft & calm' },
  { id: 'synthwave', label: 'Synthwave', hint: 'Outrun purple · Hot magenta · Neon cyan' },
  { id: 'rose', label: 'Rosé', hint: 'Muted charcoal · Dusty rose · Elegant calm' },
  { id: 'frost', label: 'Frost', hint: 'Icy white · Glacier blue · Crisp & clinical' },
]

export function isThemeId(value: string): value is ThemeId {
  return THEME_OPTIONS.some(theme => theme.id === value)
}
