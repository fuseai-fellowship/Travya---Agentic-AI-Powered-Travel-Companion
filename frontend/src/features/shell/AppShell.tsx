import { Box, chakra, Flex } from "@chakra-ui/react"
import { Outlet, useNavigate, useRouterState } from "@tanstack/react-router"
import { useEffect } from "react"
import { useAuth } from "@/features/auth/AuthProvider"
import { BottomTabs } from "./BottomTabs"
import { DemoLimitBanner } from "./DemoLimitBanner"
import { MobileTopBar } from "./MobileTopBar"
import { Sidebar } from "./Sidebar"
import { WakeBanner } from "./WakeBanner"

export function AppShell() {
  const { status } = useAuth()
  const navigate = useNavigate()
  const href = useRouterState({ select: (state) => state.location.href })

  // Signing out (or an expired session) while inside the app sends you to the sign-in page.
  useEffect(() => {
    if (status === "signedOut") void navigate({ to: "/login", search: { redirect: href } })
  }, [status, navigate, href])

  return (
    <Flex minH="100dvh" bg="bg">
      <chakra.a
        href="#main"
        position="absolute"
        left="2"
        top="-20"
        zIndex="skipLink"
        bg="bg.panel"
        px="4"
        py="2"
        borderRadius="md"
        _focus={{ top: "2" }}
      >
        Skip to content
      </chakra.a>
      <Sidebar />
      <Flex direction="column" flex="1" minW="0">
        <MobileTopBar />
        <WakeBanner />
        <DemoLimitBanner />
        <Box
          as="main"
          id="main"
          tabIndex={-1}
          flex="1"
          minW="0"
          pb={{ base: "calc(72px + env(safe-area-inset-bottom))", lg: "0" }}
          _focus={{ outline: "none" }}
        >
          <Outlet />
        </Box>
      </Flex>
      <BottomTabs />
    </Flex>
  )
}
