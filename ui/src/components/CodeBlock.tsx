import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

export function CodeBlock({ code, language = '' }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="code-lang mono">{language || 'code'}</span>
        <button className="icon-btn code-copy" onClick={copy} title="Copy">
          {copied ? <Check size={13} color="var(--green)" /> : <Copy size={13} />}
        </button>
      </div>
      <pre className="code-pre mono">{code}</pre>
    </div>
  )
}
