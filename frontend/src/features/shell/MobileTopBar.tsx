import { Flex, HStack } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { Logo } from "@/components/Logo"
import { ColorModeButton } from "@/components/ui/color-mode"
import { UserMenu } from "./UserMenu"

export function MobileTopBar() {
  return (
    <Flex
      as="header"
      display={{ base: "flex", lg: "none" }}
      align="center"
      justify="space-between"
      px="4"
      h="56px"
      borderBottomWidth="1px"
      bg="bg"
      position="sticky"
      top="0"
      zIndex="sticky"
    >
      <Link to="/trips">
        <Logo size={24} />
      </Link>
      <HStack gap="1">
        <ColorModeButton size="sm" />
        <UserMenu compact />
      </HStack>
    </Flex>
  )
}
