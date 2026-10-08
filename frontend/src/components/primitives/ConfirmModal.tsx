import { Button } from './Button'
import { Modal } from './Modal'

export type ConfirmModalProps = {
  open: boolean
  title: string
  body: string
  confirmLabel?: string
  cancelLabel?: string
  /** destructive styling for the confirm button */
  danger?: boolean
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/** In-app consent dialog. Prefer this over window.confirm. */
export function ConfirmModal({
  open,
  title,
  body,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  danger = false,
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={() => {
        if (!busy) onCancel()
      }}
      footer={
        <>
          <Button type="button" variant="secondary" disabled={busy} onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={danger ? 'danger' : 'primary'}
            loading={busy}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="m-0 leading-6 text-[var(--text)]">{body}</p>
    </Modal>
  )
}
