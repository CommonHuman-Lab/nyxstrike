import { useEffect, useState } from 'react'
import { THEME_STORAGE_KEY, isThemeId, type ThemeId } from './themes'

export function useThemePreferences() {
  const [themeId, setThemeId] = useState<ThemeId>(() => {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY)
      if (stored && isThemeId(stored)) return stored
    } catch { /* ignored */ }
    return 'dark'
  })
  const [reduceTextureEffects, setReduceTextureEffects] = useState<boolean>(() => {
    try {
      return localStorage.getItem('nyxstrike_reduce_texture_effects') === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', themeId)
    if (reduceTextureEffects) {
      document.documentElement.setAttribute('data-reduce-textures', '1')
    } else {
      document.documentElement.removeAttribute('data-reduce-textures')
    }
    try {
      localStorage.setItem(THEME_STORAGE_KEY, themeId)
      localStorage.setItem('nyxstrike_reduce_texture_effects', reduceTextureEffects ? '1' : '0')
    } catch { /* ignored */ }
  }, [themeId, reduceTextureEffects])

  return { themeId, setThemeId, reduceTextureEffects, setReduceTextureEffects }
}
