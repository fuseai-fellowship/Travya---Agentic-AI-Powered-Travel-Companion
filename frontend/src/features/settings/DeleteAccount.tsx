import { Button, Stack, Text } from "@chakra-ui/react"
import { useMutation } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { accountDeleteMeMutation } from "@/client/@tanstack/react-query.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { signOutUser } from "@/features/auth/actions"
import { notifySuccess } from "@/lib/notify"

export function DeleteAccount() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const remove = useMutation({
    ...accountDeleteMeMutation(),
    meta: { errorTitle: "Couldn't delete your account" },
    onSuccess: async () => {
      await navigate({ to: "/" })
      await signOutUser().catch(() => undefined)
      notifySuccess("Account deleted", "Your trips, notes, conversations and files are gone.")
    },
  })

  return (
    <Stack gap="3" align="flex-start">
      <Text fontSize="sm" color="fg.muted">
        Deletes your account and everything in it: trips, itineraries, bookings, notes,
        conversations and uploaded files.
      </Text>
      <Button colorPalette="red" variant="outline" onClick={() => setOpen(true)}>
        Delete account
      </Button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Delete your account?"
        description="This can't be undone."
        confirmLabel="Delete everything"
        destructive
        typedConfirmation="delete"
        loading={remove.isPending}
        onConfirm={() => remove.mutate({})}
      />
    </Stack>
  )
}
