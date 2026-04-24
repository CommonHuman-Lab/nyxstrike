import type { ButtonHTMLAttributes, ReactNode } from 'react'
import './ActionButton.css'

type ActionButtonVariant = 'default' | 'success' | 'warning' | 'danger' | 'running'

interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ActionButtonVariant
  children: ReactNode
}

export function ActionButton({
  variant = 'default',
  className = '',
  children,
  ...rest
}: ActionButtonProps) {
  return (
    <button
      className={`action-button action-button--${variant}${className ? ` ${className}` : ''}`}
      {...rest}
    >
      {children}
    </button>
  )
}

export type { ActionButtonVariant }
