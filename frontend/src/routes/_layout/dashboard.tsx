import { Box, Container, Text } from "@chakra-ui/react";
import { createFileRoute } from "@tanstack/react-router";

import useAuth from "@/hooks/useAuth";
import TravyaChatInterfaces from "../../components/Chat/mainChat";

export const Route = createFileRoute("/_layout/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  const { user: currentUser } = useAuth();

  return (
    <>
      <Box h="full" overflow="hidden">
        <TravyaChatInterfaces />
      </Box>
    </>
  );
}
