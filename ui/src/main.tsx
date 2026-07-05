import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './animations.css'
import './themes/candy.css'
import './themes/unicorn.css'
import './themes/forest.css'
import './themes/solarized-terminal.css'
import './themes/ocean-glass.css'
import './themes/crimson-night.css'
import './themes/retro-crt.css'
import './themes/nord-calm.css'
import './themes/desert-sand.css'
import './themes/minimal-light.css'
import './themes/dracula.css'
import './themes/gruvbox.css'
import './themes/folio.css'
import './themes/tokyo.css'
import './themes/catppuccin.css'
import './themes/synthwave.css'
import './themes/rose.css'
import './themes/frost.css'
import './themes/effects.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
