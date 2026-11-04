import { Button, Field, HStack, Input, Stack } from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { accountPatchMeMutation, accountReadMeQueryKey } from "@/client/@tanstack/react-query.gen"
import type { MeRead } from "@/client/types.gen"
import { notifySuccess } from "@/lib/notify"

const schema = z.object({
  display_name: z.string().trim().max(120, "Use at most 120 characters"),
  home_city: z.string().trim().max(120, "Use at most 120 characters"),
  currency: z
    .string()
    .trim()
    .transform((value) => value.toUpperCase())
    .pipe(z.string().regex(/^[A-Z]{3}$/, "Use a 3-letter code like USD")),
})
type FormInput = z.input<typeof schema>
type FormOutput = z.output<typeof schema>

export function ProfileForm({ me }: { me: MeRead }) {
  const queryClient = useQueryClient()
  const save = useMutation({
    ...accountPatchMeMutation(),
    meta: { errorTitle: "Couldn't save your profile" },
    onSuccess: (data) => {
      queryClient.setQueryData(accountReadMeQueryKey(), data)
      notifySuccess("Profile saved")
    },
  })
  const { register, handleSubmit, formState } = useForm<FormInput, unknown, FormOutput>({
    resolver: zodResolver(schema),
    values: {
      display_name: me.display_name ?? "",
      home_city: me.home_city ?? "",
      currency: me.currency,
    },
  })
  const { errors } = formState

  return (
    <Stack asChild gap="4">
      <form
        noValidate
        onSubmit={handleSubmit((values) =>
          save.mutate({
            body: {
              display_name: values.display_name || null,
              home_city: values.home_city || null,
              currency: values.currency,
            },
          }),
        )}
      >
        <Field.Root invalid={!!errors.display_name}>
          <Field.Label>Display name</Field.Label>
          <Input autoComplete="name" {...register("display_name")} />
          <Field.ErrorText>{errors.display_name?.message}</Field.ErrorText>
        </Field.Root>
        <HStack gap="4" align="start" flexWrap={{ base: "wrap", sm: "nowrap" }}>
          <Field.Root invalid={!!errors.home_city}>
            <Field.Label>Home city</Field.Label>
            <Input autoComplete="address-level2" {...register("home_city")} />
            <Field.ErrorText>{errors.home_city?.message}</Field.ErrorText>
          </Field.Root>
          <Field.Root invalid={!!errors.currency} maxW={{ sm: "140px" }}>
            <Field.Label>Currency</Field.Label>
            <Input maxLength={3} textTransform="uppercase" {...register("currency")} />
            <Field.ErrorText>{errors.currency?.message}</Field.ErrorText>
          </Field.Root>
        </HStack>
        <Button
          type="submit"
          colorPalette="brand"
          alignSelf="flex-start"
          loading={save.isPending}
          disabled={!formState.isDirty}
        >
          Save profile
        </Button>
      </form>
    </Stack>
  )
}
