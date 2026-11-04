import { Box, Flex, HStack, Icon, Stack, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { Logo } from "@/components/Logo"
import { ColorModeButton } from "@/components/ui/color-mode"
import { NAV_ITEMS } from "./nav"
import { UserMenu } from "./UserMenu"

/** Desktop navigation (lg and up). */
export function Sidebar() {
  return (
    <Flex
      as="nav"
      aria-label="Main"
      direction="column"
      display={{ base: "none", lg: "flex" }}
      w="240px"
      flexShrink={0}
      borderRightWidth="1px"
      bg="bg.subtle"
      position="sticky"
      top="0"
      h="100dvh"
      px="3"
      py="5"
    >
      <Box px="3" pb="6">
        <Link to="/trips" aria-label="Travya, your trips">
          <Logo />
        </Link>
      </Box>
      <Stack as="ul" gap="1" listStyleType="none" flex="1">
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <Link to={item.to}>
              {({ isActive }) => (
                <HStack
                  gap="3"
                  px="3"
                  minH="44px"
                  borderRadius="md"
                  fontWeight={isActive ? "600" : "500"}
                  bg={isActive ? "bg.panel" : "transparent"}
                  color={isActive ? "fg" : "fg.muted"}
                  boxShadow={isActive ? "card" : "none"}
                  _hover={{ bg: "bg.panel", color: "fg" }}
                >
                  <Icon as={item.icon} boxSize="5" color={isActive ? "brand.fg" : "inherit"} />
                  <Text>{item.label}</Text>
                </HStack>
              )}
            </Link>
          </li>
        ))}
      </Stack>
      <HStack justify="space-between" px="1">
        <UserMenu />
        <ColorModeButton size="sm" />
      </HStack>
    </Flex>
  )
}
