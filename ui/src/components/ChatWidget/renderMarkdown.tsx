// Lightweight markdown -> React node renderer (no external deps)
// Handles: fenced code blocks, bold, italic, inline code, bullet lists, paragraphs.

import { createElement, Fragment } from 'react'
import type { ReactNode } from 'react'
import { CodeBlock } from '../CodeBlock'

function renderInline(text: string): ReactNode[] {
  // Process bold (**text**), italic (*text*), inline code (`code`)
  const parts: ReactNode[] = []
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+)`)/g
  let last = 0
  let match: RegExpExecArray | null
  let key = 0
  while ((match = re.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    if (match[2] != null) parts.push(createElement('strong', { key: key++ }, match[2]))
    else if (match[3] != null) parts.push(createElement('em', { key: key++ }, match[3]))
    else if (match[4] != null) parts.push(createElement('code', { key: key++, className: 'chat-inline-code' }, match[4]))
    last = match.index + match[0].length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

export function renderMarkdown(raw: string): ReactNode {
  const nodes: ReactNode[] = []
  const lines = raw.split('\n')
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]

    // Fenced code block
    const fenceMatch = line.match(/^(`{3,})(\w*)$/)
    if (fenceMatch) {
      const fence = fenceMatch[1]
      const lang = fenceMatch[2] || ''
      const codeLines: string[] = []
      let depth = 1
      i++
      while (i < lines.length && depth > 0) {
        const l = lines[i].trimEnd()
        if (l === fence) {
          depth--
          if (depth === 0) break
          codeLines.push(lines[i])
        } else if (l.match(new RegExp(`^${fence}\\w+$`))) {
          depth++
          codeLines.push(lines[i])
        } else {
          codeLines.push(lines[i])
        }
        i++
      }
      i++ // skip closing fence
      nodes.push(createElement(CodeBlock, { key: key++, code: codeLines.join('\n'), language: lang }))
      continue
    }

    // Bullet list item
    const bulletMatch = line.match(/^[-*]\s+(.*)$/)
    if (bulletMatch) {
      const items: ReactNode[] = []
      while (i < lines.length && lines[i].match(/^[-*]\s+/)) {
        const content = lines[i].replace(/^[-*]\s+/, '')
        items.push(createElement('li', { key: i }, renderInline(content)))
        i++
      }
      nodes.push(createElement('ul', { key: key++, className: 'chat-md-list' }, ...items))
      continue
    }

    // Horizontal rule
    if (line.match(/^---+$/)) {
      nodes.push(createElement('hr', { key: key++, style: { border: 'none', borderTop: '1px solid var(--border)', margin: '8px 0' } }))
      i++
      continue
    }

    // Blockquote
    if (line.startsWith('> ')) {
      const quoteLines: string[] = []
      while (i < lines.length && lines[i].startsWith('> ')) {
        quoteLines.push(lines[i].slice(2))
        i++
      }
      nodes.push(createElement('blockquote', { key: key++, style: { margin: '4px 0', paddingLeft: '8px', borderLeft: '3px solid var(--border)', color: 'var(--text-dim)' } }, ...quoteLines.map((l, j) => createElement('p', { key: j, className: 'chat-md-p' }, renderInline(l)))))
      continue
    }

    // Table
    if (line.includes('|') && line.trim().startsWith('|')) {
      const tableRows: string[][] = []
      while (i < lines.length && lines[i].includes('|') && lines[i].trim().startsWith('|')) {
        const cells = lines[i].split('|').slice(1, -1).map(c => c.trim())
        // Skip separator rows like | :--- | :--- |
        if (!cells.every(c => /^[:\-\s]+$/.test(c))) {
          tableRows.push(cells)
        }
        i++
      }
      if (tableRows.length > 0) {
        const header = tableRows[0]
        const body = tableRows.slice(1)
        nodes.push(createElement('table', { key: key++, style: { fontSize: '12px', borderCollapse: 'collapse', margin: '4px 0', width: '100%' } },
          createElement('thead', null,
            createElement('tr', null, ...header.map((h, j) => createElement('th', { key: j, style: { textAlign: 'left', padding: '3px 6px', borderBottom: '1px solid var(--border)', fontWeight: 600 } }, renderInline(h))))
          ),
          body.length > 0 ? createElement('tbody', null,
            ...body.map((row, ri) => createElement('tr', { key: ri }, ...row.map((c, ci) => createElement('td', { key: ci, style: { padding: '3px 6px', borderBottom: '1px solid rgba(255,255,255,0.06)' } }, renderInline(c)))))
          ) : null
        ))
      }
      continue
    }

    // Blank line
    if (line.trim() === '') {
      i++
      continue
    }

    // Paragraph / heading
    const isH1 = line.startsWith('# ')
    const isH2 = line.startsWith('## ')
    const isH3 = line.startsWith('### ')
    if (isH1) {
      nodes.push(createElement('h3', { key: key++ }, line.slice(2)))
    } else if (isH2) {
      nodes.push(createElement('h4', { key: key++ }, line.slice(3)))
    } else if (isH3) {
      nodes.push(createElement('strong', { key: key++ }, line.slice(4)))
    } else {
      nodes.push(createElement('p', { key: key++, className: 'chat-md-p' }, renderInline(line)))
    }
    i++
  }

  return createElement(Fragment, null, ...nodes)
}
