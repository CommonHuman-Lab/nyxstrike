import React from 'react'
import { createPortal } from 'react-dom'
import { AlertTriangle } from 'lucide-react'
import { ActionButton, type ActionButtonVariant } from './ActionButton'
import './ConfirmActionModal.css'

interface ConfirmActionModalProps {
  isOpen: boolean
  title: string
  description: string
  impactItems?: string[]
  confirmLabel?: string
  cancelLabel?: string
  confirmVariant?: ActionButtonVariant
  isConfirming?: boolean
  onConfirm: () => void | Promise<void>
  onClose: () => void
}

export function ConfirmActionModal({
  isOpen,
  title,
  description,
  impactItems = [],
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  confirmVariant = 'danger',
  isConfirming = false,
  onConfirm,
  onClose,
}: ConfirmActionModalProps) {
  React.useEffect(() => {
    if (!isOpen) return
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !isConfirming) onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [isOpen, isConfirming, onClose])

  if (!isOpen) return null

  return createPortal(
    <div className="modal-backdrop" onClick={e => { if (e.target === e.currentTarget && !isConfirming) onClose() }}>
      <div className="modal confirm-action-modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <div className="modal-title-row">
            <span className="confirm-action-icon" aria-hidden="true">
              <AlertTriangle size={14} />
            </span>
            <span className="modal-name">{title}</span>
          </div>
        </div>

        <div className="modal-body">
          <p className="modal-desc">{description}</p>

          {impactItems.length > 0 && (
            <div className="confirm-action-impact">
              {impactItems.map(item => (
                <div key={item} className="confirm-action-impact-item">{item}</div>
              ))}
            </div>
          )}

          <div className="confirm-action-buttons">
            <ActionButton variant="default" onClick={onClose} disabled={isConfirming}>
              {cancelLabel}
            </ActionButton>
            <ActionButton
              variant={confirmVariant}
              onClick={() => { void onConfirm() }}
              disabled={isConfirming}
            >
              {isConfirming ? 'Clearing…' : confirmLabel}
            </ActionButton>
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}
