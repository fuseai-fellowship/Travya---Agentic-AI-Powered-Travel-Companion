import { Button, CloseButton, Dialog, Field, Input, Portal, Text } from "@chakra-ui/react"
import { type ReactNode, useId, useState } from "react"

export interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: ReactNode
  confirmLabel: string
  onConfirm: () => void
  loading?: boolean
  destructive?: boolean
  /** When set, the user must type this text before confirming. */
  typedConfirmation?: string
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  onConfirm,
  loading,
  destructive,
  typedConfirmation,
}: ConfirmDialogProps) {
  const [typed, setTyped] = useState("")
  const inputId = useId()
  const blocked = typedConfirmation !== undefined && typed.trim() !== typedConfirmation

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(details) => {
        if (!details.open) setTyped("")
        onOpenChange(details.open)
      }}
      role={destructive ? "alertdialog" : "dialog"}
      placement="center"
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content mx="4">
            <Dialog.Header>
              <Dialog.Title fontFamily="heading">{title}</Dialog.Title>
            </Dialog.Header>
            <Dialog.Body display="flex" flexDirection="column" gap="4">
              {typeof description === "string" ? <Text>{description}</Text> : description}
              {typedConfirmation !== undefined && (
                <Field.Root>
                  <Field.Label htmlFor={inputId}>
                    Type <strong>{typedConfirmation}</strong> to confirm
                  </Field.Label>
                  <Input
                    id={inputId}
                    value={typed}
                    onChange={(event) => setTyped(event.target.value)}
                    autoComplete="off"
                  />
                </Field.Root>
              )}
            </Dialog.Body>
            <Dialog.Footer>
              <Dialog.ActionTrigger asChild>
                <Button variant="outline">Keep it</Button>
              </Dialog.ActionTrigger>
              <Button
                colorPalette={destructive ? "red" : "brand"}
                loading={loading}
                disabled={blocked}
                onClick={onConfirm}
              >
                {confirmLabel}
              </Button>
            </Dialog.Footer>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" aria-label="Close" />
            </Dialog.CloseTrigger>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  )
}
