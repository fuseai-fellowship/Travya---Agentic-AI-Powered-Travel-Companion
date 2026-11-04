import React from "react";
import { Box, Flex, Text } from "@chakra-ui/react";
import { Sparkles } from "lucide-react";

export const TypingIndicator: React.FC = () => {
  return (
    <Flex justify="flex-start">
      <Box maxW="85%">
        <Flex align="center" gap={2} mb={2}>
          <Flex
            w="24px"
            h="24px"
            bgGradient="linear(to-br, cyan.500, blue.600)"
            borderRadius="md"
            align="center"
            justify="center"
          >
            <Sparkles size={14} color="white" />
          </Flex>
          <Text fontSize="sm" fontWeight="medium" color="gray.700">
            Travya
          </Text>
        </Flex>
        <Box bg="gray.50" borderRadius="2xl" px={4} py={3}>
          <Flex gap={1}>
            <Box
              w="6px"
              h="6px"
              bg="gray.400"
              borderRadius="full"
              animation="bounce 1.4s infinite"
              style={{ animationDelay: "0ms" }}
            />
            <Box
              w="6px"
              h="6px"
              bg="gray.400"
              borderRadius="full"
              animation="bounce 1.4s infinite"
              style={{ animationDelay: "200ms" }}
            />
            <Box
              w="6px"
              h="6px"
              bg="gray.400"
              borderRadius="full"
              animation="bounce 1.4s infinite"
              style={{ animationDelay: "400ms" }}
            />
          </Flex>
        </Box>
      </Box>
    </Flex>
  );
};
