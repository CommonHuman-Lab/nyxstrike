import { type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Info } from 'lucide-react'
import { ActionButton, type ActionButtonVariant } from './ActionButton'
import { useEscapeClose } from '../hooks/useEscapeClose'
import './InformationModal.css'

interface InformationModalProps {
  isOpen: boolean
  title: string
  description?: string
  children?: ReactNode
  primaryLabel?: string
  secondaryLabel?: string
  primaryVariant?: ActionButtonVariant
  isPrimaryBusy?: boolean
  disableClose?: boolean
  className?: string
  onPrimary?: () => void | Promise<void>
  onSecondary?: () => void
  onClose: () => void
}

export function InformationModal({
  isOpen,
  title,
  description,
  children,
  primaryLabel = 'Continue',
  secondaryLabel = 'Cancel',
  primaryVariant = 'default',
  isPrimaryBusy = false,
  disableClose = false,
  className = '',
  onPrimary,
  onSecondary,
  onClose,
}: InformationModalProps) {
  const isClosable = !disableClose && !isPrimaryBusy

  useEscapeClose(isOpen && isClosable, onClose)

  if (!isOpen) return null

  return createPortal(
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget && isClosable) onClose() }}>
      <div className={`modal information-modal${className ? ` ${className}` : ''}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="modal-icon modal-icon--accent" aria-hidden="true">
              <Info size={14} />
            </span>
            <span className="modal-name">{title}</span>
          </div>
          <button className="modal-close" onClick={onClose} disabled={!isClosable}>x</button>
        </div>

        <div className="modal-body">
          {description && <p className="modal-desc">{description}</p>}
          {children}

          {(onPrimary || onSecondary) && (
            <div className="information-modal-buttons">
              {onSecondary && (
                <ActionButton variant="default" onClick={onSecondary} disabled={isPrimaryBusy}>
                  {secondaryLabel}
                </ActionButton>
              )}
              {onPrimary && (
                <ActionButton variant={primaryVariant} onClick={() => { void onPrimary() }} disabled={isPrimaryBusy}>
                  {isPrimaryBusy ? 'Working…' : primaryLabel}
                </ActionButton>
              )}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}
