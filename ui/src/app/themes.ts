export type ThemeId =
  | 'dark'
  | 'candy'
  | 'unicorn'
  | 'forest'
  | 'solarized-terminal'
  | 'ocean-glass'
  | 'crimson-night'
  | 'retro-crt'
  | 'nord-calm'
  | 'desert-sand'
  | 'minimal-light'

export interface ThemeOption {
  id: ThemeId
  label: string
  hint: string
}

export const THEME_STORAGE_KEY = 'nyxstrike_theme'

export const THEME_OPTIONS: ThemeOption[] = [
  { id: 'dark', label: 'Dark Ops', hint: 'Default tactical dark' },
  { id: 'candy', label: 'Candy Pop', hint: 'Playful colorful palette' },
  { id: 'unicorn', label: 'Unicorn Dream', hint: 'Pastel neon fantasy glow' },
  { id: 'forest', label: 'Forest Canopy', hint: 'Moss, pine, bark, and misty sky' },
  { id: 'solarized-terminal', label: 'Solarized Terminal', hint: 'Muted tan and navy readability' },
  { id: 'ocean-glass', label: 'Ocean Glass', hint: 'Deep sea blues with clean contrast' },
  { id: 'crimson-night', label: 'Crimson Night', hint: 'Dark steel with alert red accents' },
  { id: 'retro-crt', label: 'Retro CRT', hint: 'Old-school phosphor monitor vibe' },
  { id: 'nord-calm', label: 'Nord Calm', hint: 'Cool balanced blue-gray palette' },
  { id: 'desert-sand', label: 'Desert Sand', hint: 'Warm light neutral workspace' },
  { id: 'minimal-light', label: 'White Minimalist', hint: 'Clean and bright' },
]

export function isThemeId(value: string): value is ThemeId {
  return THEME_OPTIONS.some(theme => theme.id === value)
}
