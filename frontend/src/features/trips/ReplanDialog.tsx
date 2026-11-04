import { Button, CloseButton, Dialog, Field, Portal, Text, Textarea } from "@chakra-ui/react"
import { useState } from "react"
import { LuSparkles } from "react-icons/lu"

export function ReplanDialog({
  disabled,
  hasPlan,
  onReplan,
}: {
  disabled: boolean
  hasPlan: boolean
  onReplan: (instructions: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [instructions, setInstructions] = useState("")

  return (
    <Dialog.Root open={open} onOpenChange={(details) => setOpen(details.open)} placement="center">
      <Dialog.Trigger asChild>
        <Button
          size="sm"
          colorPalette="brand"
          variant={hasPlan ? "outline" : "solid"}
          disabled={disabled}
        >
          <LuSparkles /> {hasPlan ? "Re-plan" : "Plan with agents"}
        </Button>
      </Dialog.Trigger>
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content mx="4">
            <Dialog.Header>
              <Dialog.Title fontFamily="heading">
                {hasPlan ? "Re-plan this trip" : "Plan this trip"}
              </Dialog.Title>
            </Dialog.Header>
            <Dialog.Body display="flex" flexDirection="column" gap="3">
              {hasPlan && (
                <Text fontSize="sm" color="fg.muted">
                  The agents replace their own itinerary items and quotes. Items you added and
                  confirmed bookings stay.
                </Text>
              )}
              <Field.Root>
                <Field.Label>Instructions (optional)</Field.Label>
                <Textarea
                  rows={3}
                  maxLength={1000}
                  value={instructions}
                  onChange={(event) => setInstructions(event.target.value)}
                  placeholder="e.g. More food markets, slower mornings, skip museums"
                />
                <Field.HelperText>{instructions.length}/1000</Field.HelperText>
              </Field.Root>
            </Dialog.Body>
            <Dialog.Footer>
              <Dialog.ActionTrigger asChild>
                <Button variant="outline">Cancel</Button>
              </Dialog.ActionTrigger>
              <Button
                colorPalette="brand"
                onClick={() => {
                  onReplan(instructions)
                  setOpen(false)
                  setInstructions("")
                }}
              >
                Start planning
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
