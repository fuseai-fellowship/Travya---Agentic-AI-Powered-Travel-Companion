import { Avatar, Button, Menu, Portal, Text } from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { LuLogOut, LuSettings } from "react-icons/lu"
import { useAuth } from "@/features/auth/AuthProvider"
import { signOutUser } from "@/features/auth/actions"

export function displayName(
  user: { isAnonymous: boolean; displayName: string | null; email: string | null } | null,
) {
  if (!user) return "Guest"
  if (user.isAnonymous) return "Demo traveller"
  return user.displayName || user.email || "Traveller"
}

export function UserMenu({ compact = false }: { compact?: boolean }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const name = displayName(user)

  // Leave the signed-in area first, so the shell doesn't treat this as an expired session.
  const signOut = async () => {
    await navigate({ to: "/" })
    await signOutUser()
  }

  return (
    <Menu.Root positioning={{ placement: compact ? "bottom-end" : "top-start" }}>
      <Menu.Trigger asChild>
        <Button variant="ghost" size="sm" minH="44px" px="2">
          <Avatar.Root size="xs" colorPalette="brand" aria-hidden="true">
            <Avatar.Fallback name={user?.isAnonymous ? "Demo" : name} />
          </Avatar.Root>
          <Text as="span" srOnly>
            Account menu for{" "}
          </Text>
          <Text as="span" maxW="120px" truncate fontSize="sm" srOnly={compact}>
            {name}
          </Text>
        </Button>
      </Menu.Trigger>
      <Portal>
        <Menu.Positioner>
          <Menu.Content minW="200px">
            <Menu.ItemGroup>
              <Menu.ItemGroupLabel>
                {name}
                {user?.isAnonymous && (
                  <Text fontSize="xs" color="fg.muted" fontWeight="normal">
                    Save your trips from Settings
                  </Text>
                )}
              </Menu.ItemGroupLabel>
            </Menu.ItemGroup>
            <Menu.Separator />
            <Menu.Item value="settings" onSelect={() => void navigate({ to: "/settings" })}>
              <LuSettings /> Settings
            </Menu.Item>
            <Menu.Item value="sign-out" onSelect={() => void signOut()}>
              <LuLogOut /> Sign out
            </Menu.Item>
          </Menu.Content>
        </Menu.Positioner>
      </Portal>
    </Menu.Root>
  )
}
