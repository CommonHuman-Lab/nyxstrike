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
    const fenceMatch = line.match(/^```(\w*)$/)
    if (fenceMatch) {
      const lang = fenceMatch[1] || ''
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++ // skip closing ```
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
