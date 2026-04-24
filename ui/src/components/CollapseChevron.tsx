import React from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface CollapseChevronProps {
  open: boolean
  size?: number
  className?: string
  style?: React.CSSProperties
}

/**
 * Simple chevron that rotates between right (closed) and down (open).
 * Use this wherever a collapsible section toggle icon is needed.
 */
export function CollapseChevron({ open, size = 13, className, style }: CollapseChevronProps) {
  return open
    ? <ChevronDown size={size} className={className} style={style} />
    : <ChevronRight size={size} className={className} style={style} />
}
