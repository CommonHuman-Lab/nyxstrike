import { useState } from 'react'
import { Lock, Eye, EyeOff } from 'lucide-react'
import { api, setToken, clearToken } from '../api'
import './TokenGate.css'

export function TokenGate({ onUnlocked }: { onUnlocked: () => void }) {
  const [val, setVal] = useState('')
  const [show, setShow] = useState(false)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function tryToken() {
    setLoading(true)
    setErr('')
    setToken(val.trim())
    try {
      await api.dashboard()
      onUnlocked()
    } catch (e: unknown) {
      clearToken()
      setErr(e instanceof Error && e.message === 'UNAUTHORIZED'
        ? 'Invalid token'
        : 'Could not reach server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="token-gate">
      <div className="token-card">
        <Lock size={32} color="var(--green)" />
        <h2>Authentication Required</h2>
        <p>Enter your <code>NYXSTRIKE_API_TOKEN</code> to continue</p>
        <div className="token-input-row">
          <input
            type={show ? 'text' : 'password'}
            placeholder="Bearer token…"
            value={val}
            onChange={e => setVal(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && tryToken()}
            className="mono"
            autoFocus
          />
          <button className="icon-btn" onClick={() => setShow(s => !s)} title="Toggle visibility">
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>
        {err && <p className="token-err">{err}</p>}
        <button className="btn-primary" onClick={tryToken} disabled={loading || !val.trim()}>
          {loading ? 'Checking…' : 'Connect'}
        </button>
      </div>
    </div>
  )
}
