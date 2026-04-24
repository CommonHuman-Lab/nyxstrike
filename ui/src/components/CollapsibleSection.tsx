import { useState, type ReactNode } from 'react'
import { CollapseChevron } from './CollapseChevron'

interface CollapsibleSectionProps {
  /** Section heading text */
  title: ReactNode
  /** Optional badge/meta rendered after the title */
  badge?: ReactNode
  /** Extra controls rendered on the right side of the header */
  headerRight?: ReactNode
  /** Whether the section starts open (default: false). Used only in uncontrolled mode. */
  defaultOpen?: boolean
  /** Controlled open state. When provided, component is controlled. */
  open?: boolean
  /** Called when the header is clicked in controlled mode. */
  onToggle?: (open: boolean) => void
  /** Content to show when open */
  children: ReactNode
  /** Additional class names for the outer <section> */
  className?: string
  /** Chevron icon size (default: 13) */
  chevronSize?: number
}

/**
 * Generic collapsible section with a `.section` / `.section-header` shell.
 * Supports both uncontrolled (defaultOpen) and controlled (open + onToggle) modes.
 */
export function CollapsibleSection({
  title,
  badge,
  headerRight,
  defaultOpen = false,
  open: openProp,
  onToggle,
  children,
  className,
  chevronSize = 13,
}: CollapsibleSectionProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen)
  const isControlled = openProp !== undefined
  const open = isControlled ? openProp : internalOpen

  const handleToggle = () => {
    if (isControlled) {
      onToggle?.(!open)
    } else {
      setInternalOpen(o => !o)
    }
  }

  return (
    <section className={`section${className ? ` ${className}` : ''}`}>
      <div
        className="section-header section-header--clickable"
        onClick={handleToggle}
      >
        <h3>
          <CollapseChevron open={open} size={chevronSize} className="section-chevron" />
          {title}
          {badge && <> {badge}</>}
        </h3>
        {headerRight && (
          <div onClick={e => e.stopPropagation()}>
            {headerRight}
          </div>
        )}
      </div>
      {open && children}
    </section>
  )
}
