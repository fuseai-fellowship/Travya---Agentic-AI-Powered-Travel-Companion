import { Flex, Icon, Text, VStack } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { NAV_ITEMS } from "./nav"

/** Mobile and tablet navigation, fixed above the home indicator. */
export function BottomTabs() {
  return (
    <Flex
      as="nav"
      aria-label="Main"
      display={{ base: "flex", lg: "none" }}
      position="fixed"
      bottom="0"
      insetX="0"
      zIndex="docked"
      bg="bg.panel"
      borderTopWidth="1px"
      pb="env(safe-area-inset-bottom)"
    >
      {NAV_ITEMS.map((item) => (
        <Link key={item.to} to={item.to} style={{ flex: 1 }}>
          {({ isActive }) => (
            <VStack
              gap="0.5"
              minH="60px"
              justify="center"
              color={isActive ? "brand.fg" : "fg.muted"}
              fontWeight={isActive ? "600" : "500"}
            >
              <Icon as={item.icon} boxSize="5" />
              <Text fontSize="xs">{item.label}</Text>
            </VStack>
          )}
        </Link>
      ))}
    </Flex>
  )
}
